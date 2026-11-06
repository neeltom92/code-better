---
name: code-better
description: Use when writing, changing, fixing, refactoring, or reviewing code or infra config in any repo - new features, bug fixes, failing tests or CI, broken deploys, migrations, Terraform/Helm/K8s changes, code-review feedback, or before claiming work is done, committing, or opening a PR.
---

# Code Better

One pipeline for all coding work, built for large existing codebases. Same stages every time; ceremony scales with risk. User instructions (CLAUDE.md, direct requests) override this skill.

```text
Gate --> Plan --> Teardown --> Build (test-first, debug) --> Verify --> Commit
```

## Iron laws

1. **No edit before understanding.** Read the code the change touches. Trace the real flow end to end.
2. **No fix without root cause.** Symptom patches are a second bug.
3. **No logic without a failing check first.** Watch it fail, then make it pass.
4. **No irreversible step without a written rollback.** If you can't say how to undo it, you can't do it yet.
5. **No "done" without fresh evidence.** Evidence from this turn, not memory or a subagent's word.
6. **No code that doesn't need to exist.** The best code is the code never written.

## Gate rule

Each stage exits with one line, in order: `map:` → `gate:` → (`debug:`) → `plan:` → `teardown/<round>:` → `build:` → `verify:` → `commit:`. Format: `<stage>: pass|fail - <reason>`; a stage the rung or the user skips prints nothing. A failed gate blocks the next stage. The only way past a red gate without fixing it is an explicit user bypass, stated in chat as: who approved, what was red, why it was waived. A silent skip is a defect. Gates are fast checks, not ceremony: small work gets less process, never more. Print each line as plain text in exactly this form (or, if your output style forbids text between tool calls, as its own `echo "gate: pass - ..."` Bash call): the harness reads them.

## Harness (enforced by hooks)

Installed as a plugin, or with `hooks/guard.py` wired into settings, the gates are checked from your transcript and from the git working tree, so a file changed by Bash counts the same as one changed by Edit:

- No file change before `gate: pass`; at full/project rung, none before `plan: pass` and `teardown/readiness: pass` either.
- No `git commit`, and no ending the turn, with files changed after the last `verify:` line (commit needs `verify: pass`).
- No force push, `git reset --hard`, `git clean -f`, or `terraform apply` without a saved plan file.
- A block names what is missing: produce that. Never route around it with another tool or a rephrased command. `<stage>: bypass - <why>` passes only after a user message starts with "bypass". Off switch: `CODE_BETTER_GUARD=off`. Decision log: `$(git rev-parse --git-path code-better)/harness.log`.

## Pick the entry

| Situation | Path |
|---|---|
| New behavior or change | Gate → Plan → Teardown → Build → Verify → Commit |
| Something broken (error, failing test, CI, pod, perf) | Gate → Debug (find cause) → Plan → Teardown → fix → Verify → Commit |
| Restructure without behavior change | Gate → Plan → Teardown → Refactor → Verify → Commit |
| Review a diff or PR | Gate → review fan-out (Subagents) → report |
| Received review feedback | Gate → Review → Plan → Teardown → Build → Verify → Commit |
| "Is it done?" / about to commit or open PR | Verify → Commit |

Plan and Teardown always run at the gate's rung: at one-liner that is one chat line and no teardown.

## 1. Gate: understand, classify, size

Understand first:

