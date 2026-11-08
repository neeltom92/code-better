# code-better

A Claude Code agent harness for senior engineers working in large existing codebases. It merges [obra/superpowers](https://github.com/obra/superpowers) and [bmtrnavsky/disciplined-vibe-coding](https://github.com/bmtrnavsky/disciplined-vibe-coding) into one adaptive, gated lifecycle shaped like AWS's AI-DLC ([awslabs/aidlc-workflows](https://github.com/awslabs/aidlc-workflows)), and enforces the gates with hooks instead of hoping the model follows prose:

```text
INCEPTION                          CONSTRUCTION         HAND-OFF
Gate -> Plan -> Teardown -> [approve] -> Build -> Verify -> Hand-off (commands for the user)
```

Agent = model + harness. Claude Code supplies the loop, tools, and permissions. code-better adds the workflow (a skill) and the guardrails that make it stick: a hook script (`guard.py`) that blocks the next step until the current gate has passed. The **scope** picks which stages run, the **rung** picks how deep each goes, the **tier** picks who must approve.

## What is enforced

Instructions alone are often skipped. In our own live runs, the agent edited files through a Bash heredoc before ever declaring the gate. So every gate below is checked by a script against two sensors. The **session transcript** shows which stage lines were printed. A **git working-tree fingerprint** catches files changed by any tool: Edit, Write, `sed -i`, or a heredoc.

| Rule | Blocks | Incident it exists for |
|---|---|---|
| G1 | any file change before `gate: pass` | agent edited code, then printed the gate at the end |
| G2 | at full/project rung, changes before `plan: pass` and `teardown/readiness: pass` | building an unreviewed plan |
| G3 | `git commit` with files changed after the last `verify: pass` | "done" without fresh evidence |
| G4 | ending the turn with files changed after the last `verify:` line | same, without a commit |
| G5 | force push, `git reset --hard`, `git clean -f`, `terraform`/`tofu`/`terragrunt destroy`, or `apply` without a saved plan | no rollback path |

G3 and G5 are backstops: the agent never commits, pushes, merges, deploys, or applies at all (see Hand-off below), but a command that slips through still meets the guard.

The guard is armed only after the skill loads in a session; other sessions pass straight through. Read-only and revert commands are always allowed, so a block can't deadlock you. The skill's own working files don't count as changes, and neither does tool state other plugins keep under `.claude/`. Before the gate, Bash is limited to reads: obvious writes (`>`, `sed -i`, `tee`, interpreter heredocs, `mv`/`cp`/`rm`) are blocked. Anything that slips through is caught by the git sensor on the next call. Any guard error fails open. Cost: about 0.2 s per tool call on a 7k-file repo (django).

## The stages

**Inception**

- **Gate**: in an existing repo, first build or refresh a ≤80-line code map (`.claude/code-map.md`: stack, commands, layout, entry points, hubs, danger zones), imported from `CLAUDE.local.md` so later sessions load it. No graphify needed. Then read the code, turn the request into acceptance criteria, ask the questions that change the work, and declare scope, tier, and rung: `gate: pass - scope=feature tier=internal rung=micro - <reason>`.
- **Plan**: follow the repo's patterns. Steps come with check commands; reuse comes first; every destructive step has a rollback line. Public-surface changes stay additive. Add dry-run, idempotency, metric bands, a kill-switch, and a deploy runbook for the hand-off when relevant.
- **Teardown**: cold, adversarial review of the plan before code. Two passes at `micro`; five rounds by a fresh subagent at `full` and above.

**Construction**

- **Build**: lazy ladder (reuse, then stdlib, then minimum code). Baseline test run first. Red-green TDD, with characterization tests for untested legacy code. Offline-first infra checks before any live diff. Root-cause debugging; a prod incident starts by handing the user the rollback command. After 2 failed fixes, loop back to Plan or Gate and let the user choose.
- **Verify**: targeted tests plus the repo's CI checks for changed paths. Failures already on the baseline are reported, not "fixed". A near-miss is a fail. Full/prod work gets a review fan-out (`references/review.md`).

**Hand-off**

- **Hand-off**: the agent's work ends with verified changes in the working tree. It never runs `git add`, commit, push, PR merge, deploys, `terraform apply`, or prod restarts, even when the session has permission. It secret-scans the diff, then prints the exact commit, PR, and deploy-runbook commands (deploy path, watch command with abort band, rollback) for you to run (`handoff: pass - ...`). Built for enterprises where the agent's credentials could merge or deploy.

**Scopes** pick the route: `feature`, `bugfix`, `refactor`, `infra`, `security-patch`, `review`, `feedback`, `poc`, `done-check`. A bugfix adds Debug; a done-check runs a one-liner gate, then Verify and Hand-off. **Rungs** (`one-liner` / `micro` / `full` / `project`) set depth; **tiers** (`sandbox` / `internal` / `prod`) set approvals.

**Checkpoints**: open questions, plan approval (full/project rung or prod tier), and loopbacks that change an approved plan. The agent stops with a fixed `**<Stage> complete:** ... Approve → <next> | Request changes` message and continues only on a human reply. Urgency is not approval.

**Record**: at full/project rung, plans and questions files (`[Answer]:` tags) under `.claude/plans/`, a `state.md` resume point, and an append-only `.claude/audit.md` (also in prod tier at any rung): one block per human decision, ISO timestamp from `date -u`, the operator from `git config user.name`, the human's words quoted verbatim.

**Learnings**: when you correct the agent in a way that applies again, it asks "Keep that for next time?" and saves it to the project CLAUDE.md or your `CLAUDE.local.md`.

## How it maps to AI-DLC

| AI-DLC | code-better |
|---|---|
| Inception / Construction / Operations phases | Inception / Construction / Hand-off: Operations becomes commands the user runs |
| Scopes and adaptive stage selection | scopes table |
| Adaptive depth | rung |
| Stage gates and human approval | checkpoints with a hard stop |
| Questions files | `plans/NN-<slice>-questions.md` with `[Answer]:` tags |
| `aidlc-state.md` | `.claude/state.md` |
| `audit.md` | `.claude/audit.md` |
| Reverse engineering (brownfield) | code map |
| Reviewer | teardown |
| Sensors | guard (transcript + git) and Verify |
| Loopback | loopback |
| Learnings | learnings |

Left out on purpose: the ideation phase, the 14 role agents, the TypeScript engine, and the sharded audit. One skill file plus one stdlib hook keeps the context and install cost small enough for every task.

## Install

Requires [Claude Code](https://code.claude.com). The hooks also need `python3` and `git` on PATH: stdlib only, nothing to pip install. Without them the hooks fail open, and you get the skill without enforcement (with no `python3`, each guarded tool call also shows a `python3: not found` hook error).

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

**4. Copy into a repo (no marketplace access):** get this repo into `~/code-better` (`git clone`, or your internal mirror or tarball), then:

```bash
cd /path/to/your-repo
mkdir -p .claude/skills
rm -rf .claude/skills/code-better   # only when updating an existing copy
cp -R ~/code-better/skills/code-better .claude/skills/
# no .claude/settings.json yet: copy the hooks block; otherwise merge its "hooks" key by hand
if [ -e .claude/settings.json ]; then echo 'merge "hooks" from .claude/skills/code-better/hooks/settings.json into .claude/settings.json'; else cp .claude/skills/code-better/hooks/settings.json .claude/settings.json; fi
```

Invoke it as `/code-better <task>`. Commit `.claude/skills/code-better` and `.claude/settings.json` to share it with the team.

**5. Air-gapped (no GitHub, no installs, only Claude Code):** open Claude Code at the repo root and paste the upgrade prompt from `CHANGELOG.md`. It carries every skill file with checksums, installs or upgrades `.claude/skills/code-better`, merges the hooks into `.claude/settings.json`, keeps your team's edits, and prints the commit commands for you. It needs only `git` and `python3`. Claude Code asks you to approve each write under `.claude/`; approve them, or the prompt stops and removes its backup.

**6. Skill only, no enforcement:** `ln -sfn ~/code-better/skills/code-better ~/.claude/skills/code-better`.

**Other agents (no hooks):** tools that read `AGENTS.md` can follow the skill with one line in `AGENTS.md` pointing at `skills/code-better/SKILL.md` (or wherever you copied it). The hooks are Claude Code only, so there is no enforcement.

**Enterprise rollout:** to move an existing copy to v2 without network access, use the "Upgrade prompt" in `CHANGELOG.md` (option 5).

Check: run `/skills`, or start a task and look for a `gate:` line (in the reply or in an `echo` call) and for new lines in the decision log (below). If the superpowers, caveman, or ponytail plugins are enabled, disable them with `/plugin`; they inject overlapping rules.

## Use

```text
/code-better:code-better add rate limiting to POST /login
/code-better:code-better CI is failing on the integration job since yesterday
```

Copy installs (options 4-6) drop the prefix: `/code-better <task>`.

When a hook blocks, its message names exactly what's missing, for example "needs a `gate:` line". The agent supplies it and continues. Stage lines count when written as reply text, or as their own `echo "gate: pass - ..."` Bash call. The echo form is for terse output styles that forbid text between tool calls; text in thinking is invisible to the guard.

## Operating the harness

- **Bypass:** start a message (or a line of it) with `bypass`, e.g. `bypass - prod is down, skip the plan`. The agent then prints `<stage>: bypass - <what was red>, waived by user: <why>`. G5 has no bypass: under the Hand-off rule you run those commands yourself. "don't bypass" mid-sentence does not count.
- **Off switch:** `CODE_BETTER_GUARD=off claude` disables every check for that session.
- **Decision log:** one JSON line per armed hook call, in `$(git rev-parse --git-path code-better)/harness.log`. Use it to see which rules fire, and drop a rule whose incident stops happening:
  ```bash
  jq -r 'select(.decision=="block").rule' "$(git rev-parse --git-path code-better)/harness.log" | sort | uniq -c
  # no jq: grep -o '"rule": "G[0-9]"' "$(git rev-parse --git-path code-better)/harness.log" | sort | uniq -c
  ```
- **Tests:** `python3 -m unittest discover -s tests`. Every rule is tested both ways (must block / must allow). CI runs them on each push.

## Files it writes in your repo

- **Under `.claude/`:** `code-map.md`, `plans/NN-<slice>.md` and `plans/NN-<slice>-questions.md` (full and project rung), `audit.md` (full and project rung, or prod tier; append-only), and `state.md` (project rung). They stay out of git through `info/exclude` by default, which is worktree-safe and leaves the team `.gitignore` untouched. Share `audit.md` when you need the trail for compliance.
- **`CLAUDE.local.md`:** one `@.claude/code-map.md` import line.
- **Harness state and log:** inside `.git/code-better/`, so they are never committed.

Formats are in `skills/code-better/references/`.

## Layout

```text
skills/code-better/SKILL.md                  the skill (workflow, ≤250 lines)
skills/code-better/references/               plan/questions/state/audit formats, code-map build rules, review.md (review fan-out)
skills/code-better/hooks/guard.py            the harness guard (stdlib Python)
skills/code-better/hooks/settings.json       hooks block for per-repo copy installs
hooks/hooks.json                             hooks block for the plugin install
.claude-plugin/                              plugin + marketplace manifests
tests/                                       two-sided guard tests, upgrade-prompt freshness test
scripts/upgrade_prompt.py                    refreshes the skill files embedded in the CHANGELOG upgrade prompt
CHANGELOG.md                                 what changed per version
```

## Credits and license

MIT, see `LICENSE`. Adapts material from obra/superpowers (MIT, Jesse Vincent), bmtrnavsky/disciplined-vibe-coding (MIT, Brad Trnavsky), and the ponytail plugin (MIT, DietrichGebert); their notices are in `THIRD_PARTY_NOTICES.md`. The lifecycle shape (phases, scopes, adaptive depth, approval checkpoints, questions, state, and audit files) adapts ideas from [awslabs/aidlc-workflows](https://github.com/awslabs/aidlc-workflows) (MIT-0, Amazon.com, Inc. or its affiliates); no text is copied. The review fan-out follows the logic of the `code-review` command in [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) (Apache-2.0); no text is copied. Harness design follows [The State of AI Harness Engineering 2026](https://marmelab.com/blog/2026/09/24/the-state-of-ai-harness-engineering-2026.html): enforce with scripts, test both ways, log usage, and record why each control exists.
