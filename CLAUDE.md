# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Home of `code-better`, a Claude Code agent harness for large existing codebases: a skill that merges obra/superpowers and bmtrnavsky/disciplined-vibe-coding (plus the ponytail lazy ladder and caveman process skills) into one adaptive, gated lifecycle shaped like AWS's AI-DLC (awslabs/aidlc-workflows): Inception (Gate → Plan → Teardown), Construction (Build → Verify), Hand-off (commit, PR, and deploy commands the user runs). Scopes pick the stages, rung picks depth, tier picks approvals. A hook guard enforces the gates. Shipped as a plugin and as a copyable skill folder. No build; stdlib Python only.

- `skills/code-better/SKILL.md` — the skill. Frontmatter `name` + `description` (≤1024 chars, starts with "Use when…", lists triggers only, never summarizes the workflow — Claude skips the body if the description reads like a summary).
- `skills/code-better/references/templates.md` — plan (`.claude/plans/NN-<slice>.md`), questions file, `.claude/state.md`, and append-only `.claude/audit.md` formats, loaded only at full/project rung or in prod tier.
- `skills/code-better/references/code-map.md` — how the Gate builds/refreshes a ≤80-line `.claude/code-map.md` in target repos and imports it via `CLAUDE.local.md` (graphify-lite, no install).
- `skills/code-better/references/review.md` — the review fan-out (full rung and up, prod tier, PRs), loaded on demand.
- `skills/code-better/hooks/guard.py` — the harness: one PreToolUse/Stop hook, rules G1-G5, each documented with the incident it exists for; its block messages cite "SKILL.md section N". Lives inside the skill folder so a per-repo copy carries it. `hooks/hooks.json` (plugin) and `skills/code-better/hooks/settings.json` (copy install) both point at it.
- `scripts/upgrade_prompt.py` — embeds every skill file, with checksums, in the newest CHANGELOG upgrade prompt, so offline enterprise users can upgrade by pasting it. Run it after any change under `skills/code-better/`; `tests/test_upgrade_prompt.py` fails when the copy is stale.
- `.claude-plugin/plugin.json` + `marketplace.json` — plugin manifests; `version` must match the top entry in `CHANGELOG.md`.

## Install / use

```bash
claude --plugin-dir "$(git rev-parse --show-toplevel)"   # load this checkout as a plugin (skill + hooks)
```

The skill appears as `code-better:code-better`. It overlaps the superpowers, caveman, and ponytail plugins — disable those (`/plugin`) when testing to avoid duplicate or conflicting instructions.

## Editing rules

- Keep SKILL.md under ~250 lines; bulk formats go in `references/`. New material must replace or compress something, not just append.
- Numbered sections 1-6 are the stages, grouped under phases: Inception (1 Gate, 2 Plan, 3 Teardown), Construction (4 Build, 5 Verify), Hand-off (6 Hand-off: commit, PR, and deploy commands the user runs; the agent never runs them). Debug, Refactor, and Rollback live inside Build. The "Scopes" table, the tier/rung tables, and the "Checkpoints" list must stay in sync with section names.
- Guard messages cite "SKILL.md section N": never renumber sections 1-5. A new stage goes after them or under an existing one.
- User instructions (global `~/.claude/CLAUDE.md`) take priority over the skill; don't add rules that contradict them (terse output, never commit/push unless asked, no new deps without need). The Hand-off rule is deliberately stricter: the agent never commits, pushes, merges, or deploys, even when asked. Keep it.
- Upstreams to diff against when pulling in updates: https://github.com/obra/superpowers (`skills/`), https://github.com/bmtrnavsky/disciplined-vibe-coding (`skills/`, `plugins/disciplined-vibe-coding/`), https://github.com/awslabs/aidlc-workflows (`v1` branch, and `core/` on `main`), and the `code-review` command in https://github.com/anthropics/claude-plugins-official. If you adapt new upstream material, update `THIRD_PARTY_NOTICES.md`.
- The skill targets large existing codebases: prefer rules that follow repo conventions, protect public surfaces, and keep exploration cheap.
- Every change gets a `CHANGELOG.md` entry (Keep a Changelog sections) and, on release, a `version` bump in `.claude-plugin/plugin.json`.
- Harness rules: add one only in reaction to an observed failure, name that incident in `guard.py`'s docstring, and add tests both ways (must block / must allow). Remove a rule when the decision log shows its incident stopped. The guard must stay stdlib-only and fail open.
- Stage-line formats in SKILL.md and the `STAGE` regex in `guard.py` must stay in sync for the guarded stages (gate, plan, teardown/<round>, verify); `map:`, `debug:`, `build:`, and `handoff:` are unguarded.

## Checking a change

```bash
head -4 skills/code-better/SKILL.md                                   # frontmatter intact
awk '/^description:/{print length($0)-13}' skills/code-better/SKILL.md # description length ≤1024
wc -l skills/code-better/SKILL.md
python3 -m unittest discover -s tests                                  # guard tests, both directions
python3 scripts/upgrade_prompt.py                                      # refresh the embedded upgrade prompt
claude plugin validate .                                               # manifests and skills
```

Behavioral check (superpowers `writing-skills` method): give a subagent a pressure scenario (e.g. "fix this failing test fast, deadline in 5 min") with and without the skill loaded, and confirm it follows the relevant iron law. For hook changes, also run a live session against a scratch git repo with `claude -p --plugin-dir <this repo>` and read `.git/code-better/harness.log`.
