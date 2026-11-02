---
name: code-better
description: Use when writing, changing, fixing, refactoring, or reviewing code or infra config in any repo - new features, bug fixes, failing tests or CI, broken deploys, migrations, Terraform/Helm/K8s changes, code-review feedback, or before claiming work is done, committing, or opening a PR.
---

# Code Better

One pipeline for all coding work. Same stages every time; ceremony scales with risk.

```text
Gate --> Plan --> Teardown --> Build (test-first, debug) --> Verify --> Commit
```

User instructions (CLAUDE.md, direct requests) override this skill.

## Iron laws

1. **No edit before understanding.** Read the code the change touches. Trace the real flow end to end.
2. **No fix without root cause.** Symptom patches are a second bug.
3. **No logic without a failing check first.** Watch it fail, then make it pass.
4. **No irreversible step without a written rollback.** If you can't say how to undo it, you can't do it yet.
5. **No "done" without fresh evidence.** Evidence from this turn, not memory or a subagent's word.
6. **No code that doesn't need to exist.** The best code is the code never written.

## Gate rule

Each stage exits with a one-line result: `<stage>: pass|fail - <reason>`. A failed gate blocks the next stage. The only way past a red gate without fixing it is an explicit user bypass, stated in chat as: who approved, what was red, why it was waived. A silent skip is a defect.

Gates are fast checks, not ceremony. Small work gets less process, never more.

## Pick the entry

| Situation | Path |
|---|---|
| New behavior or change | Gate → Plan → Teardown → Build → Verify → Commit |
| Something broken (error, failing test, CI, pod, perf) | Gate → Debug → Verify → Commit |
| Restructure without behavior change | Gate → Plan → Refactor → Verify → Commit |
| Review a diff or PR | Gate → review fan-out (Subagents) → report |
| Received review feedback | Review → Build → Verify |
| "Is it done?" / about to commit or open PR | Verify → Commit |

## 1. Gate: understand, classify, size

Understand first:

- Turn the request into observable acceptance criteria and explicit non-goals.
- Search before reading. Read only the line ranges you need. Trace entry point → effect. Grep every caller of anything you will change.
- Unfamiliar API, library, or version → read its docs or changelog first. Never write against an API from memory.
- Ambiguous, and the answer changes the work → ask ONE question with a recommended default. Otherwise state the default and proceed.

Then declare tier and rung in one line: `gate: tier=internal rung=micro - reversible 2-file change`.

**Stakes tier:**

| Tier | Means | Adds |
|---|---|---|
| sandbox | local, throwaway, nothing at risk | nothing |
| internal | your own systems, CI, staging could break | rollback line for destructive steps |
| prod | production, customer data, payments, public surface, security | approval before Build, rollback + dry-run mandatory, review fan-out before done |

**Scope rung** (pick the lower one when unsure):

| Rung | When | Plan | Teardown | Commit |
|---|---|---|---|---|
| one-liner | 1 file, reversible, no open questions | the chat line | skip | single commit |
| micro | ≤3 files, reversible, no new dependency | 3 bullets | 2 passes, self | single commit |
| full | more files, irreversible, new dependency, schema/API change | full plan | 5 rounds, fresh subagent | changelog entry if repo keeps one |
| project | spans sessions, milestones | plan per milestone + state file | 5 rounds per milestone | changelog + tag at release |

**Step-up rule:** when blast radius grows mid-work (more files, new dependency, irreversible or prod touch), declare the higher rung and backfill its missing artifacts before continuing. Prod touches need user confirmation now. A rung never steps down mid-build. Prod tier is never a one-liner.

## 2. Plan

Real design choices → 2-3 approaches with trade-offs, simplest first, recommend one. Get approval before building when the change spans components, adds a dependency, changes a schema/API, or is prod tier. Too big → split into shippable slices; plan the first.

Every plan, at any rung, names:

- **Steps**: each with exact file, the change, and the check command that proves it. No placeholders ("TBD", "add error handling", "similar to above").
- **Reuse first**: existing code, stdlib, installed deps, or managed services that cover it. New code needs a one-line reason.
- **Rollback**: how to undo each destructive or irreversible step (see Rollback below). "Fully reversible via `git revert`" is a valid line; a missing line is not.
- **Commit message draft**: `type: subject`.

Add when relevant:

