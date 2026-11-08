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
