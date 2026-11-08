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
