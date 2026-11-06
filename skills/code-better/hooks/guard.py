#!/usr/bin/env python3
"""code-better harness guard: turns the skill's stage gates into enforced checks.

One script for every hook event (PreToolUse on Edit/Write/MultiEdit/NotebookEdit/Bash,
and Stop). Two sensors, no trust in claims:
  - the session transcript: which stage lines the agent actually printed;
  - git: a fingerprint of the working tree at every hook call, so a file changed by
    Bash (sed -i, heredoc, script) counts exactly like one changed by Edit.
It is armed only after the code-better skill loads in this session; every other
session passes straight through.

Each control names the incident it exists for. Remove a control when its incident
stops happening (the decision log shows how often each one fires).

  G1 change-before-gate  Live runs: agent changed files (via Edit, and via a Bash
                         heredoc) before printing `gate:`, then printed it at the end.
  G2 full-without-plan   Full/project rung changes before `plan: pass` and the
                         `teardown/readiness: pass` round: building an unreviewed plan.
  G3 commit-unverified   `git commit` with files changed after the last `verify: pass`.
  G4 stop-unverified     Ending the turn with files changed after the last `verify:` line.
  G5 irreversible        force push (incl. `+refspec`), `git reset --hard`, `git clean -f`, and
                         `terraform|tofu|terragrunt apply` without a saved plan file: no rollback.

Bypass: a stage printed as `<stage>: bypass - <why>` counts as pass only when a line of a
human message in this session starts with "bypass". G5 is bypassed the same way.
Kill-switch: CODE_BETTER_GUARD=off disables every check.
State and decision log live in `$(git rev-parse --git-path code-better)/`: never
committed, nothing to gitignore. Outside git, it falls back to Edit/Write tool calls.

Stdlib only. Any internal error fails open (allow) and prints to stderr, so a guard
bug never bricks a session.
"""
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import time

EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
SKILL_LOADED = re.compile(r"Base directory for this skill: \S*/code-better(?=\s|$)")  # not code-better-*
# Tolerates `gate: pass`, **gate:** pass, `Gate: PASS`; normalized to lowercase.
STAGE = re.compile(r"\b(gate|plan|verify|teardown/[a-z-]+)\**\s*:\s*\**\s*(pass|fail|bypass)\b([^\n`]*)", re.I)
REMINDER = re.compile(r"<(system-reminder|local-command-stdout)>.*?</\1>", re.S)
RUNG = re.compile(r"\brung=([a-z-]+)")
# "bypass" must start a line of a human message, so "don't bypass the gate" never counts.
USER_BYPASS = re.compile(r"^\s*bypass\b", re.I | re.M)
TAG = re.compile(r"<[^>\n]+>")
# Output styles that forbid text between tool calls (seen live) can declare stages via echo.
ECHO = re.compile(r"^\s*(echo|printf)\b")
# Inspect or undo only: always allowed, so a G1 block can never deadlock the session.
SAFE_CMD = re.compile(r"^\s*(cat|ls|head|tail|grep|rg|wc|pwd|echo|git\s+(status|diff|log|show|blame|restore|checkout|stash))\b")
SUBSHELL = re.compile(r"\$\(|`|<\(|>\(")
# Obvious file writes, checked on a segment with quoted strings blanked (so awk 'NF>1' is fine).
WRITES = re.compile(r">|\bsed\s+(-[A-Za-z]*i|--in-place)|\bperl\s+-[A-Za-z]*i|\btee\b"
                    r"|\b(mv|cp|rm|touch|truncate|patch|ln|dd)\b|\bgit\s+(apply|am)\b")
INTERP_HEREDOC = re.compile(r"\b(python3?|node|ruby|perl|bash|sh)\b[^\n]*<<")
HARMLESS_REDIRECT = re.compile(r"\d*>&\d+|&>\s*/dev/null|\d*>>?\s*/dev/null")
# Not counted by the git sensor: the skill's own files (code map, plans, state) and any
# tool state other plugins keep under .claude/ (seen live: autoharness session files).
# Edit/Write to .claude/settings.json and friends is still guarded by path (EXEMPT).
UNSENSED = ("CLAUDE.local.md", ".claude",
            # Caches a baseline test run writes, in repos that don't gitignore them (seen live).
            # ponytail: fixed list; extend when another cache shows up in a G1 block.
            "*__pycache__*", "*.pyc", "*.pytest_cache*", "*.mypy_cache*", "*.ruff_cache*",
            "*.coverage", "*.tox/*", "*node_modules*", "*.eslintcache", "*.tsbuildinfo")
EXEMPT = re.compile(r"^(CLAUDE\.local\.md|\.claude/(code-map\.md|state\.md|plans/.*))$")