- **Code map:** `.claude/state.md` exists → read it first and resume at its last `next:`. Read `.claude/code-map.md` (usually auto-loaded via `CLAUDE.local.md`). Missing, or `git diff --name-status <at>..HEAD` touches entry points, build/CI files, or top-level dirs → build or refresh it per `references/code-map.md` before the first change (a clearly one-line request may defer it); else `map: pass - fresh at <at>`. `graphify-out/` exists → query that instead. Orientation-only request → the map is the whole Gate.
- **Local rules:** read the nearest CLAUDE.md / AGENTS.md / CONTRIBUTING and lint config for each subtree you touch, plus 1-2 sibling files. Copy their patterns (errors, logging, config loading, naming, test layout) even where you'd choose differently.
- Turn the request into observable acceptance criteria and explicit non-goals. Rambling or self-correcting request → state the reading you're acting on in one line.
- **Blast radius** (before the first edit): grep every reference to what you change, as identifier AND string: callers, config/env keys, Helm values and templates, TF outputs and remote-state consumers, CI files, SQL, reflection/DI. Generated file (header says so, or a map danger zone) → change the source or generator and regenerate.
- Unfamiliar API, library, or version → read its docs or changelog first. Never write against an API from memory.
- Ambiguous, and the answer changes the work → ask ONE question with a recommended default. Otherwise state the default and proceed.

Then declare: `gate: pass - tier=internal rung=micro, one component, reversible`.

**Stakes tier** (by where the change ships, not where you edit it):

| Tier | Means | Adds |
|---|---|---|
| sandbox | never ships: spike, scratch, throwaway | nothing; rollback can be "discard the branch" |
| internal | ships to your own systems, CI, staging; additive public-surface change | Plan defaults |
| prod | runs in production, customer data, payments, auth/secrets, breaking public-surface change | approval before Build, rollback + dry-run mandatory, review fan-out before done; never store card data |

**Scope rung** (by blast radius, not file count; pick the lower one when unsure):

| Rung | When | Plan | Teardown |
|---|---|---|---|
| one-liner | 1 logical edit (+ its test), reversible, no open questions | the chat line | skip |
| micro | one component, reversible, additive-only public change, no schema change, no new dependency | 4 bullets | 2 passes, self |
| full | crosses components, irreversible, new dependency, breaking public-surface or schema change, or a map hub/danger zone | plan file | 5 rounds, fresh subagent |
| project | spans sessions, milestones | plan per milestone + state file | 5 rounds per milestone |

**Step-up rule:** when blast radius grows mid-work (new component, breaking public-surface change, new dependency, irreversible or prod touch), declare the higher rung and backfill its missing artifacts before continuing. Prod touches need user confirmation now. A rung never steps down mid-build. Prod tier is never a one-liner.

## 2. Plan

Existing pattern covers it → follow it, no alternatives. Real design choices → 2-3 approaches with trade-offs, simplest first, recommend one. Get approval before building when the change spans components, adds a dependency, changes a schema or breaks a public surface, or is prod tier. Too big → split into shippable slices; plan the first.

Every plan, at any rung, names (the 4 bullets at micro):

- **Steps**: each with exact file, the change, and the check command that proves it. No placeholders ("TBD", "add error handling", "similar to above").
- **Reuse first**: existing code, stdlib, installed deps, or managed services that cover it. New code needs a one-line reason.
- **Rollback**: how to undo each destructive or irreversible step (see Rollback below). "Fully reversible via `git revert`" is a valid line; a missing line is not.
- **Commit message draft**: `type: subject`.

Add when relevant:

- **Compat**: public-surface changes (API fields, CLI flags, env vars, config keys, Helm values, TF variables/outputs, event/DB schemas) are additive. Rename = add new, keep old working, mark deprecated. TF resource rename → `moved` block; plan must show 0 destroys.
- **Dry-run step** before any destructive action. The dry run gets its own check.
- **Rerun-safe**: jobs, migrations, and data scripts must pass when run twice. Name the idempotency mechanism.
- **Budget line** for anything over ~2 minutes of wall time: expected duration, cost, completion signal.
- **Metric band** for nondeterministic checks: `p95 < 200ms`, `F1 >= 0.82, seed 42`. Not a bare boolean.
- **Kill-switch** for anything that runs unsupervised (bots, cron, daemons, autoscalers): the decision policy is config, and the off switch exists before the code.

Full rung and up: write the plan to `.claude/plans/NN-<slice>.md`, `NN` = next free two-digit number (format in `references/templates.md`). Below that, keep it in chat. Exit: `plan: pass - 4 steps, rollback: git revert`.

## 3. Teardown: cold review before code

