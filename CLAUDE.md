# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Home of `code-better`, a single Claude Code skill that merges obra/superpowers and bmtrnavsky/disciplined-vibe-coding (plus the ponytail lazy ladder and caveman process skills) into one gated pipeline: Gate → Plan → Teardown → Build → Verify → Commit. No build, no dependencies.

- `skills/code-better/SKILL.md` — the skill. Frontmatter `name` + `description` (≤1024 chars, starts with "Use when…", lists triggers only, never summarizes the workflow — Claude skips the body if the description reads like a summary).
- `skills/code-better/references/templates.md` — `.claude/plans/NN-<slice>.md` and `.claude/state.md` formats, loaded only at full/project rung.
- `skills/code-better/references/code-map.md` — how the Gate builds/refreshes a ≤80-line `.claude/code-map.md` in target repos and imports it via `CLAUDE.local.md` (graphify-lite, no install).

## Install / use

```bash
ln -s "$PWD/skills/code-better" ~/.claude/skills/code-better   # global
```

Start a fresh `claude` session; the skill appears as `code-better`. It overlaps the superpowers, caveman, and ponytail plugins — disable those (`/plugin`) when testing to avoid duplicate or conflicting instructions.

## Editing rules

- Keep SKILL.md under ~250 lines; bulk formats go in `references/`. New material must replace or compress something, not just append.
- Numbered sections are pipeline stages (Gate, Plan, Teardown, Build, Verify, Commit); Debug and Refactor live inside Build. The "Pick the entry" table and the tier/rung tables must stay in sync with section names.
- User instructions (global `~/.claude/CLAUDE.md`) take priority over the skill; don't add rules that contradict them (terse output, never commit/push unless asked, no new deps without need).
- Upstream sources live in `~/.claude/plugins/cache/` (`claude-plugins-official/superpowers/*/skills`, `caveman/caveman/*/skills`, `ponytail/ponytail/*/skills`); disciplined-vibe-coding is not installed, so clone https://github.com/bmtrnavsky/disciplined-vibe-coding (`skills/`, `plugins/disciplined-vibe-coding/`). Diff against them when pulling in updates.

## Checking a change

```bash
head -4 skills/code-better/SKILL.md                                   # frontmatter intact
awk '/^description:/{print length($0)-13}' skills/code-better/SKILL.md # description length ≤1024
wc -l skills/code-better/SKILL.md
```

Behavioral check (superpowers `writing-skills` method): give a subagent a pressure scenario (e.g. "fix this failing test fast, deadline in 5 min") with and without the skill loaded, and confirm it follows the relevant iron law.
