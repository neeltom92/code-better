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
