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
