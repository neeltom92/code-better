# Changelog

All notable changes to code-better. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [SemVer](https://semver.org/). The version here matches `.claude-plugin/plugin.json`.

Upgrading a per-repo copy: read the entries since your version, then re-copy `skills/code-better/` and re-merge `hooks/settings.json` if the Changed section mentions hooks. From 2.0.0 on, each release also carries a self-contained **upgrade prompt** with every skill file embedded: paste it into Claude Code in the repo you are upgrading. It needs no network access.

## [2.0.0] - 2026-11-08

code-better now follows the shape of AWS's AI-DLC workflows ([awslabs/aidlc-workflows](https://github.com/awslabs/aidlc-workflows)): an adaptive lifecycle in three phases, where a scope picks the stages, the rung picks the depth, and the tier picks who approves. The lean core stays: lazy ladder, test-first, root-cause debugging, rollback lines, fresh evidence, and the hook guard. Ideas were adapted from AI-DLC; no text was copied.

### Added

- **Phases.** SKILL.md is grouped as Inception (1 Gate, 2 Plan, 3 Teardown), Construction (4 Build, 5 Verify), and Hand-off (6 Hand-off). Sections 1-5 keep their numbers, so guard messages stay valid.
- **Scopes** replace the "Pick the entry" table: `feature`, `bugfix`, `refactor`, `infra`, `security-patch`, `review`, `feedback`, `poc`, `done-check`. Each lists the stages it runs. The gate line names it: `gate: pass - scope=bugfix tier=prod rung=micro - <reason>`.
- **Checkpoints.** The agent stops and ends its turn for questions that change the work, plan approval (full/project rung, or prod tier at any rung), and loopbacks that change an approved plan. The approval message has one fixed shape. Silence, urgency, or "just get it done" is not approval (new iron law 7).
- **Questions file.** At full/project rung, two or more open questions go to `.claude/plans/NN-<slice>-questions.md`, with lettered options, a recommended default, and `[Answer]:` tags.
- **Audit log.** At full/project rung, and in prod tier at any rung, `.claude/audit.md` is append-only, with one block per human decision: scope overrides, answers, approvals, change requests, bypasses, loopbacks, hand-offs. Each block has a UTC timestamp from `date -u`, the operator from `git config user.name`, and the human's words verbatim.
- **Hand-off instead of Operations.** The agent's work ends with verified changes in the working tree. It never runs `git add`, `git commit`, `git push`, PR create or merge, deploys, `terraform apply`, `helm upgrade|rollback`, `kubectl apply|rollout`, prod restarts, or data fixes, even when the session has permission or the user says "ship it". Section 6 secret-scans the diff and prints the exact commands for the user: branch, `git add <exact files>`, commit, push/PR, and a deploy runbook (deploy path, watch command with the abort band and window, rollback). Exit: `handoff: pass - ...`. Built for enterprises where the agent's credentials could merge or deploy.
- **Incident handling.** A prod break after a deploy or flag change → first hand the user the exact rollback or flag-off command, then find the root cause. "Fast" or "skip the tests" is not a bypass.
- **Loopback.** After 2 failed fixes, or when Verify shows the plan was wrong, work goes back to Plan (re-teardown, re-approval) or to Gate, and is recorded.
- **Learnings.** A user correction that applies again → "Keep that for next time? project / personal / no", saved to CLAUDE.md or `CLAUDE.local.md`.
- `references/review.md`: the review fan-out procedure, moved out of SKILL.md and loaded on demand.
- `references/templates.md`: questions file, audit log, and a state file with phase checkboxes (`[ ]`, `[-]`, `[?]`, `[x]`, `[S]`). The plan template gains Deploy runbook, Approval, and Loopbacks sections.
- Self-contained upgrade prompt (below): carries all six skill files with sha256 checksums, so a laptop with only Claude Code can install or upgrade offline from any earlier version, keeping team edits. `scripts/upgrade_prompt.py` regenerates it and `tests/test_upgrade_prompt.py` fails CI when it goes stale.
- README: air-gapped install option (paste the upgrade prompt), copy-install invocation note, a `jq`-free decision-log query, and a loud hint when `.claude/settings.json` already exists and the hooks need a manual merge.
- Guard tests: record files are writable before the gate, look-alike paths are not, a `scope=` gate line passes, a `scope=` gate line without `rung=` is still blocked, and the review fixes above, each both ways (72 cases with the upgrade-prompt tests).

### Changed

- Hooks: `guard.py` now also exempts `.claude/audit.md`, alongside the other record files. The G3 and G5 block messages now tell the agent to hand the command to the user. Fixes from an end-to-end review: G5 also blocks `terraform|tofu|terragrunt destroy`; G5 has no bypass any more, since the user runs those commands (a single early "bypass" used to unlock force push and plan-less apply for the whole session); a "bypass" in the message that loads the skill now counts; a loopback to Gate no longer blames already-verified Build changes as "changed before the gate"; gate lines in backticks or capitals (`` `gate: pass` - ... rung=Micro ``) keep their rung; the state directory works on git older than 2.31 (Debian 11, Ubuntu 20.04); temp index files left by a hook killed at its timeout are cleaned up (only when their process is gone); outside git, an Edit the guard refused no longer counts as a change before the gate. Known gaps are listed in the guard's docstring. `hooks/settings.json` and `hooks/hooks.json` are unchanged. Old gate lines without `scope=` still pass.
- Gate rule: one bypass format, `<stage>: bypass - <what was red>, waived by user: <why>`, valid only after a user message (or a line of it) that starts with "bypass". A stage left out by your scope or rung prints nothing. Skipping one they require is a defect.
- Micro teardown rounds are named `teardown/consequence` and `teardown/alternatives`.
- Project rung means more than one slice, or work across sessions. Each slice gets its own plan approval.
- Flags: if the repo has no flag mechanism, ask before adding one.
- The `poc` scope is capped at micro rung. Loopbacks can return to Debug when the cause is still unknown. The agent proposes the scope; the user can override it. Never set `CODE_BETTER_GUARD=off` yourself.
- README, CLAUDE.md, THIRD_PARTY_NOTICES (AI-DLC credit, MIT-0), and the plugin manifests describe the new lifecycle.

### Upgrade prompt (copy into Claude Code)

For teams whose laptops have Claude Code but no network or package-install access. The prompt is self-contained: it carries every 2.0.0 skill file plus checksums, so nothing else has to reach the laptop. It upgrades a per-repo copy from any earlier version (keeping your team's edits), or installs a fresh copy. It needs only `git` and `python3`, which the hooks need anyway. Plugin installs update from their marketplace instead: `claude plugin update code-better@code-better`, then restart Claude Code.

How to use it: open Claude Code at the root of the repo that holds (or should hold) `.claude/skills/code-better`, paste the whole block below, and review the diff it reports. It never commits; it prints the commit commands for you.

<details>
<summary>Upgrade prompt for 2.0.0 (about 1,000 lines; use the code block's copy button)</summary>

`````text
Install or upgrade the code-better skill in this repository to version 2.0.0, using only the files in this message. Work offline: do not download, clone, fetch, or install anything, and do not use web tools. If a step seems to need the network, stop and tell me.

Before changing any file, print this line as plain text (an active code-better guard needs it):
gate: pass - scope=refactor tier=internal rung=micro - code-better 2.0.0 upgrade
After step 7 passes, print "verify: pass - <results>" as plain text. Never commit, push, or open a PR: step 8 gives me the commands.
Claude Code asks me to approve writes under .claude/; wait for my approval. If a write is refused, stop, delete the backup from step 2, and tell me. Never work around a refused write with Bash.

Definitions:
- Run every command from the repo root (git rev-parse --show-toplevel).
- TARGET = .claude/skills/code-better
- The six files to write are at the end of this message, each between a "=== BEGIN <path> ===" line and an "=== END <path> ===" line. <path> is relative to TARGET. A file's content is every line between its two marker lines, ending with exactly one newline.

Steps:
1. Find the current install.
   - TARGET/SKILL.md exists: this is an upgrade. If its frontmatter name is not code-better, stop and tell me.
   - TARGET is missing but ~/.claude/skills/code-better/SKILL.md exists: ask me whether to upgrade that personal copy (then TARGET = ~/.claude/skills/code-better and skip step 6) or to install a repo copy here.
   - .claude/settings.json or ~/.claude/settings.json enables a plugin whose key starts with "code-better@": tell me that plugins update from their marketplace, and that a repo copy next to the plugin loads the skill twice. Stop unless I say to continue.
   - Nothing found: this is a fresh install.
2. Upgrades only: back up the old copy outside .claude/skills/ (a backup inside it loads as a second skill named code-better):
   b=".claude/code-better.backup-$(date -u +%Y%m%dT%H%M%SZ)"; cp -R .claude/skills/code-better "$b"; echo "$b"
   (For a personal copy, back up to ~/.claude/code-better.backup-<same stamp> instead.) Tell me the path.
   Keep a repo backup out of git right away: ex="$(git rev-parse --git-path info/exclude)"; mkdir -p "$(dirname "$ex")"; touch "$ex"; grep -qxF '.claude/code-better.backup-*/' "$ex" || echo '.claude/code-better.backup-*/' >> "$ex"
3. Write the six files into TARGET with the Write tool, replacing the old ones and creating directories as needed. Copy each file exactly: same characters, blank lines, and indentation. Do not reformat, fix, translate, or shorten anything. Keep any other file already in TARGET and list it in the step 8 report.
4. Check the copies. From TARGET, run:
   shasum -a 256 SKILL.md references/templates.md references/code-map.md references/review.md hooks/guard.py hooks/settings.json 2>/dev/null || sha256sum SKILL.md references/templates.md references/code-map.md references/review.md hooks/guard.py hooks/settings.json
   Every line must equal the matching line under "Checksums" below. For each mismatch, write that file again from its block and re-check. After two failed attempts on one file, stop and tell me which file.
5. Upgrades only: re-apply team edits. Run: diff -ru "$b" TARGET
   A "-" line whose rule appears in none of the six new files (grep TARGET for its key words) may be a team edit, especially one that names this repo's commands, paths, services, people, or policies. Text that 2.0.0 merely reworded is not a team edit. Show me the list, mark each item "re-apply" or "unsure", and ask me about the unsure ones; do not guess. Then fold each approved edit into TARGET/SKILL.md, in the section that now owns its topic:
   - "Pick the entry" is now "Scopes: pick the route".
   - Sections 1-5 keep their numbers. The old "6. Commit" is now "6. Hand-off: commands for the user"; commit-message and PR rules go there.
   - "Review" and "Subagents" merged into "Review and subagents"; the review fan-out moved to references/review.md.
   - "Rollback" is now a subsection under "Phase 2: Construction".
   Merge each rule into an existing bullet where it fits; otherwise add one line. If a team rule conflicts with a 2.0.0 rule, show me both and let me choose. Never edit hooks/guard.py or hooks/settings.json to re-apply an edit: list those edits for me instead.
6. Hooks (repo copy only). The hooks block is TARGET/hooks/settings.json.
   - No .claude/settings.json yet: copy TARGET/hooks/settings.json to .claude/settings.json.
   - .claude/settings.json already has a PreToolUse entry with matcher "Edit|Write|MultiEdit|NotebookEdit|Bash" and a Stop entry, both running .claude/skills/code-better/hooks/guard.py: change nothing.
   - Otherwise merge: append those two entries from TARGET/hooks/settings.json to the "hooks" PreToolUse and Stop arrays in .claude/settings.json, creating the keys if missing. Keep every other key and entry unchanged.
   Then run: python3 -m json.tool .claude/settings.json > /dev/null && echo settings-ok
7. Git hygiene, then verify.
   - ex="$(git rev-parse --git-path info/exclude)"; mkdir -p "$(dirname "$ex")"; touch "$ex"
   - If "$ex" already lists .claude/code-map.md (this repo keeps code-better's working files out of git), append whichever of these lines are missing: CLAUDE.local.md, .claude/code-map.md, .claude/plans/, .claude/state.md, .claude/audit.md
   Verify, showing each command with its output:
   - head -4 TARGET/SKILL.md (expect: name: code-better)
   - awk '/^description:/{print length($0)-13}' TARGET/SKILL.md (expect: 1024 or less)
   - grep -c "^## Phase" TARGET/SKILL.md (expect: 3)
   - wc -l TARGET/SKILL.md (expect: 246, plus any team lines from step 5)
   - the step 4 checksum command again (expect: every file matches, except SKILL.md if step 5 changed it)
   - echo '{}' | python3 TARGET/hooks/guard.py; echo "exit=$?" (expect: exit=0; the guard parses and stays idle outside a skill session)
   - git status --short (expect: only TARGET, .claude/settings.json, and the backup, unless they are excluded from git)
8. Report in 5 lines or fewer: fresh install or upgrade, team edits re-applied, conflicts or extra files left for me, verify results, and the backup path. Then print these commands for me to run, and do not run them yourself (leave out .claude/settings.json if step 6 changed nothing, and print no commands if the repo keeps the skill out of git):
   git add .claude/skills/code-better .claude/settings.json
   git commit -m "chore: upgrade code-better skill to 2.0.0"
   Use "chore: add code-better skill 2.0.0" for a fresh install. If step 5 re-applied a commit-message rule (for example a ticket-key prefix), write the message to follow it.
   Finally tell me to start a new Claude Code session so the new skill and hooks load, and to delete the backup after I have reviewed the diff.

What changes for our engineers (paste into the PR description):
- The gate line now names a scope: gate: pass - scope=<feature|bugfix|refactor|infra|security-patch|review|feedback|poc|done-check> tier=<sandbox|internal|prod> rung=<one-liner|micro|full|project> - <reason>.
- The agent stops for approval at checkpoints: questions that change the work, plan approval at full/project rung or in prod tier, and loopbacks that change an approved plan. Reply "Approve" or say what to change. "Just get it done" does not count as approval.
- Full/project work and all prod-tier work leave an append-only .claude/audit.md (operator, UTC time, and verbatim words for every scope override, answer, approval, change request, bypass, loopback, and hand-off) for compliance review.
- The agent never commits, pushes, merges, or deploys, even with permission. It ends with a hand-off block: secret-scan result, exact commit and PR commands, and a deploy runbook (deploy path, what to watch and the abort band, rollback command). You run them.
- Prod incidents: the agent hands you the rollback or flag-off command before it fixes forward.

=== FILES (generated by scripts/upgrade_prompt.py; do not edit by hand) ===
Checksums (shasum -a 256 output, run from TARGET):
3c43d8f907d6d6cd2060bd5ad45890754e4f114a1706448d14deefdf8bdfa9e1  SKILL.md
f7b7ff43eda2f661df0ee35456e2065a047a3eb06aeac55ff0af188b3365a47e  references/templates.md
8154c007072bad81221d9d9d3450096481d7230f531d6b1643ce8a732cfea20c  references/code-map.md
7f922ebab8eacee0984841b2d863a7c15026c055091caa69d4fdf3ffb78791f4  references/review.md
c7a33d05361cc827b4b40aa5d6cc4ee7c600d2477019316e7ad65f03f77b7c46  hooks/guard.py
9655af9fe7e7698b10289e18c566f869a3b4fac4f91de06393788d30096dbf1a  hooks/settings.json

=== BEGIN SKILL.md ===
---
name: code-better
description: Use when writing, changing, fixing, refactoring, or reviewing code or infra config in any repo - new features, bug fixes, failing tests or CI, broken deploys, prod incidents, security patches or CVE bumps, migrations, Terraform/Helm/K8s changes, code-review feedback, work that needs approvals or an audit trail, or before claiming work is done, committing, deploying, or opening a PR.
---

# Code Better

An adaptive, gated lifecycle for coding work in large existing codebases, in three phases. The **scope** picks which stages run, the **rung** picks how deep each one goes, the **tier** picks who must approve. User instructions (CLAUDE.md, direct requests) override this skill; a request to skip a gate counts once a line of the user's message starts with "bypass". The hand-off is fixed, bypass or not: a request to commit, merge, or deploy gets the commands, not the action.

```text
INCEPTION                          CONSTRUCTION         HAND-OFF
Gate -> Plan -> Teardown -> [approve] -> Build -> Verify -> Hand-off (commands for the user)
```

## Iron laws

1. **No edit before understanding.** Read the code the change touches. Trace the real flow end to end.
2. **No fix without root cause.** Symptom patches are a second bug.
3. **No logic without a failing check first.** Watch it fail, then make it pass.
4. **No irreversible step without a written rollback.** If you can't say how to undo it, you can't do it yet.
5. **No "done" without fresh evidence.** Evidence from this turn, not memory or a subagent's word.
6. **No code that doesn't need to exist.** The best code is the code never written.
7. **The user decides, you execute.** You propose the scope; the user can override it. Answers, approvals, and waivers come from a human message (or an approval already recorded in `audit.md`). Silence, urgency, or "just get it done" is not an approval. You change code; the user commits, merges, and deploys.

## Gate rule

Each stage exits with one line, in order: `map:` → `gate:` → (`debug:`) → `plan:` → `teardown/<round>:` → `build:` → `verify:` → `handoff:`. Format: `<stage>: pass|fail - <reason>`. A stage your scope or rung leaves out prints nothing; skipping one both require is a defect. A failed gate blocks the next stage. The only way past a red gate without fixing it is a user message (or a line of it) starting with "bypass"; then print `<stage>: bypass - <what was red>, waived by user: <why>`. Gates are fast checks, not ceremony: small work gets less process, never more. Print each line as plain text in exactly this form (or, if your output style forbids text between tool calls, as its own `echo "gate: pass - ..."` Bash call): the harness reads them.

## Harness (enforced by hooks)

Installed as a plugin, or with `hooks/guard.py` wired into settings, the gates are checked from your transcript and from the git working tree, so a file changed by Bash counts the same as one changed by Edit:

- The skill's record files (`.claude/` code map, plans, state, audit; `CLAUDE.local.md`) never count as changes. No other file change before `gate: pass`; at full/project rung, none before `plan: pass` and `teardown/readiness: pass` either. No ending the turn with files changed after the last `verify:` line.
- Backstops if a hand-off command slips through: no `git commit` before `verify: pass`, no force push, `git reset --hard`, `git clean -f`, `terraform destroy`, or `terraform apply` without a saved plan file.
- A block names what is missing: produce that. Never route around it with another tool, a rephrased command, or the off switch. A bypass line passes only after a user message starts with "bypass". Off switch: `CODE_BETTER_GUARD=off`. Decision log: `$(git rev-parse --git-path code-better)/harness.log`.

## Scopes: pick the route

Pick the scope from the request and name it in the `gate:` line. Torn between two → take the one with more stages. Stages not in the row are skipped and print nothing. Plan and Teardown run at the gate's rung: at one-liner, the plan is one chat line and there is no teardown. Every route that changes files ends at Hand-off, poc included.

| Scope | Triggers | Stages |
|---|---|---|
| feature | new behavior or change | Gate → Plan → Teardown → Build → Verify → Hand-off |
| bugfix | error, failing test, CI red, pod down, perf regression, incident | Gate → Debug → Plan → Teardown → Build (the fix) → Verify → Hand-off |
| refactor | restructure, no behavior change | Gate → Plan → Teardown → Build (Refactor rules) → Verify → Hand-off |
| infra | Terraform, Helm, K8s manifests, CI/CD config | as feature; the failing check is offline validation plus a plan or diff showing only the expected changes, 0 unexpected destroys; dry-run and rollback lines mandatory |
| security-patch | CVE, dependency bump, scanner finding | as feature; read the vendor changelog in Gate; tier internal or higher; Verify adds the repo's scanner |
| review | review a diff or PR | Gate → review fan-out (`references/review.md`) → report |
| feedback | received review comments | Gate → triage it (Receiving feedback) → Plan → Teardown → Build → Verify → Hand-off |
| poc | spike, prototype, throwaway | Gate (tier=sandbox, rung micro or lower) → Plan → Build → Verify by running it → Hand-off |
| done-check | "is it done?", ready to commit, open a PR, or deploy | Gate (rung one-liner, no map) → Verify → Hand-off (red Verify → bugfix) |

## Checkpoints: the user approves

Stop and end your turn at a checkpoint; continue only on a human reply. Checkpoints:

- **Questions** that change the work (Gate). **Plan approval:** after Teardown at full/project rung, and at any rung in prod tier. **Loopback** that changes an approved plan. **Incident rollback:** after giving the user the rollback command, until they confirm service is restored.

Show exactly this shape:

```text
**<Stage> complete:** <one-line result>. Review: <file path, or "above">.
Approve → <next stage> | Request changes → reply with what to change
```

For questions, the second line reads `Answer in <file> or in chat → <next stage>`. "Approve", or a clear equivalent, continues. Changes → revise, re-run the teardown round they touch, show the checkpoint again. One approval covers one plan; each later slice gets its own. User away → stop anyway, with the plan and state written. No trigger → keep going: small work gets no extra stops.

## Record: state and audit (full/project rung; prod tier adds the audit log)

Traceable without ceremony. All files sit under the repo-root `.claude/`; formats are in `references/templates.md`. Write them with Edit/Write.

- `plans/NN-<slice>.md`: plan, teardown results, verify table, drift, loopbacks; `plans/NN-<slice>-questions.md`: open questions with `[Answer]:` tags.
- `audit.md`: append-only, one block per human decision: scope overrides, answers, approvals, change requests, bypasses, loopbacks, hand-offs. Take the timestamp from `date -u +%Y-%m-%dT%H:%M:%SZ`; never invent one. Quote the human's words verbatim. Never edit or delete a past block.
- `state.md` (project rung): phase and stage checkboxes plus the resume point.

## Phase 1: Inception

### 1. Gate: workspace, requirements, scope

- **Resume:** `.claude/state.md` exists → read it first and resume at its `next:`.
- **Reverse-engineer the workspace:** read `.claude/code-map.md` (usually auto-loaded via `CLAUDE.local.md`). Missing, or `git diff --name-status <at>..HEAD` touches entry points, build/CI files, or top-level dirs → build or refresh it per `references/code-map.md` before the first change (a clearly one-line request may defer it); else `map: pass - fresh at <at>`. `graphify-out/` exists → query that instead. Greenfield (no source yet) → `map: pass - greenfield`. Orientation-only request → the map is the whole Gate, with no scope.
- **Local rules:** read the nearest CLAUDE.md / AGENTS.md / CONTRIBUTING and lint config for each subtree you touch, plus 1-2 sibling files. Copy their patterns (errors, logging, config loading, naming, test layout) even where you'd choose differently. Unfamiliar API, library, or version → read its docs or changelog first; never write against an API from memory.
- **Requirements:** turn the request into observable acceptance criteria and explicit non-goals. Rambling or self-correcting request → state the reading you're acting on in one line. Two requirements contradict → ask; never pick one silently.
- **Questions before assumptions:** an open question whose answer changes the work gets asked, never guessed. One → ask in chat with a recommended default. Two or more at full/project rung → write the questions file, stop at a checkpoint, and print `gate:` after the answers. Read every answer; a vague or contradicting answer gets one follow-up. Never re-ask an answered question. Answer doesn't change the work → state your default and proceed.
- **Blast radius** (before the first edit): grep every reference to what you change, as identifier AND string: callers, config/env keys, Helm values and templates, TF outputs and remote-state consumers, CI files, SQL, reflection/DI. Generated file (header says so, or a map danger zone) → change the source or generator and regenerate.

Then declare, as reply text before the first change (thinking is invisible to the guard): `gate: pass - scope=feature tier=internal rung=micro - one component, reversible`.

**Stakes tier** (by where the change ships, not where you edit it):

| Tier | Means | Adds |
|---|---|---|
| sandbox | never ships: spike, scratch, throwaway | nothing; rollback can be "discard the branch" |
| internal | ships to your own systems, CI, staging; additive public-surface change | the defaults in this skill |
| prod | runs in production, customer data, payments, auth/secrets, breaking public-surface change | plan approval, rollback + dry-run mandatory, review fan-out before done, deploy runbook in the hand-off, audit log; never store card data |

**Scope rung** (depth, by blast radius, not file count; pick the lower one when unsure):

| Rung | When | Plan | Teardown | Record |
|---|---|---|---|---|
| one-liner | 1 logical edit (+ its test), reversible, no open questions | the chat line | skip | none |
| micro | one component, reversible, additive-only public change, no schema change, no new dependency | 4 bullets | 2 rounds, self | none |
| full | crosses components, irreversible, new dependency, breaking public-surface or schema change, or a map hub/danger zone | plan file | 5 rounds, fresh subagent | plan, questions, audit |
| project | more than one slice, or spans sessions | plan per slice | 5 rounds per slice | + state file |

**Step-up rule:** when blast radius grows mid-work (new component, breaking public-surface change, new dependency, irreversible or prod touch), re-print `gate:` with the higher rung, then backfill its missing artifacts and re-print `plan:` and the teardown lines before continuing. Prod touches need user confirmation now. A rung never steps down mid-build. Prod tier is never a one-liner.

### 2. Plan

Existing pattern covers it → follow it, no alternatives. Real design choices → 2-3 approaches with trade-offs, simplest first, recommend one. Too big → split into shippable slices (units); plan the first.

Every plan, at any rung, names (the 4 bullets at micro):

- **Steps**: each with exact file, the change, and the check command that proves it. No placeholders ("TBD", "add error handling", "similar to above").
- **Reuse first**: existing code, stdlib, installed deps, or managed services that cover it. New code needs a one-line reason.
- **Rollback**: how to undo each destructive or irreversible step (see Rollback). "Fully reversible via `git revert`" is a valid line; a missing line is not.
- **Commit message draft**: `type: subject`.

Add when relevant:

- **Compat**: public-surface changes (API fields, CLI flags, env vars, config keys, Helm values, TF variables/outputs, event/DB schemas) are additive. Rename = add new, keep old working, mark deprecated. TF resource rename → `moved` block; plan must show 0 destroys.
- **Dry-run step** before any destructive action, with its own check. **Rerun-safe**: jobs, migrations, and data scripts pass when run twice; name the idempotency mechanism.
- **Budget line** for anything over ~2 minutes of wall time: expected duration, cost, completion signal. **Metric band** for nondeterministic checks: `p95 < 200ms`, `F1 >= 0.82, seed 42`, not a bare boolean.
- **Kill-switch** for anything that runs unsupervised (bots, cron, daemons, autoscalers): the decision policy is config, and the off switch exists before the code. **Deploy runbook** (when it will ship), for the user to run: the repo's deploy path, the abort signal with its band, the watch window, and the rollback command.

Full rung and up: write the plan to `.claude/plans/NN-<slice>.md`, `NN` = next free two-digit number. Below that, keep it in chat. Exit: `plan: pass - 4 steps, rollback: git revert`.

### 3. Teardown: cold review before code

Review the plan before any code exists. Fixing a spec is cheap; fixing shipped code is not. The reviewer's posture is **refute, don't confirm**. Read it **cold**: the plan and its linked sources only, no conversation memory, no "you know what I meant". A look-alike precedent that answers a different question does not pass.

- **micro (2 rounds, self):** 1. consequence: if we build exactly this, where does it break? 2. alternatives: what else solves it, and is this the strongest option?
- **full+ (5 rounds, fresh subagent given only the plan file and linked sources):** 1. zoom-out: does the shape hang together? 2. comprehension: could a stranger follow it? 3. critique: trade-offs, edge cases, weakest point. 4. fit: does it still fit the codebase after the critique? 5. readiness: concrete enough to build from?

One line per round: `teardown/critique: fail - no rollback for column drop`. On a fail, fix the plan, not code, and re-run that round once. The same round failing twice → stop and ask the user for a direction change. The last round passes at full/project rung or in prod tier → plan approval checkpoint.

## Phase 2: Construction

### 4. Build

**Lazy ladder**, stop at the first rung that holds: 1. Does it need to exist? Speculative → skip it, say so in one line. 2. Already in this codebase? Reuse it. 3. Stdlib does it? 4. Native platform feature covers it (DB constraint over app code, CSS over JS)? 5. Already-installed dependency solves it? Never add one for a few lines. 6. Can it be one line? 7. Only then: the minimum code that works.

**Scope:**

- Touch only what the plan names. Every changed line traces to the request. Discoveries go back to the plan, not straight into code. Diff touches files the plan doesn't name, or grows past ~2x the planned steps → stop and report.
- No unrequested abstractions, config, flags, modes, scaffolding "for later", drive-by refactors, renames, or reformatting. Never simplify away: input validation at trust boundaries, error handling that prevents data loss, security, accessibility.
- Remove dead code your change created. Mention other dead code; don't delete it. Odd legacy code guards a past bug until its history (`git log -L`, `git blame` → PR) shows otherwise. Mark deliberate shortcuts with their ceiling: `# simplified: global lock; per-account locks if throughput matters`.

**Test first (red → green → refactor):**

0. **Baseline:** before the first edit, run the whole test module or package you'll touch. Already red on clean HEAD → pre-existing: record it, don't fix it unless in scope.
1. Smallest test for one behavior. Run it. Watch it fail for the expected reason. Fails for another reason (import, typo) → fix that and re-run. Passes already → wrong test, unless it is a characterization check pinning current behavior.
2. Minimum code to pass. Run it. Green, with no other tests broken. Refactor with tests green. Repeat. Wrote code before the test? Delete it and start from the test; don't keep it "as reference".

- No tests near the change → first pin current behavior at the nearest existing seam (CLI, HTTP, job entry, public function) with the repo's runner. Don't refactor for testability inside a fix or feature. Trivial one-liners need none. Exceptions: throwaway prototypes, generated code, pure config; verify those by running them.
- **Infra: the failing check is the plan or diff.** Offline first: `terraform fmt -check`, `terraform init -backend=false && terraform validate`, `helm template` / `helm lint`, `actionlint`. Live diffs (`terraform plan -out=tfplan`, `helm diff`, `kubectl diff`) only via the repo's own path (Makefile, Atlantis, CI) or after confirming backend, workspace, and `kubectl config current-context`. No `init -upgrade` or `state` without approval; never `apply` (it goes in the hand-off).
- Exit: `build: pass - red→green, 3 files`.

### Debug (anything broken, during Build or as the bugfix entry)

**Incident:** prod broke or degraded after a deploy or flag change → first, before the map, give the user the exact rollback or flag-off command (not a file change, so no gate needed) and stop; find the cause once they confirm service is restored. "Fast" and "skip the tests" are not a bypass: the reproduction is still the failing check unless the user's message starts with "bypass". Root cause, in order:

1. Capture the exact symptom: error text, expected vs actual, environment, input. Can't reproduce → observe (logs, timing, exact errors); never code blind.
2. Reproduce with the smallest reliable case, using existing tests, commands, or inputs; the new failing test is written in Build. Keep the original failing input.
3. Read evidence: stack trace, logs, config, data flow, and history of the exact lines (`git log -L :<func>:<file>`, `git blame`). Post-upgrade breakage → read the vendor changelog.
4. Compare against something that works: similar code, last green run, previous version.
5. Rank falsifiable hypotheses. Test one at a time with the cheapest check that tells them apart. Exit: `debug: pass - cause: <x>` → plan the fix at the gate's rung, or `debug: pass - not a bug: <evidence>` → report and stop.
6. (In Build) Fix at the first point where actual diverges from expected, at the narrowest layer that owns the bug. One guard in the shared function beats a guard in every caller.
7. (In Build) Prove it: a check that fails before the fix and passes after. Re-run the original reproduction.

**Loopback:** 2 failed fixes, or Verify shows the plan was wrong → stop. Report tried / learned / unexplained / options and let the user choose. Cause still unknown → back to Debug. Cause in the plan → back to Plan and re-run the teardown; an approved plan needs approval again. Cause in the requirements → back to Gate. Record each loopback in the plan (in chat at micro) and in the audit log when one is kept. A third fix of the same shape is banned.

Infra triage, failing layer outward: **K8s:** `kubectl describe` (events, probes, OOMKilled, image pull) → `kubectl logs --previous` → `kubectl get events --sort-by=.lastTimestamp` → node pressure. **CI:** first failing step; diff against last green run (deps, runner image, secrets, cache). **Terraform/Helm:** plan/diff vs live state, drift, provider/chart versions. **Network:** DNS → TCP → TLS → HTTP (`dig`, `nc -vz`, `openssl s_client`, `curl -v`). **Performance:** baseline first, same load, before changing anything.

Never: delete or weaken tests, suppress errors, add sleeps or silent fallbacks, claim a cause without evidence, or hand off a prod fix without an understood cause and a rollback command (handing off a rollback to the last good version is the exception).

### Refactor

Tests green before the first move; no coverage → add characterization checks first. No behavior changes mixed in. One move at a time, green between moves. Preserve interfaces, errors, and ordering.

### Rollback (applies at every stage)

Before any destructive or irreversible step, have the undo ready and tested where possible, and name the abort signal (error rate, failed health check, mismatched counts). Prod restarts, rollbacks, and data fixes are the user's to run: give the exact command.

- **Code:** changes stay uncommitted in the working tree (or a gitignored `git worktree`). Shared history → hand the user `git revert <sha>`, never `reset --hard` or force-push.
- **Infra:** `terraform plan -out=tfplan`; the user applies exactly that plan. Know the previous state version. `helm rollback <release> <rev>`. `kubectl rollout undo deploy/<name>`.
- **Data/schema:** new migration via the repo's tool; never edit an applied one. Backup or snapshot first (the user runs it), then a down-migration, or expand → migrate → contract so old and new code both run mid-deploy. Verify row counts and checksums on both sides.
- **Flags:** risky new prod-tier behavior (not a bugfix) ships behind the repo's existing flag or config mechanism, default off; none exists → ask before adding one. This is the one flag Build's Scope rules allow; the plan names its removal step.

### 5. Verify

Before any "done / fixed / passing" claim:

1. Name the command that proves each acceptance criterion. Run it fresh: targeted tests while building; before claiming done, the affected package's suite plus the repo's CI checks for changed paths (lint, format, typecheck, `terraform validate`, `helm lint`, codegen drift; read them from the CI config). Whole-repo suite only if cheap. Check tool missing → run it isolated (`uvx`, `npx`, `go run`) at the version the repo pins (pre-commit config, lockfile), or report it as not run; never install into the project's env without asking.
2. Read all output: exit code, failure count, warnings, skipped tests (skipped = not passed). Red that matches the baseline → pre-existing, report it. Flaky → report both results; never rerun until green.
3. Classify evidence: **terminal** (run this turn), **user-attested** (labeled, never simulated), **integrity** (counts, checksums, dry-run vs live: exit 0 with wrong numbers = FAIL), **metric** (observed value against its band). Near-miss is a fail: `0.819 vs 0.82` goes to the user, not rounded up.
4. **Drift:** compare the plan against what was built. List divergences only, or "no drift".
5. Full rung and up, or prod tier → run the review fan-out (`references/review.md`) on the diff before claiming done.

Report compactly: `verify: pass - 9/9 (7 terminal, 1 integrity, 1 metric in band); 1 pre-existing red; no drift`. Show failures in full. Subagent says done → check its diff yourself. Acceptance and CI checks pass → stop. No polish, extra tests, or cleanup.

## Phase 3: Hand-off

### 6. Hand-off: commands for the user

Your work ends with the changes in the working tree and `verify: pass`. Never run `git add`, `git commit`, `git push`, PR create or merge, deploys, `terraform apply`, `helm upgrade|rollback`, `kubectl apply|rollout`, prod restarts, or data fixes, even when your permissions allow them or the user says "ship it". Print them for the user instead. Never offer to run them (no "say so and I'll do it"), and a repeated request gets the same commands:

- **Secret scan** the working-tree diff (`git diff`, plus new untracked files) for keys, tokens, passwords, connection strings, `.env` files. A hit blocks the hand-off until the secret is moved out and, if it ever left the machine, revoked.
- **Commit:** on the default branch → `git switch -c <branch>` first. Then `git add <exact files>` (never `-A`), and `git commit -m "<type: subject>" -m "<why>"` in the repo's convention. One logical change per commit. The repo's changelog entry is part of the change, made in Build.
- **PR**, if the repo uses them: `git push -u origin <branch>` and the repo's PR command or URL, with the acceptance criteria as the description.
- **Deploy runbook**, when it ships: the repo's deploy path (pipeline, Makefile, Atlantis, Argo CD/Flux; never one that skips CI), the command to watch the abort signal against its band for the window, and the rollback command for when it is out of band.

Exit: `handoff: pass - commit commands for 3 files, deploy runbook`. Record the hand-off in the audit log when one is kept. The user reports back "deployed" or "out of band" → the latter is a new bugfix run.

## Review and subagents

**Receiving feedback:** read all of it first; ask about unclear items before implementing any. Verify each claim against the code; reviewers can be wrong. Push back with technical reasons when a suggestion breaks behavior, adds unused features, or conflicts with the user's decisions. No performative agreement. Order: blocking → simple → complex; test each. **Requesting review:** micro and below → self-review the diff. Full rung and up, prod tier, or a PR → review fan-out per `references/review.md`.

**Subagents** are for an independent read (no shared context) or parallel work with no shared state; ≤3 tool calls → do it yourself. Brief like a peer: goal, scope, constraints, what's ruled out, output format. Reviewers get the requirements and the diff, never your conclusions. Workers edit only their assigned files: no git, no plan edits, no gate lines. The orchestrator merges their edits, verifies, and hands off.

## Learnings

The user corrects you in a way that applies again (a convention, a banned pattern, a command) → ask once, before Verify: "Keep that for next time? project / personal / no". Project → a one-line addition to the nearest CLAUDE.md; add it to the plan and verify it with the rest. Personal → append it to `CLAUDE.local.md`. No answer → save nothing.

## Files this skill writes

Under the repo-root `.claude/`: `code-map.md`, `plans/` (plans and questions files), `audit.md`, `state.md`; plus one `@.claude/code-map.md` line in `CLAUDE.local.md`. Keep them out of git unless the user wants them shared (an audit trail for compliance usually is): append each to `$(git rev-parse --git-path info/exclude)` (works in worktrees; `mkdir -p` its dir first; skip lines already there).

## Output

Answer first. Code over prose; changed lines plus context, not whole files. One line per gate result. Final report ≤5 lines: what changed, how verified (command → result), skipped and when to add it, blockers. Persisted artifacts (comments, commits, PRs, docs, audit entries) use normal prose.

## Red flags: stop and go back

| Thought | Reality |
|---|---|
| "Too simple to need a test / a plan" | Pick the one-liner rung. It still has a check. |
| "They said just get it done, so it's approved" | Urgency is not approval. Show the checkpoint and stop. |
| "Rollback is obvious" / "cleaner to rename it" | Write the undo line. Someone you can't see reads the old name: add, deprecate. |
| "Quick fix now, investigate later" | Later never comes. Find the cause, or hand off the rollback first. |
| "Should work now" / "close enough" | Run it. A near-miss is a fail. |
| "I have permission to commit / merge / deploy, so I'll do it" / "say so and I'll run them" | Permission is not a request, and the offer is the same breach. Hand off the commands, nothing more. |
| "I'll add it now, we'll need it" / "while I'm here" | YAGNI. Out of scope: mention it, don't do it. |
| "One more fix attempt" (after 2) | Loopback. Report and let the user choose. |
| "The reviewer / subagent says it's fine" | Verify against the code and the diff. |
| "The hook is wrong, I'll do it via Bash" / "set `CODE_BETTER_GUARD=off`" | Produce the missing stage line, or ask the user to bypass. The off switch is the user's. |
=== END SKILL.md ===

=== BEGIN references/templates.md ===
# Templates

Load only when the rung or tier calls for a file. Delete sections that don't apply. All files live under the repo-root `.claude/` (`mkdir -p .claude/plans`), are written with Edit/Write, and stay out of git per SKILL.md "Files this skill writes".

## Plan file (full rung and up)

Path: `.claude/plans/NN-<slice>.md`.

```markdown
# Plan: <one-line goal>

gate: pass - scope=<feature|bugfix|refactor|infra|security-patch|feedback> tier=<sandbox|internal|prod> rung=<full|project> - <reason>

## Goal and acceptance
- [ ] <observable check, verifiable without reading source>
Non-goals:

## Decisions
- <choice> - <why> (<who approved>)

## Reuse
- <existing code / lib / service> - <covers what>

## Steps
1. File: <path> / Change: <what> / Check: `<command>` → <expected>
2. ...

## Rollback
- Step N: <undo command> / abort if <signal>
- Dry run: `<command>` → <expected>

## Budget / metric bands / kill-switch (if relevant)

## Deploy runbook (if it will ship; the user runs it)
- Deploy path: <repo pipeline, Makefile target, Atlantis, Argo CD/Flux>
- Watch: `<command or dashboard query>` - abort if <metric> outside <band> within <window>
- Rollback: `<command>`

## Teardown (copies of the lines printed in chat; the guard reads chat, not this file)
- teardown/zoom-out: pass|fail - <reason>
- teardown/comprehension:
- teardown/critique:
- teardown/fit:
- teardown/readiness:

## Approval
- <PLAN_APPROVED timestamp> - see `.claude/audit.md`

## Commit draft
<type>: <subject>

## Verify (filled after build)
| Criterion | Command | Evidence class | Result |
|---|---|---|---|

Drift: <divergences, or "no drift">

## Loopbacks
- <ISO timestamp> from <stage> to <Debug|Plan|Gate> - cause: <x> - re-approved: <yes/no/n.a.>
```

## Questions file (full/project rung, 2+ open questions)

Path: `.claude/plans/NN-<slice>-questions.md`. Ask only questions whose answer changes the work. Each question gets one line of context, lettered options with the recommended one marked, and a final `X. Other (please specify)`. Multi-select answers list letters: `[Answer]: A, C`.

```markdown
# Questions: <slice>

Fill in each `[Answer]:` line with a letter (or several, comma-separated), or with X and your own text. Reply in chat when done.

## Q1. Where should rate limits be enforced?
Context: this decides whether the change touches the gateway config or the service code.

A. API gateway, per client key (recommended)
B. In the service middleware, per user
C. Both, gateway as a coarse cap
X. Other (please specify)

[Answer]:
```

## Audit log (full/project rung, or prod tier)

Path: `.claude/audit.md`. Append-only: one block per human decision, never edit or delete a past block. Take the timestamp from `date -u +%Y-%m-%dT%H:%M:%SZ`; never invent one. Quote the human's words verbatim. `by:` is the operator from `git config user.name`; the log records who was at the keyboard, not a verified identity. Events: `SCOPE_OVERRIDDEN`, `QUESTIONS_ANSWERED`, `PLAN_APPROVED`, `CHANGES_REQUESTED`, `BYPASS_GRANTED`, `LOOPBACK`, `HANDED_OFF`.

```markdown
## 2026-11-08T14:02:11Z QUESTIONS_ANSWERED
- slice: 01-rate-limits
- by: Jane Doe
- human: "Q1: A, and keep the old header for one release."
- context: answers recorded in plans/01-rate-limits-questions.md

---

## 2026-11-08T14:31:47Z PLAN_APPROVED
- slice: 01-rate-limits
- by: Jane Doe
- human: "Approve"
- context: plan after teardown round 5, gateway-only enforcement

---
```

## Session state (project rung)

Path: `.claude/state.md`. The Gate reads it first when resuming and continues at `next:`. Markers: `[ ]` pending, `[-]` in progress, `[?]` awaiting approval, `[x]` done, `[S]` skipped (give the reason). Append one `## Log` line per stage exit.

```markdown
# State: <project>
scope: <scope> | tier: <tier> | rung: project | started: <YYYY-MM-DD>

## Phase progress
### Inception
- [x] gate
- [x] plan/01-<slice>
- [?] teardown/01-<slice> - awaiting plan approval
### Construction
- [ ] build
- [ ] verify
### Hand-off
- [ ] handoff - commit commands and deploy runbook printed for the user

## Resume point
next: build - step 1 of plans/01-<slice>.md, after approval

## Log
- <date> plan/01-auth: pass - 6 steps | next: teardown
- <date> teardown/critique: fail - no rollback for column drop | next: add backup step
- <date> verify: bypass - integrity red, row count off by 3, waived by user: known soft-deletes
```
=== END references/templates.md ===

=== BEGIN references/code-map.md ===
# Code map

A small, hand-checked map of an existing repo so every session starts oriented without re-exploring. Read this file only when the Gate says to build or refresh the map.

## When

- **Build:** no `.claude/code-map.md` in the repo and the task touches existing code.
- **Refresh:** `git diff --name-status <at>..HEAD` adds, deletes, or renames top-level dirs or entry points, touches the files `Commands` came from (Makefile, scripts, CI config), or changes more than ~20% of files. Otherwise the map is fresh: print `map: pass - fresh at <at>`. Refresh only the changed sections, then bump `at`.
- **Skip:** `graphify-out/` exists (query it instead), or the repo is under ~20 files (just read it).

## Build (≤10 tool calls; delegate to an Explore subagent if the repo has more than ~300 tracked files)

Monorepo, or more than ~2000 tracked files → map the root layout plus only the package or subtree the task touches; add a section per subtree as later tasks reach it.

Gather, using tracked files only:

```bash
git ls-files | awk -F/ 'NF>1{print $1}' | sort | uniq -c | sort -rn | head -25            # top-level dirs by size
git ls-files | sed -n 's/.*\.\([a-z0-9]*\)$/\1/p' | sort | uniq -c | sort -rn | head -8   # languages
git log --since=6.months --max-count=2000 --name-only --format= | grep . | sort | uniq -c | sort -rn | while read n f; do test -e "$f" && echo "$n $f"; done | head -15  # hot files that still exist
git ls-files | grep -iE '(^|/)(main|app|server|index|cli|manage|wsgi|asgi)\.(py|[jt]sx?|go|rb|rs|java|php)$|^cmd/|Dockerfile|docker-compose|Makefile|Justfile|package\.json|pyproject\.toml|go\.mod|Cargo\.toml|\.github/workflows/|\.gitlab-ci\.yml|Jenkinsfile|Chart\.yaml|kustomization\.ya?ml|(^|/)(main|versions)\.tf$' | awk -F/ '{print NF"\t"$0}' | sort -n | cut -f2- | head -40  # shallowest first
```

Then read only: the build/task file (Makefile, `package.json` scripts, `pyproject.toml`), the PR CI workflow(s) (record the required checks), the README's setup section, and each entry point's first ~40 lines. Hubs = the hot-files list, plus the few modules that `git grep -c` shows imported by many files. Trace one main request or job path from entry to storage.

Never record secrets, credentials, hostnames from `.env`, or customer data.

## Write

`mkdir -p .claude`, then write `.claude/code-map.md` in this shape, ≤80 lines, facts only. Every path is repo-relative from the root and tracked. Name symbols (`Session.send`), never line numbers: they rot on the next commit. A command not read from a real file gets `(unverified)`.

```markdown
# Code map
at: <short sha> · <date> · refresh: code-better Gate

## Stack
<languages, frameworks, runtime versions, package manager>

## Commands
build: `...` · test: `...` · single test: `...` · lint: `...` · run: `...` · CI required checks: `...`

## Layout
- `dir/` - <purpose, one line>

## Entry points
- `path` - <what starts here>

## Main flows
- <request/job>: `entry` → `handler` → `service` → `store`

## Hubs (most imported / most changed)
- `path` - <why it matters; who calls it>

## Conventions
<test location and naming, error handling, config and secrets loading, logging>

## Danger zones
- `path` - <migrations, payments, auth, generated code (do not edit), vendored code, prod config>

## Infra
<IaC / Helm / K8s / CI paths and what they deploy>
```

## Wire it in

Claude Code loads `CLAUDE.md` and `CLAUDE.local.md` at session start, and expands `@path` imports in them eagerly. So one import line makes the map load in every session.

- **Personal (default, for shared or legacy repos):** add the line `@.claude/code-map.md` (plain text, not in a code span) to the repo-root `CLAUDE.local.md`. Keep the skill's files out of git without touching the team's `.gitignore`:

```bash
ex="$(git rev-parse --git-path info/exclude)"; mkdir -p "$(dirname "$ex")"; touch "$ex"
for p in CLAUDE.local.md .claude/code-map.md .claude/plans/ .claude/state.md .claude/audit.md; do grep -qxF "$p" "$ex" || echo "$p" >> "$ex"; done
```

- **Team (only if the user says so):** remove the skill's lines from `$(git rev-parse --git-path info/exclude)` and the import from `CLAUDE.local.md`, then put the import line in `CLAUDE.md`, and hand the user the commit command for the map and that line.

Don't ask: default to personal and say in one line how to switch to team.

## Verify

- Every path in the map exists: `test -e <path>` from the repo root for each.
- Every command was read from a real file (Makefile, scripts, CI), not guessed. Unverified commands get `(unverified)`.
- `git status --short` shows none of the skill's files when personal.

Exit: `map: pass - built at <sha>, 52 lines, personal`.
=== END references/code-map.md ===

=== BEGIN references/review.md ===
# Review fan-out

Load at full rung and up, in prod tier, for a PR, or in the review scope (SKILL.md "Review and subagents" and Verify step 5).
Micro and below: self-review the diff instead; this file is not needed.

**Model by job:** cheapest for triage and file lookups; mid for summaries and rule checks; strongest for the bug and defect lenses and for validation.

1. **Triage** (cheap; skip for a diff you just wrote): stop if the change is trivial, already reviewed, or not ready. Prod tier is never trivial.
2. **Scope the rules:** list the CLAUDE.md files at the root and in parent dirs of changed files. A rule only applies to files under it.
3. **Parallel reviewers**, one lens each: rule compliance (quote the rule), bugs visible in the diff alone, defects in the introduced code (logic, security, compat). Prod tier: two reviewers per lens, and the defect lens may read outside the diff to check rollback, rerun-safety, auth, and locking.
4. **High signal only:** won't compile or parse, wrong for every input, or an in-scope rule clearly broken. Never flag: style, pre-existing issues, linter-catchable issues, nitpicks, rules silenced in code, or input-dependent maybes (prod tier: flag them if a concrete input breaks it).
5. **Validate** each finding with a separate subagent given only the finding and the code. Not confirmed → drop it.
6. **Report** confirmed findings, one per issue, with `file:line`. None → "No issues found." Post to a PR only when asked.
=== END references/review.md ===

=== BEGIN hooks/guard.py ===
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
                         `terraform|tofu|terragrunt apply` without a saved plan file, and
                         `destroy` (added with the 2.0.0 Hand-off: a review reproduced it passing): no rollback.

Bypass: a stage printed as `<stage>: bypass - <what was red>, waived by user: <why>` counts as pass only when a line of a
human message in this session (or the message that loaded the skill) starts with "bypass".
G5 has no bypass since 2.0.0: under the Hand-off rule the user runs those commands.
Kill-switch: CODE_BETTER_GUARD=off disables every check.
State and decision log live in `$(git rev-parse --git-path code-better)/`: never
committed, nothing to gitignore. Outside git, it falls back to Edit/Write tool calls.

Known gaps (accepted; the skill's hand-off rule covers them): `git checkout -- .` and
`git restore` stay allowed so a block can never deadlock; changes inside submodules and
tracked `.claude/` config are not sensed; commands are matched by regex, not a shell parser;
a `rung=` inside backticks in the gate line is not read (the block message asks for it);
outside git, an Edit the guard refused can still cost one G4 at Stop.

Stdlib only. Any internal error fails open (allow) and prints to stderr, so a guard
bug never bricks a session.
"""
import datetime
import glob
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
STAGE = re.compile(r"\b(gate|plan|verify|teardown/[a-z-]+)\**\s*:\s*\**\s*(pass|fail|bypass)\b[`*]*([^\n`]*)", re.I)
REMINDER = re.compile(r"<(system-reminder|local-command-stdout)>.*?</\1>", re.S)
RUNG = re.compile(r"\brung=([a-z-]+)", re.I)
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
EXEMPT = re.compile(r"^(CLAUDE\.local\.md|\.claude/(code-map\.md|state\.md|audit\.md|plans/.*))$")

GIT_COMMIT = re.compile(r"\bgit\b(\s+(-[Cc]\s+\S+|--\S+))*\s+commit\b")
FORCE_PUSH = re.compile(r"\bgit\b.*\bpush\b.*(\s--force(?!-with-lease|-if-includes)\b|\s-[A-Za-z]*f[A-Za-z]*\b|\s\+[^\s+])")
RESET_HARD = re.compile(r"\bgit\b.*\breset\b.*\s--hard\b")
CLEAN_FORCE = re.compile(r"\bgit\b.*\bclean\b.*(\s-[A-Za-z]*f|\s--force\b)")
TF_DESTROY = re.compile(r"\b(terraform|tofu|terragrunt)\b(\s+-chdir=\S+)?(\s+run-all|\s+run\s+--all)?\s+destroy\b")
TF_APPLY = re.compile(r"\b(terraform|tofu|terragrunt)\b(\s+-chdir=\S+)?(\s+run-all|\s+run\s+--all)?\s+apply\b(?P<args>.*)")
RETRY_SLEEP = 0.4  # seconds between transcript re-reads before a stage-line deny
TF_VALUE_FLAGS = {"-var", "-var-file", "-target", "-replace", "-parallelism", "-lock-timeout", "-state", "-state-out", "-backup"}


# ---------- sensor 1: transcript ----------

def read_events(transcript_path):
    """(events after the last code-better load, line number of that load), or None.

    ponytail: reads the whole transcript on every call; fine to tens of MB.
    Track a byte offset per session if hook latency ever shows up.
    """
    events, load, last_human = [], None, None
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
                        events, load = ([last_human] if last_human else []), n  # the message that asked for it counts
                    elif text and not entry.get("isMeta"):
                        last_human = ("human", bool(USER_BYPASS.search(TAG.sub("\n", REMINDER.sub("", text)))))
                        events.append(last_human)
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


def pid_alive(pid):
    try:
        os.kill(int(pid), 0)
    except (ValueError, ProcessLookupError):
        return False
    except OSError:  # e.g. PermissionError: exists, owned by someone else
        return True
    return True


def fingerprint(root, state_dir):
    """Tree hash of the whole working tree (tracked + untracked, minus .gitignore'd files
    and UNSENSED paths), built in a temp index so the real index is never touched.

    ponytail: writes blobs for changed files into .git/objects (git gc prunes them);
    a huge non-ignored untracked file gets hashed on every call.
    """
    tmp = os.path.join(state_dir, "index.%d" % os.getpid())
    for old in glob.glob(os.path.join(state_dir, "index.*")):  # left by a hook killed at its timeout
        m = re.match(r"index\.(\d+)$", os.path.basename(old))  # never git's index.<pid>.lock
        if m and not pid_alive(m.group(1)):  # not mtime: copy2 keeps the real index's old one
            try:
                os.remove(old)
            except OSError:
                pass
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
            return ("G1", "a `rung=` in your `gate:` line, e.g. `gate: pass - scope=feature tier=internal rung=micro - <reason>`")
        if g < 0:
            return ("G1", "a `gate:` line, and none is in your visible replies since the skill loaded "
                          "(the guard cannot see thinking). Write it as plain text before your next tool call, or, "
                          "if your output style forbids text between tool calls, run it as its own Bash call: "
                          "echo \"gate: pass - scope=<feature|bugfix|...> tier=<sandbox|internal|prod> rung=<one-liner|micro|full|project> - <reason>\" "
                          "(SKILL.md section 1)")
        level = rung.group(1).lower() if rung else None
        if level in ("full", "project"):
            p = self.passed("plan", g)
            if p < 0:
                return ("G2", "the plan file and `plan: pass - ...` (rung=%s, SKILL.md section 2)" % level)
            if self.passed("teardown/readiness", p) < 0:
                return ("G2", "the 5 teardown rounds ending with `teardown/readiness: pass - ...` "
                              "(rung=%s, SKILL.md section 3)" % level)
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
    # No git: only Edit/Write calls are seen, and refused ones are in the transcript too.
    # Since the last `verify:` line, so a loopback to Gate doesn't re-blame verified Build work.
    v = st.last("stage", "verify")
    if not any(e[:2] == ("stage", "gate") for e in st.events[:max(v, 0)]):
        v = -1  # a verify line before any gate hides nothing
    changed = st.changed_since(v) if st.tree is not None else []
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
        (FORCE_PUSH.search, "force push rewrites shared history; hand the user `git revert <sha>` instead"),
        (RESET_HARD.search, "`git reset --hard` destroys uncommitted work; use `git stash` or `git revert`"),
        (CLEAN_FORCE.search, "`git clean -f` deletes untracked files with no undo; list them with `git clean -n` and ask"),
        (lambda s: TF_DESTROY.search(unquoted(s)), "`terraform destroy` deletes live infrastructure; hand the user `terraform plan -destroy -out=tfplan` and `terraform apply tfplan`"),
        (tf_apply_without_plan, "apply only a saved plan, and only the user applies: hand off `terraform plan -out=tfplan` and `terraform apply tfplan`"),
    )
    for test, why in risky:
        if any(test(s) for s in segments):  # no bypass: the user runs these (SKILL.md section 6)
            return ("G5", "code-better: blocked irreversible command: %s (SKILL.md Rollback). "
                    "Print it for the user to run (SKILL.md section 6, Hand-off)." % why)
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
                    "and print `verify: pass - <n>/<n> ...`. Commits are the user's: hand off the commands (SKILL.md section 6)." % ", ".join(changed[:8]))
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
    state_dir = git(root, "rev-parse", "--git-path", "code-better")  # no --path-format: git < 2.31 lacks it
    state_dir = state_dir and os.path.join(root, state_dir)  # relative to root, or already absolute
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
=== END hooks/guard.py ===

=== BEGIN hooks/settings.json ===
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit|NotebookEdit|Bash",
        "hooks": [
          {
            "type": "command",
            "command": "f=\"$CLAUDE_PROJECT_DIR/.claude/skills/code-better/hooks/guard.py\"; [ -f \"$f\" ] && exec python3 \"$f\"; exit 0",
            "timeout": 10
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "f=\"$CLAUDE_PROJECT_DIR/.claude/skills/code-better/hooks/guard.py\"; [ -f \"$f\" ] && exec python3 \"$f\"; exit 0",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
=== END hooks/settings.json ===
`````

</details>

## [1.0.0] - 2026-11-06

code-better is now an agent harness: the stage gates are enforced by hooks, not just written down.

### Added

- `skills/code-better/hooks/guard.py`: one stdlib-only Python hook for PreToolUse (Edit, Write, MultiEdit, NotebookEdit, Bash) and Stop. It reads two sensors. The session transcript shows which stage lines were printed. A git working-tree fingerprint, built in a temp index, catches files changed by any tool, Bash included. It is armed only after the skill loads in a session. Controls, each tied to the incident it exists for:
  - G1: no file change before `gate: pass`.
  - G2: at full/project rung, no change before `plan: pass` and `teardown/readiness: pass`.
  - G3: no `git commit` with files changed after the last `verify: pass`.
  - G4: no ending the turn with files changed after the last `verify:` line.
  - G5: no force push, `git reset --hard`, `git clean -f`, or `terraform|tofu apply` without a saved plan.
- Bypass: a `<stage>: bypass` line, or a G5 command, passes only after a human message in the session says "bypass". Kill-switch: `CODE_BETTER_GUARD=off`.
- Decision log, one JSON line per armed hook call, at `$(git rev-parse --git-path code-better)/harness.log`. It lives inside `.git`, so there is nothing to gitignore.
- Plugin packaging: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, and `hooks/hooks.json`. Install with `claude plugin install code-better --marketplace neeltom92/code-better`. Teams and orgs can require it with `extraKnownMarketplaces` + `enabledPlugins`.
- `skills/code-better/hooks/settings.json`: the hooks block for per-repo copy installs with no marketplace access.
- `tests/test_guard.py`: two-sided tests, so every rule both fires and stays quiet; 59 cases, stdlib `unittest`. CI runs them, plus the skill checks, in `.github/workflows/ci.yml`.
- This changelog.

### Changed

- SKILL.md: new "Harness (enforced by hooks)" section. Stage lines must be plain text in the exact `<stage>: pass|fail - <reason>` form. Added a red flag against routing around a block. Compressed a few one-line paragraphs to stay at 250 lines.
- README: install paths for plugin, team repo, org-managed, per-repo copy, and skill-only; plus harness operations.

### Fixed during live testing (before release)

- Live runs showed the agent editing through a Bash heredoc before printing `gate:`. Edit-tool tracking alone missed this, so the git sensor was added.
- Other plugins' state under `.claude/` (e.g. autoharness) no longer counts as a change.
- A temp index copied with a fresh mtime hid same-second, same-size edits. Fixed by preserving the mtime (git racy-clean check).
- A stage line printed in the same message as the tool call can land in the transcript after the hook runs. The guard now re-reads before denying, and Stop reads `last_assistant_message`. A `gate:` line that appears only in the final message does not count.
- Read-only and revert commands (`cat`, `grep`, `git status|diff|restore|checkout|stash`, ...) are always allowed, so a G1 block cannot deadlock the session.
- Stage lines are matched case-insensitively and tolerate `**bold**` or backticks. `<system-reminder>` text never counts as a user bypass.
- From an independent review, before release:
  - Arming: the skill-load match ignores look-alike skills (`code-better-*`).
  - Bypass: it must start a line of a human message, so "don't bypass" doesn't unlock it. A `gate: pass` needs `rung=`.
  - Pre-gate writes: obvious Bash writes are blocked on the first call, not only on the next one.
  - Bash bypasses closed: single `&`, `$(...)` and backticks in "safe" commands, `git --no-pager commit`, `+refspec` force push, `git clean --force`, `terragrunt apply`.
  - Snapshots are anchored to `tool_use_id`, so an edit made right after `verify:` is not missed.
  - The block message no longer tells the agent to revert files it may not own.
  - Copy-install hooks exit 0 when the script is missing, instead of blocking every call.
  - Stage lines can also be declared as their own `echo "gate: pass - ..."` Bash call. Output styles that forbid text between tool calls (seen live, e.g. caveman or "no narration" rules) led the model to "print" the gate only in thinking.
  - Common test/build caches (`__pycache__`, `.pytest_cache`, `node_modules`, ...) don't count as changes, even when a repo doesn't gitignore them.
  - The git sensor no longer turns off when `CLAUDE.local.md` is gitignored (an ignored pathspec made `git add` fail). Measured at 0.17 s on django.

## [0.6.0] - 2026-11-02

### Fixed

- Right-sized for very large repos: monorepos and repos over ~2000 files get a scoped code map (root layout plus the touched subtree). Additive-only public changes stay at the micro rung.
- Missing check tools run isolated (`uvx`, `npx`, `go run`) at the version the repo pins. The hot-files scan is capped.

## [0.5.0] - 2026-11-02

### Added

- Hardening for large existing codebases:
  - local rules first, and a blast-radius grep for identifiers and strings
  - compat rules: additive changes, deprecate on rename, Terraform `moved` blocks
  - a baseline test run before the first edit, and characterization tests for untested code
  - offline-first infra checks
  - the repo's CI checks for changed paths
  - `debug:` exit with a "not a bug" outcome
- LICENSE (MIT) and THIRD_PARTY_NOTICES.md.

## [0.4.0] - 2026-11-02

### Changed

- Plans (`.claude/plans/NN-<slice>.md`) and session state (`.claude/state.md`) live under the repo-root `.claude/`.

## [0.3.0] - 2026-11-02

### Added

- The Gate builds a ≤80-line `.claude/code-map.md` for existing repos and imports it via `CLAUDE.local.md`. It is personal by default, kept out of git via `info/exclude`. No graphify install is needed.

## [0.2.0] - 2026-11-02

### Added

- Review fan-out subagents: triage, scoped CLAUDE.md rules, parallel single-lens reviewers, a high-signal filter, and validation of every finding. Models are picked by job.

## [0.1.0] - 2026-11-02

### Added

- The code-better skill: obra/superpowers and bmtrnavsky/disciplined-vibe-coding merged into one gated pipeline. Gate → Plan → Teardown → Build (test-first, debug) → Verify → Commit, with stakes tiers, scope rungs, and rollback rules.

[1.0.0]: https://github.com/neeltom92/code-better/compare/3afcf07...main
[0.6.0]: https://github.com/neeltom92/code-better/compare/ef99ee5...3afcf07
[0.5.0]: https://github.com/neeltom92/code-better/compare/1b67a91...ef99ee5
[0.4.0]: https://github.com/neeltom92/code-better/compare/f2a47b0...1b67a91
[0.3.0]: https://github.com/neeltom92/code-better/compare/280faf8...f2a47b0
[0.2.0]: https://github.com/neeltom92/code-better/compare/ea409e3...280faf8
[0.1.0]: https://github.com/neeltom92/code-better/commit/ea409e3