Review the plan before any code exists. Fixing a spec is cheap; fixing shipped code is not.

Read it **cold**: the plan and its linked sources only, no conversation memory, no "you know what I meant". A look-alike precedent that answers a different question does not pass.

- **micro (2 passes, self):** *consequence*: if we build exactly this, where does it break? *alternatives*: what else solves it, and is this the strongest option?
- **full+ (5 rounds, fresh subagent given only the plan file and linked sources):** 1. zoom-out: does the shape hang together? 2. comprehension: could a stranger follow it? 3. critique: trade-offs, edge cases, weakest point. 4. fit: does it still fit the codebase after the critique? 5. readiness: concrete enough to build from?

One line per round: `teardown/critique: fail - no rollback for column drop`. On a fail, fix the plan, not code, and re-run that round once. The same round failing twice → stop and ask the user for a direction change.

## 4. Build

### The lazy ladder

Stop at the first rung that holds:

1. Does it need to exist? Speculative need → skip it, say so in one line.
2. Already in this codebase? Reuse the helper, type, or pattern.
3. Stdlib does it? 4. Native platform feature covers it? (DB constraint over app code, CSS over JS.)
5. Already-installed dependency solves it? Never add a dependency for a few lines.
6. Can it be one line? 7. Only then: the minimum code that works.

### Scope

- Touch only what the plan names. Every changed line traces to the request. Discoveries go back to the plan, not straight into code.
- No unrequested abstractions, config, flags, modes, scaffolding "for later", drive-by refactors, renames, or reformatting.
- Remove dead code your change created. Mention other dead code; don't delete it. Odd legacy code guards a past bug until its history (`git log -L`, `git blame` → PR) shows otherwise.
- Mark deliberate shortcuts with their ceiling: `# simplified: global lock; per-account locks if throughput matters`.
- Never simplify away: input validation at trust boundaries, error handling that prevents data loss, security, accessibility.
- Diff touches files the plan doesn't name, or grows past ~2x the planned steps → stop and report before continuing.

### Test first (red → green → refactor)

0. **Baseline:** before the first edit, run the whole test module or package you'll touch. Already red on clean HEAD → pre-existing: record it, don't fix it unless in scope.
1. Smallest test for one behavior. Run it. Watch it fail for the expected reason. Fails for another reason (import, typo) → fix that and re-run. Passes already → wrong test, unless it is a characterization check pinning current behavior.
2. Minimum code to pass. Run it. Green, with no other tests broken. Refactor with tests green. Repeat. Wrote code before the test? Delete it and start from the test; don't keep it "as reference".

- No tests near the change → first pin current behavior at the nearest existing seam (CLI, HTTP, job entry, public function) with the repo's runner. Don't refactor for testability inside a fix or feature. Trivial one-liners need none.
- State exceptions: throwaway prototypes, generated code, pure config. Verify those by running them.
- **Infra: the failing check is the plan or diff.** Offline first: `terraform fmt -check`, `terraform init -backend=false && terraform validate`, `helm template` / `helm lint`, `actionlint`. Live diffs (`terraform plan -out=tfplan`, `helm diff`, `kubectl diff`) only via the repo's own path (Makefile, Atlantis, CI) or after confirming backend, workspace, and `kubectl config current-context`. No `init -upgrade`, `state`, or `apply` without approval.
- Exit: `build: pass - red→green, 3 files`.

### Debug (anything broken, during Build or as the entry)

Root cause first, in order:

1. Capture the exact symptom: error text, expected vs actual, environment, input. Can't reproduce → observe (logs, timing, exact errors); never code blind.
2. Reproduce with the smallest reliable case. Keep the original failing input.
3. Read evidence: stack trace, logs, config, data flow, and history of the exact lines (`git log -L :<func>:<file>`, `git blame`). Post-upgrade breakage → read the vendor changelog.
4. Compare against something that works: similar code, last green run, previous version.
5. Rank falsifiable hypotheses. Test one at a time with the cheapest check that tells them apart. Exit: `debug: pass - cause: <x>` → plan the fix at the gate's rung, or `debug: pass - not a bug: <evidence>` → report and stop.
6. Fix at the first point where actual diverges from expected, at the narrowest layer that owns the bug. One guard in the shared function beats a guard in every caller.
7. Prove it: a check that fails before the fix and passes after. Re-run the original reproduction.

