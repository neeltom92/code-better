# code-better

A Claude Code agent harness for senior engineers working in large existing codebases. It merges [obra/superpowers](https://github.com/obra/superpowers) and [bmtrnavsky/disciplined-vibe-coding](https://github.com/bmtrnavsky/disciplined-vibe-coding) into one gated pipeline, and enforces the gates with hooks instead of hoping the model follows prose:

```text
Gate --> Plan --> Teardown --> Build (test-first, debug) --> Verify --> Commit
```

Agent = model + harness. Claude Code supplies the loop, tools, and permissions. code-better adds the workflow (a skill) and the guardrails that make it stick: a hook script (`guard.py`) that blocks the next step until the current gate has passed.

## What is enforced

Instructions alone are often skipped. In our own live runs, the agent edited files through a Bash heredoc before ever declaring the gate. So every gate below is checked by a script against two sensors. The **session transcript** shows which stage lines were printed. A **git working-tree fingerprint** catches files changed by any tool: Edit, Write, `sed -i`, or a heredoc.

| Rule | Blocks | Incident it exists for |
|---|---|---|
| G1 | any file change before `gate: pass` | agent edited code, then printed the gate at the end |
| G2 | at full/project rung, changes before `plan: pass` and `teardown/readiness: pass` | building an unreviewed plan |
| G3 | `git commit` with files changed after the last `verify: pass` | "done" without fresh evidence |
| G4 | ending the turn with files changed after the last `verify:` line | same, without a commit |
| G5 | force push, `git reset --hard`, `git clean -f`, `terraform`/`tofu`/`terragrunt apply` without a saved plan | no rollback path |

The guard is armed only after the skill loads in a session; other sessions pass straight through. Read-only and revert commands are always allowed, so a block can't deadlock you. The skill's own working files don't count as changes, and neither does tool state other plugins keep under `.claude/`. Before the gate, Bash is limited to reads: obvious writes (`>`, `sed -i`, `tee`, interpreter heredocs, `mv`/`cp`/`rm`) are blocked. Anything that slips through is caught by the git sensor on the next call. Any guard error fails open. Cost: about 0.2 s per tool call on a 7k-file repo (django).

## The stages

- **Gate**: in an existing repo, first build or refresh a ≤80-line code map (`.claude/code-map.md`: stack, commands, layout, entry points, hubs, danger zones), imported from `CLAUDE.local.md` so later sessions load it. No graphify needed. Then read the code, and declare a stakes tier (`sandbox` / `internal` / `prod`) and a scope rung (`one-liner` / `micro` / `full` / `project`). The rung sets how much process the later stages get.
- **Plan**: follow the repo's patterns. Steps come with check commands; reuse comes first; every destructive step has a rollback line. Public-surface changes stay additive. Add dry-run, idempotency, metric bands, and a kill-switch when relevant.
- **Teardown**: cold review of the plan before code. Two passes at `micro`; five rounds by a fresh subagent at `full` and above.
- **Build**: lazy ladder (reuse, then stdlib, then minimum code). Baseline test run first. Red-green TDD, with characterization tests for untested legacy code. Offline-first infra checks before any live diff. Root-cause debugging, stopping after 2 failed fixes.
- **Verify**: targeted tests plus the repo's CI checks for changed paths. Failures already on the baseline are reported, not "fixed". A near-miss is a fail.
- **Subagents**: review fan-out for full/prod work. Parallel single-lens reviewers; every finding is validated by a separate subagent.
- **Commit**: only when asked, after a secret scan of the staged diff.

## Install

Requires [Claude Code](https://code.claude.com). The hooks also need `python3` and `git` on PATH: stdlib only, nothing to pip install. Without them the hooks fail open, and you get the skill without enforcement.

**1. Plugin (recommended: skill + hooks, updates with the plugin):**

```bash
claude plugin install code-better --marketplace neeltom92/code-better
```

Or in a session: `/plugin install code-better --marketplace neeltom92/code-better`. Invoke it as `/code-better:code-better <task>`, or let it trigger on coding tasks.

**2. Team: require it in one repo.** Commit this to the repo's `.claude/settings.json`. Contributors get the plugin after they trust the folder:

```json
{
  "extraKnownMarketplaces": {
    "code-better": { "source": { "source": "github", "repo": "neeltom92/code-better" } }
  },
  "enabledPlugins": { "code-better@code-better": true }
}
```

**3. Org-wide.** Put the same two keys in managed settings (MDM or the managed settings file). See [Manage plugins for your organization](https://code.claude.com/docs/en/plugins/org). Forking this repo into your org and pointing `repo` at the fork gives you a reviewed, pinned copy. In `-p`/CI runs, set `CLAUDE_CODE_SYNC_PLUGIN_INSTALL=1` so the plugin is installed before the first turn.

**4. Copy into a repo (no marketplace access, air-gapped):**

```bash
git clone https://github.com/neeltom92/code-better ~/code-better
cd /path/to/your-repo
mkdir -p .claude/skills
rm -rf .claude/skills/code-better   # only when updating an existing copy
cp -R ~/code-better/skills/code-better .claude/skills/
# no .claude/settings.json yet: copy the hooks block; otherwise merge its "hooks" key by hand
test -e .claude/settings.json || cp .claude/skills/code-better/hooks/settings.json .claude/settings.json
```

Invoke it as `/code-better <task>`. Commit `.claude/skills/code-better` and `.claude/settings.json` to share it with the team.

**5. Skill only, no enforcement:** `ln -sfn ~/code-better/skills/code-better ~/.claude/skills/code-better`.

Check: run `/skills`, or start a task and look for a `gate:` line. If the superpowers, caveman, or ponytail plugins are enabled, disable them with `/plugin`; they inject overlapping rules.

## Use

```text
/code-better:code-better add rate limiting to POST /login
/code-better:code-better CI is failing on the integration job since yesterday
```

When a hook blocks, its message names exactly what's missing, for example "needs a `gate:` line". The agent supplies it and continues. Stage lines count when written as reply text, or as their own `echo "gate: pass - ..."` Bash call. The echo form is for terse output styles that forbid text between tool calls; text in thinking is invisible to the guard.

## Operating the harness

- **Bypass:** start a message (or a line of it) with `bypass`, e.g. `bypass - prod is down, skip the plan`. The agent then prints `<stage>: bypass - <why>`, and G5 commands go through. "don't bypass" mid-sentence does not count.
- **Off switch:** `CODE_BETTER_GUARD=off claude` disables every check for that session.
- **Decision log:** one JSON line per armed hook call, in `$(git rev-parse --git-path code-better)/harness.log`. Use it to see which rules fire, and drop a rule whose incident stops happening:
  ```bash
  jq -r 'select(.decision=="block").rule' "$(git rev-parse --git-path code-better)/harness.log" | sort | uniq -c
  ```
- **Tests:** `python3 -m unittest discover -s tests`. Every rule is tested both ways (must block / must allow). CI runs them on each push.

## Files it writes in your repo

- **Under `.claude/`:** `code-map.md`, `plans/NN-<slice>.md` (full and project rung), and `state.md` (project rung). They stay out of git through `info/exclude` by default, which is worktree-safe and leaves the team `.gitignore` untouched.
- **`CLAUDE.local.md`:** one `@.claude/code-map.md` import line.
- **Harness state and log:** inside `.git/code-better/`, so they are never committed.

Formats are in `skills/code-better/references/`.

## Layout

```text
skills/code-better/SKILL.md                  the skill (workflow, ≤250 lines)
skills/code-better/references/               plan/state formats, code-map build rules
skills/code-better/hooks/guard.py            the harness guard (stdlib Python)
skills/code-better/hooks/settings.json       hooks block for per-repo copy installs
hooks/hooks.json                             hooks block for the plugin install
.claude-plugin/                              plugin + marketplace manifests
tests/test_guard.py                          two-sided guard tests
CHANGELOG.md                                 what changed per version
```

## Credits and license

MIT, see `LICENSE`. Adapts material from obra/superpowers (MIT, Jesse Vincent), bmtrnavsky/disciplined-vibe-coding (MIT, Brad Trnavsky), and the ponytail plugin (MIT, DietrichGebert); their notices are in `THIRD_PARTY_NOTICES.md`. The review fan-out follows the logic of the `code-review` command in [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) (Apache-2.0); no text is copied. Harness design follows [The State of AI Harness Engineering 2026](https://marmelab.com/blog/2026/09/24/the-state-of-ai-harness-engineering-2026.html): enforce with scripts, test both ways, log usage, and record why each control exists.