- **Dry-run step** before any destructive action. The dry run gets its own check.
- **Rerun-safe**: jobs, migrations, and data scripts must pass when run twice. Name the idempotency mechanism.
- **Budget line** for anything over ~2 minutes of wall time: expected duration, cost, completion signal.
- **Metric band** for nondeterministic checks: `p95 < 200ms`, `F1 >= 0.82, seed 42`. Not a bare boolean.
- **Kill-switch** for anything that runs unsupervised (bots, cron, daemons, autoscalers): the decision policy is config, and the off switch exists before the code.
- **Payments**: provider-hosted checkout only. A plan that stores raw card data is rejected.

Full rung and up: write the plan to a file (format in `references/templates.md`). Below that, keep it in chat.

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
- Remove dead code your change created. Mention other dead code; don't delete it.
- Mark deliberate shortcuts with their ceiling: `# simplified: global lock; per-account locks if throughput matters`.
- Never simplify away: input validation at trust boundaries, error handling that prevents data loss, security, accessibility.
- Diff grows to ~2x the plan's estimate → stop and report before continuing.

### Test first (red → green → refactor)

1. Smallest test for one behavior. Run it. Watch it fail for the expected reason. Passes already → the test is wrong.
2. Minimum code to pass. Run it. Green, with no other tests broken. Refactor with tests green. Repeat.

Wrote code before the test? Delete it and start from the test. Don't keep it "as reference".

- No test suite → leave one runnable check for non-trivial logic (`assert`-based `__main__` or one small test file). Trivial one-liners need none.
- State exceptions: throwaway prototypes, generated code, pure config. Verify those by running them.
- **Infra: the failing check is the plan or diff.** `terraform plan -out`, `helm diff` / `helm template`, `kubectl diff` or `--dry-run=server`, `actionlint`. Read the diff before any apply.

### Debug (anything broken, during Build or as the entry)

Root cause first, in order:

1. Capture the exact symptom: error text, expected vs actual, environment, input. Can't reproduce → observe (logs, timing, exact errors); never code blind.
2. Reproduce with the smallest reliable case. Keep the original failing input.
3. Read evidence: stack trace, logs, `git log -p` / `git diff`, config, data flow. Post-upgrade breakage → read the vendor changelog.
4. Compare against something that works: similar code, last green run, previous version.
5. Rank falsifiable hypotheses. Test one at a time with the cheapest check that tells them apart.
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

Before any destructive or irreversible step, have the undo ready and tested where possible:

- **Code:** work on a branch or `git worktree` (verify the worktree dir is gitignored). Shared history → `git revert <sha>`, never `reset --hard` or force-push.
- **Infra:** `terraform plan -out=tfplan` and apply that exact plan; know the previous state version. `helm rollback <release> <rev>`. `kubectl rollout undo deploy/<name>`.
- **Data/schema:** backup or snapshot first, then a down-migration or expand → migrate → contract. Verify row counts and checksums on both sides.
- **Flags:** risky behavior ships behind a flag or config toggle that can be turned off without a deploy.
- **Abort criteria:** name the signal that triggers rollback (error rate, failed health check, mismatched counts) before you start.

Prod restarts, rollbacks, and data fixes need user approval first.

## 5. Verify

Before any "done / fixed / passing" claim:

1. Name the command that proves each acceptance criterion. Run it fresh and in full.
2. Read all output: exit code, failure count, warnings, skipped tests (skipped = not passed).
3. Classify evidence: **terminal** (run this turn), **user-attested** (labeled, never simulated), **integrity** (counts, checksums, dry-run vs live: exit 0 with wrong numbers = FAIL), **metric** (observed value against its band).
4. Near-miss is a fail: `0.819 vs 0.82` goes to the user, not rounded up.
5. **Drift:** compare the plan against what was built. List divergences only, or "no drift".
6. Full rung or prod tier → run the review fan-out (see Subagents) on the diff before claiming done.

Report compactly: `verify: 9/9 pass (7 terminal, 1 integrity, 1 metric in band); no drift`. Show failures in full. Subagent says done → check its diff yourself. Acceptance passes → stop. No polish, extra tests, or cleanup.

## 6. Commit

Never commit or push unless the user asks. When asked:

- **Secret scan the staged diff** (`git diff --cached`) for keys, tokens, passwords, connection strings, `.env` files. A hit blocks the commit until the secret is moved out and, if it ever left the machine, revoked.
- One logical change per commit. Message: `type: subject`, body says why. The acceptance criteria are the proof statement.
- Rung-scaled: one-liner and micro ship as one commit. Full adds a changelog entry if the repo keeps one. Tags only for project releases.
- Finishing a branch: offer merge locally / push + PR / keep / discard. Discard needs explicit confirmation.

## Review

**Receiving feedback:** read all of it first; ask about unclear items before implementing any. Verify each claim against the code; reviewers can be wrong. Push back with technical reasons when a suggestion breaks behavior, adds unused features, or conflicts with the user's decisions. No performative agreement. Order: blocking → simple → complex; test each.

**Requesting review:** micro and below → self-review the diff. Full rung, prod tier, or a PR → review fan-out (Subagents).

## Subagents

Use them for an independent read (no shared context) or for parallel work with no shared state. ≤3 tool calls → do it yourself.

- **Brief like a peer:** goal, scope, constraints, what's ruled out, expected output format. Reviewers get the requirements and the diff, never your conclusions.
- **Model by job:** cheapest for triage and file lookups; mid for summaries and rule checks; strongest for the bug and defect lenses and for validation.
- **Workers** edit only their assigned files. No git, no plan edits, no gate calls. The orchestrator merges, verifies, and commits. Subagent says done → check its diff yourself.

**Review fan-out:**

1. **Triage** (cheap): stop if the change is trivial, already reviewed, or not ready. Prod tier is never trivial.
2. **Scope the rules:** list the CLAUDE.md files at the root and in parent dirs of changed files. A rule only applies to files under it.
3. **Parallel reviewers**, one lens each: rule compliance (quote the rule), bugs visible in the diff alone, defects in the introduced code (logic, security). Prod tier: two reviewers per lens, and the defect lens may read outside the diff to check rollback, rerun-safety, auth, and locking.
4. **High signal only:** won't compile or parse, wrong for every input, or an in-scope rule clearly broken. Never flag: style, pre-existing issues, linter-catchable issues, nitpicks, rules silenced in code, or input-dependent maybes (prod tier: flag them if a concrete input breaks it).
5. **Validate** each finding with a separate subagent given only the finding and the code. Not confirmed → drop it.
6. **Report** confirmed findings, one per issue, with `file:line`. None → "No issues found." Post to a PR only when asked.

## Session state (project rung only)

Keep `.pipeline/state.md`: one line per stage exit with the gate result and the next step, so a new session resumes without a re-brief. Format in `references/templates.md`. Ask whether `.pipeline/` should be committed or gitignored.

## Output

- Answer first. Code over prose. Show changed lines plus context, not whole files.
- One line per gate result. Final report ≤5 lines: what changed, how verified (command → result), skipped and when to add it, blockers.
- Persisted artifacts (comments, commits, PRs, docs) use normal prose.

## Red flags: stop and go back

| Thought | Reality |
|---|---|
| "Too simple to need a test / a plan" | Pick the one-liner rung. It still has a check. |
| "Rollback is obvious" | Write the line. Obvious undo steps fail at 3am. |
| "Quick fix now, investigate later" | Later never comes. Find the cause. |
| "Should work now" / "close enough" | Run it. A near-miss is a fail. |
| "I'll add it now, we'll need it" / "while I'm here" | YAGNI. Out of scope: mention it, don't do it. |
| "One more fix attempt" (after 2) | Stop. Report and let the user choose. |
| "The reviewer / subagent says it's fine" | Verify against the code and the diff. |
| "Need more context first" (forever) | Stop exploring once evidence names the cause or the blocker. |

## Sources

Merged from obra/superpowers (brainstorming, writing-plans, test-driven-development, systematic-debugging, verification-before-completion, receiving-code-review, subagent-driven-development, using-git-worktrees, finishing-a-development-branch) and bmtrnavsky/disciplined-vibe-coding (pipeline gates and logged bypass, stakes tiers, economy ladder, teardown, plan rules for rollback / dry-run / rerun-safe / kill-switch / payments, evidence classes, drift, secret scan, wayfinder), the review fan-out logic of the anthropics/claude-plugins-official `code-review` command (triage, scoped rules, parallel lenses, validate-then-filter, model tiering), plus the ponytail lazy ladder and caveman process skills. superpowers and disciplined-vibe-coding are MIT; the code-review command is Apache-2.0 and only its logic is reused, not its text.