**2 failed fixes → stop.** Report: tried / learned / unexplained / options. Let the user choose. A third attempt of the same shape is banned.

Infra triage, failing layer outward:

- **K8s:** `kubectl describe` (events, probes, OOMKilled, image pull) → `kubectl logs --previous` → `kubectl get events --sort-by=.lastTimestamp` → node pressure.
- **CI:** first failing step; diff against last green run (deps, runner image, secrets, cache).
- **Terraform/Helm:** plan/diff vs live state, drift, provider/chart version changes.
- **Network:** DNS → TCP → TLS → HTTP (`dig`, `nc -vz`, `openssl s_client`, `curl -v`).
- **Performance:** baseline first, same load, before changing anything.

Never: delete or weaken tests, suppress errors, add sleeps or silent fallbacks, claim a cause without evidence, touch prod without an understood cause and a rollback path.

### Refactor

- Tests green before the first move. No coverage → add characterization checks first.
- No behavior changes mixed in. One move at a time, green between moves. Preserve interfaces, errors, and ordering.

## Rollback (applies at every stage)

Before any destructive or irreversible step, have the undo ready and tested where possible. Prod restarts, rollbacks, and data fixes need user approval first.

- **Code:** work on a branch or `git worktree` (verify the worktree dir is gitignored). Shared history → `git revert <sha>`, never `reset --hard` or force-push.
- **Infra:** `terraform plan -out=tfplan` and apply that exact plan; know the previous state version. `helm rollback <release> <rev>`. `kubectl rollout undo deploy/<name>`.
- **Data/schema:** new migration via the repo's tool; never edit an applied one. Backup or snapshot first, then a down-migration, or expand → migrate → contract so old and new code both run mid-deploy. Verify row counts and checksums on both sides.
- **Flags:** risky prod-tier behavior ships behind the repo's existing flag or config mechanism (never a new one), default off. This is the one flag Scope allows; the plan names its removal step.
- **Abort criteria:** name the signal that triggers rollback (error rate, failed health check, mismatched counts) before you start.

## 5. Verify

Before any "done / fixed / passing" claim:

1. Name the command that proves each acceptance criterion. Run it fresh: targeted tests while building; before claiming done, the affected package's suite plus the repo's CI checks for changed paths (lint, format, typecheck, `terraform validate`, `helm lint`, codegen drift; read them from the CI config). Whole-repo suite only if cheap. Check tool missing → run it isolated (`uvx`, `npx`, `go run`) at the version the repo pins (pre-commit config, lockfile), or report it as not run; never install into the project's env without asking.
2. Read all output: exit code, failure count, warnings, skipped tests (skipped = not passed). Red that matches the baseline → pre-existing, report it. Flaky → report both results; never rerun until green.
3. Classify evidence: **terminal** (run this turn), **user-attested** (labeled, never simulated), **integrity** (counts, checksums, dry-run vs live: exit 0 with wrong numbers = FAIL), **metric** (observed value against its band).
4. Near-miss is a fail: `0.819 vs 0.82` goes to the user, not rounded up.
5. **Drift:** compare the plan against what was built. List divergences only, or "no drift".
6. Full rung and up, or prod tier → run the review fan-out (see Subagents) on the diff before claiming done.

Report compactly: `verify: pass - 9/9 (7 terminal, 1 integrity, 1 metric in band); 1 pre-existing red; no drift`. Show failures in full. Subagent says done → check its diff yourself. Acceptance and CI checks pass → stop. No polish, extra tests, or cleanup.

## 6. Commit

Never commit or push unless the user asks. When asked:

- **Secret scan the staged diff** (`git diff --cached`) for keys, tokens, passwords, connection strings, `.env` files. A hit blocks the commit until the secret is moved out and, if it ever left the machine, revoked.
- One logical change per commit. Message in the repo's convention, else `type: subject`; body says why. The acceptance criteria are the proof statement.
- Follow the repo's changelog convention (CHANGES file, changesets, release notes) at every rung. Tags only for project releases.
- Finishing a branch: offer merge locally / push + PR / keep / discard. Discard needs explicit confirmation.

## Review

**Receiving feedback:** read all of it first; ask about unclear items before implementing any. Verify each claim against the code; reviewers can be wrong. Push back with technical reasons when a suggestion breaks behavior, adds unused features, or conflicts with the user's decisions. No performative agreement. Order: blocking → simple → complex; test each. **Requesting review:** micro and below → self-review the diff. Full rung and up, prod tier, or a PR → review fan-out (Subagents).

## Subagents

Use them for an independent read (no shared context) or for parallel work with no shared state. ≤3 tool calls → do it yourself.

- **Brief like a peer:** goal, scope, constraints, what's ruled out, expected output format. Reviewers get the requirements and the diff, never your conclusions.
- **Model by job:** cheapest for triage and file lookups; mid for summaries and rule checks; strongest for the bug and defect lenses and for validation.
- **Workers** edit only their assigned files. No git, no plan edits, no gate calls. The orchestrator merges, verifies, and commits. Subagent says done → check its diff yourself.

**Review fan-out:**

1. **Triage** (cheap; skip for a diff you just wrote): stop if the change is trivial, already reviewed, or not ready. Prod tier is never trivial.
2. **Scope the rules:** list the CLAUDE.md files at the root and in parent dirs of changed files. A rule only applies to files under it.
3. **Parallel reviewers**, one lens each: rule compliance (quote the rule), bugs visible in the diff alone, defects in the introduced code (logic, security, compat). Prod tier: two reviewers per lens, and the defect lens may read outside the diff to check rollback, rerun-safety, auth, and locking.
4. **High signal only:** won't compile or parse, wrong for every input, or an in-scope rule clearly broken. Never flag: style, pre-existing issues, linter-catchable issues, nitpicks, rules silenced in code, or input-dependent maybes (prod tier: flag them if a concrete input breaks it).
5. **Validate** each finding with a separate subagent given only the finding and the code. Not confirmed → drop it.
6. **Report** confirmed findings, one per issue, with `file:line`. None → "No issues found." Post to a PR only when asked.

## Files this skill writes

`.claude/code-map.md`, `.claude/plans/`, `.claude/state.md` (project rung: one line per stage exit with gate result and next step), all under the repo root, plus one `@.claude/code-map.md` line in the repo-root `CLAUDE.local.md`. Keep all four out of git unless the user wants them shared: append each to `$(git rev-parse --git-path info/exclude)` (works in worktrees; `mkdir -p` its dir first; skip lines already there).

## Output

- Answer first. Code over prose. Show changed lines plus context, not whole files.
- One line per gate result. Final report ≤5 lines: what changed, how verified (command → result), skipped and when to add it, blockers.
- Persisted artifacts (comments, commits, PRs, docs) use normal prose.

## Red flags: stop and go back

| Thought | Reality |
|---|---|
| "Too simple to need a test / a plan" | Pick the one-liner rung. It still has a check. |
| "Rollback is obvious" | Write the line. Obvious undo steps fail at 3am. |
| "Cleaner to rename it" | Someone you can't see reads the old name. Add, deprecate. |
| "Quick fix now, investigate later" | Later never comes. Find the cause. |
| "Should work now" / "close enough" | Run it. A near-miss is a fail. |
| "I'll add it now, we'll need it" / "while I'm here" | YAGNI. Out of scope: mention it, don't do it. |
| "One more fix attempt" (after 2) | Stop. Report and let the user choose. |
| "The reviewer / subagent says it's fine" | Verify against the code and the diff. |
| "The hook is wrong, I'll do it via Bash" | Produce the missing stage line, or ask the user to bypass. |