GIT_COMMIT = re.compile(r"\bgit\b(\s+(-[Cc]\s+\S+|--\S+))*\s+commit\b")
FORCE_PUSH = re.compile(r"\bgit\b.*\bpush\b.*(\s--force(?!-with-lease|-if-includes)\b|\s-[A-Za-z]*f[A-Za-z]*\b|\s\+[^\s+])")
RESET_HARD = re.compile(r"\bgit\b.*\breset\b.*\s--hard\b")
CLEAN_FORCE = re.compile(r"\bgit\b.*\bclean\b.*(\s-[A-Za-z]*f|\s--force\b)")
TF_APPLY = re.compile(r"\b(terraform|tofu|terragrunt)\b(\s+-chdir=\S+)?(\s+run-all|\s+run\s+--all)?\s+apply\b(?P<args>.*)")
RETRY_SLEEP = 0.4  # seconds between transcript re-reads before a stage-line deny
TF_VALUE_FLAGS = {"-var", "-var-file", "-target", "-replace", "-parallelism", "-lock-timeout", "-state", "-state-out", "-backup"}


# ---------- sensor 1: transcript ----------

def read_events(transcript_path):
    """(events after the last code-better load, line number of that load), or None.

    ponytail: reads the whole transcript on every call; fine to tens of MB.
    Track a byte offset per session if hook latency ever shows up.
    """
    events, load = [], None
    try:
        lines = open(transcript_path, encoding="utf-8", errors="replace")
    except (OSError, TypeError):
        return None
    with lines:
        for n, line in enumerate(lines):
            if '"content"' not in line:
                continue
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if entry.get("isSidechain") or entry.get("type") not in ("user", "assistant"):
                continue
            content = (entry.get("message") or {}).get("content")
            blocks = [{"type": "text", "text": content}] if isinstance(content, str) else content or []
            for b in blocks:
                if not isinstance(b, dict):
                    continue
                text = b.get("text", "") if b.get("type") == "text" else ""
                if entry["type"] == "user":
                    if SKILL_LOADED.search(text):
                        events, load = [], n
                    elif text and not entry.get("isMeta"):
                        events.append(("human", bool(USER_BYPASS.search(TAG.sub("\n", REMINDER.sub("", text))))))
                elif text:
                    for m in STAGE.finditer(text):
                        events.append(("stage", m.group(1).lower(), m.group(2).lower(), m.group(3)))
                elif b.get("type") == "tool_use":
                    cmd = (b.get("input") or {}).get("command") or "" if b.get("name") == "Bash" else ""
                    if ECHO.match(cmd):  # `echo "gate: pass - ..."`: a stage line for no-narration styles
                        for m in STAGE.finditer(cmd):
                            events.append(("stage", m.group(1).lower(), m.group(2).lower(), m.group(3)))
                    events.append(("tool", b.get("id")))  # anchors this call's tree snapshot
                    if b.get("name") in EDIT_TOOLS:
                        inp = b.get("input") or {}
                        events.append(("edit", inp.get("file_path") or inp.get("notebook_path") or ""))
    return None if load is None else (events, load)


# ---------- sensor 2: git working-tree fingerprint ----------

def git(root, *args, env=None):
    r = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True, env=env, timeout=8)
    return r.stdout.strip() if r.returncode == 0 else None


def fingerprint(root, state_dir):
    """Tree hash of the whole working tree (tracked + untracked, minus .gitignore'd files
    and UNSENSED paths), built in a temp index so the real index is never touched.

    ponytail: writes blobs for changed files into .git/objects (git gc prunes them);
    a huge non-ignored untracked file gets hashed on every call.
    """
    tmp = os.path.join(state_dir, "index.%d" % os.getpid())
    real = git(root, "rev-parse", "--git-path", "index")
    try:
        if real and os.path.exists(os.path.join(root, real)):
            shutil.copy2(os.path.join(root, real), tmp)  # keep mtime: git racy-clean check stays correct
        env = dict(os.environ, GIT_INDEX_FILE=tmp)
        # Not `:(exclude)` pathspecs: naming an ignored path makes `git add` fail outright.
        if git(root, "add", "-A", "--", ".", env=env) is None:
            return None
        git(root, "rm", "-r", "-q", "--cached", "--ignore-unmatch", "--", *UNSENSED, env=env)
        return git(root, "write-tree", env=env)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


