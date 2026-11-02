# Templates

Load only when the rung calls for a file. Delete sections that don't apply.

## Plan file (full rung and up)

Path: `.claude/plans/NN-<slice>.md` at the repo root (`mkdir -p .claude/plans`). Keep it out of git per SKILL.md "Files this skill writes".

```markdown
# Plan: <one-line goal>

gate: tier=<sandbox|internal|prod> rung=<full|project> - <reason>

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

## Teardown
- zoom-out: pass|fail - <reason>
- comprehension:
- critique:
- fit:
- readiness:

## Commit draft
<type>: <subject>

## Verify (filled after build)
| Criterion | Command | Evidence class | Result |
|---|---|---|---|

Drift: <divergences, or "no drift">
```

## Session state (project rung)

Path: `.claude/state.md` at the repo root. Append one line per stage exit. The Gate reads it first when resuming. Keep it out of git per SKILL.md "Files this skill writes".

```markdown
# State: <project>

- <date> plan/01-auth: pass - approved by user | next: teardown
- <date> teardown/critique: fail - no rollback for column drop | next: add backup step
- <date> bypass: verify/integrity red, row count off by 3, waived by <user>: known soft-deletes
```
