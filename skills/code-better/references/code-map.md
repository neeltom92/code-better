# Code map

A small, hand-checked map of an existing repo so every session starts oriented without re-exploring. Read this file only when the Gate says to build or refresh the map.

## When

- **Build:** no `.claude/code-map.md` in the repo and the task touches existing code.
- **Refresh:** the map's `at` commit is behind HEAD and `git diff --stat <at>..HEAD` adds or removes top-level dirs, entry points, or more than ~20% of files. Update only the sections that changed, then bump `at`.
- **Skip:** `graphify-out/` exists (query it instead), or the repo is under ~20 files (just read it).

## Build (≤10 tool calls; delegate to an Explore subagent if the repo has more than ~300 tracked files)

Gather, using tracked files only:

```bash
git ls-files | awk -F/ 'NF>1{print $1}' | sort | uniq -c | sort -rn | head -25            # top-level dirs by size
git ls-files | sed -n 's/.*\.\([a-z0-9]*\)$/\1/p' | sort | uniq -c | sort -rn | head -8   # languages
git log --since=6.months --name-only --format= | grep . | sort | uniq -c | sort -rn | head -15  # hot files
git ls-files | grep -iE '(^|/)(main|app|server|index|cli|manage|wsgi|asgi)\.[a-z]+$|^cmd/|Dockerfile|docker-compose|Makefile|Justfile|package\.json|pyproject\.toml|go\.mod|Cargo\.toml|\.github/workflows/|Chart\.yaml|\.tf$' | head -40
```

Then read only: the build/task file (Makefile, `package.json` scripts, `pyproject.toml`), one CI workflow, the README's setup section, and each entry point's first ~40 lines. Hubs = the hot-files list, plus the few modules that `git grep -c` shows imported by many files. Trace one main request or job path from entry to storage.

Never record secrets, credentials, hostnames from `.env`, or customer data.

## Write

`mkdir -p .claude`, then write `.claude/code-map.md` in this shape, ≤80 lines, facts only, every path real. Name symbols (`Session.send`), never line numbers: they rot on the next commit. A command not read from a real file gets `(unverified)`.

```markdown
# Code map
at: <short sha> · <date> · refresh: code-better Gate

## Stack
<languages, frameworks, runtime versions, package manager>

## Commands
build: `...` · test: `...` · single test: `...` · lint: `...` · run: `...`

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

- **Personal (default, for shared or legacy repos):** add the line `@.claude/code-map.md` (plain text, not in a code span) to `CLAUDE.local.md`. Then keep both files out of git without touching the team's `.gitignore`: `mkdir -p .git/info` and append `CLAUDE.local.md` and `.claude/code-map.md` to `.git/info/exclude`.
- **Team (only if the user says so):** put the import line in `CLAUDE.md` and commit the map with it.

Don't ask: default to personal and say in one line how to switch to team.

## Verify

- Every path in the map exists: `test -e <path>` for each.
- Every command was read from a real file (Makefile, scripts, CI), not guessed. Unverified commands get `(unverified)`.
- `git status --short` shows neither file when personal.