class State:
    def __init__(self, events, root, snaps, tree):
        self.events, self.root = events, root
        self.tree = tree
        # A snapshot is the tree just before a tool call. Place it at that call's tool_use
        # in the transcript (lag-proof); fall back to the event count when it was taken.
        where = {e[1]: i for i, e in enumerate(events) if e[0] == "tool"}
        self.snaps = [(where.get(s[2], s[0]) if len(s) > 2 else s[0], s[1]) for s in snaps]
        self.bypass_ok = any(e[0] == "human" and e[1] for e in events)

    def last(self, kind, name=None):
        for i in range(len(self.events) - 1, -1, -1):
            e = self.events[i]
            if e[0] == kind and (name is None or e[1] == name):
                return i
        return -1

    def passed(self, name, after=-1):
        """Index of the last `name` stage line if it passed and comes after `after`, else -1."""
        i = self.last("stage", name)
        if i <= after:
            return -1
        status = self.events[i][2]
        return i if status == "pass" or (status == "bypass" and self.bypass_ok) else -1

    def changed_since(self, idx):
        """Files changed after event `idx` (-1 = since the skill loaded)."""
        if self.tree is None:  # no git: fall back to Edit/Write tool calls
            return sorted({os.path.relpath(e[1], self.root) for e in self.events[idx + 1:]
                           if e[0] == "edit" and guarded(e[1], self.root)})
        ref = next((t for n, t in self.snaps if n > idx), None)
        if ref is None or ref == self.tree:
            return []
        return (git(self.root, "diff", "--name-only", ref, self.tree) or "?").split("\n")

    def build_open(self):
        """None if Build may change files; else (rule, what is missing)."""
        g = self.passed("gate")
        rung = RUNG.search(self.events[g][3]) if g >= 0 else None
        if g >= 0 and not rung and self.events[g][2] == "pass":  # a user bypass waives the rung
            return ("G1", "a `rung=` in your `gate:` line, e.g. `gate: pass - tier=internal rung=micro - <reason>`")
        if g < 0:
            return ("G1", "a `gate:` line, and none is in your visible replies since the skill loaded "
                          "(the guard cannot see thinking). Write it as plain text before your next tool call, or, "
                          "if your output style forbids text between tool calls, run it as its own Bash call: "
                          "echo \"gate: pass - tier=<sandbox|internal|prod> rung=<one-liner|micro|full|project> - <reason>\" "
                          "(SKILL.md section 1)")
        if rung and rung.group(1) in ("full", "project"):
            p = self.passed("plan", g)
            if p < 0:
                return ("G2", "the plan file and `plan: pass - ...` (rung=%s, SKILL.md section 2)" % rung.group(1))
            if self.passed("teardown/readiness", p) < 0:
                return ("G2", "the 5 teardown rounds ending with `teardown/readiness: pass - ...` "
                              "(rung=%s, SKILL.md section 3)" % rung.group(1))
        return None


def guarded(path, root):
    """True for files inside the repo that are not skill-owned working files."""
    if not path:
        return False
    full = os.path.realpath(os.path.join(root, path))
    root = os.path.realpath(root)
    if not full.startswith(root + os.sep):
        return False
    return not EXEMPT.match(os.path.relpath(full, root).replace(os.sep, "/"))


# ---------- checks ----------

def check_change_order(st, about_to_edit=None):
    """G1/G2: no file changes until the gate (and plan + teardown at full rung) pass."""
    missing = st.build_open()
    if not missing:
        return None
    if about_to_edit is not None and guarded(about_to_edit, st.root):
        return (missing[0], "code-better: edit blocked, needs %s first." % missing[1])
    changed = st.changed_since(-1)
    if changed:
        return (missing[0], "code-better: files changed before the gate: %s. Needs %s. If you made these "
                "changes early, say so; never revert a file you did not change (the user may have)." % (", ".join(changed[:8]), missing[1]))
    return None


def tf_apply_without_plan(cmd):
    m = TF_APPLY.search(cmd)
    if not m:
        return False
    skip = False
    for a in m.group("args").split():
        if skip:
            skip = False
        elif a in TF_VALUE_FLAGS:
            skip = True
        elif not a.startswith("-"):
            return False  # positional arg = saved plan file
    return True


def unquoted(s):
    return re.sub(r"'[^']*'|\"[^\"]*\"", "''", s)


def check_bash(st, cmd):
    # One check per simple command, so `git push x && rm -rf y` doesn't read as a force push.
    segments = re.split(r"&&|\|\||[;|&\n]", HARMLESS_REDIRECT.sub(" ", cmd))
    risky = (
        (FORCE_PUSH.search, "force push rewrites shared history; use `git revert <sha>` or `--force-with-lease` on your own branch"),
        (RESET_HARD.search, "`git reset --hard` destroys uncommitted work; use `git stash` or `git revert`"),
        (CLEAN_FORCE.search, "`git clean -f` deletes untracked files with no undo; list them with `git clean -n` and ask"),
        (tf_apply_without_plan, "apply only a saved plan: `terraform plan -out=tfplan`, review it, then `terraform apply tfplan`"),
    )
    for test, why in risky:
        if not st.bypass_ok and any(test(s) for s in segments):
            return ("G5", "code-better: blocked irreversible command: %s (SKILL.md Rollback). "
                    "The user can approve by starting a message with \"bypass\"." % why)
    missing = st.build_open()
    if missing:
        writes = INTERP_HEREDOC.search(cmd) or any(WRITES.search(unquoted(s)) for s in segments)
        if writes and "info/exclude" not in cmd:  # the code-map wiring edits info/exclude pre-gate
            return (missing[0], "code-better: file write blocked, needs %s first." % missing[1])
        safe = all(SAFE_CMD.match(s) and not SUBSHELL.search(s) for s in segments if s.strip())
        order = check_change_order(st)
        if order and not safe:
            return order
    if any(GIT_COMMIT.search(s) for s in segments):
        v = st.passed("verify")
        changed = st.changed_since(v)
        if changed:
            return ("G3", "code-better: %s changed since the last passing verify. Run Verify (SKILL.md section 5) "
                    "and print `verify: pass - <n>/<n> ...` before committing." % ", ".join(changed[:8]))
    return None


def check_stop(st, event):
    if event.get("stop_hook_active"):
        return None  # already blocked once this turn; never loop
    order = check_change_order(st)  # a gate printed only in the final message is too late
    if order:
        return order
    # The final message may not be in the transcript yet; Stop gets it directly.
    for m in STAGE.finditer(event.get("last_assistant_message") or ""):
        if m.group(1).lower() == "verify":
            st.events.append(("stage", "verify", m.group(2).lower(), m.group(3)))
    changed = st.changed_since(st.last("stage", "verify"))
    if changed:
        return ("G4", "code-better: %s changed since the last `verify:` line. Run Verify (SKILL.md section 5) and "
                "print `verify: pass|fail - ...` with the evidence before ending the turn." % ", ".join(changed[:8]))
    return None


# ---------- wiring ----------

def evaluate(event, st):
    name, tool, inp = event.get("hook_event_name"), event.get("tool_name"), event.get("tool_input") or {}
    if name == "Stop":
        return check_stop(st, event)
    if tool in EDIT_TOOLS:
        return check_change_order(st, inp.get("file_path") or inp.get("notebook_path") or "")
    if tool == "Bash":
        return check_bash(st, inp.get("command") or "")
    return None


def decide(event):
    """Return (rule, reason) to block, or None to allow."""
    if os.environ.get("CODE_BETTER_GUARD", "").lower() == "off":
        return None
    parsed = read_events(event.get("transcript_path"))
    if parsed is None:
        return None
    events, load = parsed
    root = os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or os.getcwd()
    state_dir = git(root, "rev-parse", "--path-format=absolute", "--git-path", "code-better")
    snaps, tree, snap_file = [], None, None
    if state_dir:
        os.makedirs(state_dir, exist_ok=True)
        snap_file = os.path.join(state_dir, "%s-%d.jsonl" % (event.get("session_id") or "nosession", load))
        tree = fingerprint(root, state_dir)
        if tree and os.path.exists(snap_file):
            with open(snap_file) as f:
                snaps = [json.loads(l) for l in f if l.strip()]
        if tree:
            rec = [len(events), tree, event.get("tool_use_id")]
            snaps.append(rec)
            with open(snap_file, "a") as f:
                f.write(json.dumps(rec) + "\n")
    name, tool = event.get("hook_event_name"), event.get("tool_name")
    verdict = evaluate(event, State(events, root, snaps, tree))
    # The transcript line for the message that carries this tool call can land a moment
    # after the hook starts (seen live: `gate: pass` + first call in one message, denied).
    # Before denying on a missing stage line, re-read a few times.
    for _ in range(3):
        if not verdict or verdict[0] not in ("G1", "G2", "G3") or name == "Stop":
            break
        time.sleep(RETRY_SLEEP)
        events = (read_events(event.get("transcript_path")) or ([], 0))[0]
        verdict = evaluate(event, State(events, root, snaps, tree))
    if state_dir:
        log(state_dir, name, tool, verdict)
    return verdict


def log(state_dir, name, tool, verdict):
    """One JSON line per armed decision, so you can see which controls earn their place."""
    try:
        with open(os.path.join(state_dir, "harness.log"), "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                "event": name, "tool": tool,
                "decision": "block" if verdict else "allow",
                "rule": verdict[0] if verdict else None,
            }) + "\n")
    except OSError:
        pass


def main():
    try:
        event = json.load(sys.stdin)
        verdict = decide(event)
    except Exception as exc:  # fail open: a guard bug must not brick the session
        print("code-better guard error (allowing): %r" % exc, file=sys.stderr)
        return 0
    if verdict:
        if event.get("hook_event_name") == "Stop":
            out = {"decision": "block", "reason": verdict[1]}
        else:
            out = {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                          "permissionDecision": "deny",
                                          "permissionDecisionReason": verdict[1]}}
        print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
