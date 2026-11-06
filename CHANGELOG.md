# Changelog

All notable changes to code-better. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [SemVer](https://semver.org/). The version here matches `.claude-plugin/plugin.json`.

Upgrading a per-repo copy: read the entries since your version, then re-copy `skills/code-better/` and re-merge `hooks/settings.json` if the Changed section mentions hooks.

## [1.0.0] - 2026-11-06

code-better is now an agent harness: the stage gates are enforced by hooks, not just written down.

### Added

- `skills/code-better/hooks/guard.py`: one stdlib-only Python hook for PreToolUse (Edit, Write, MultiEdit, NotebookEdit, Bash) and Stop. It reads two sensors. The session transcript shows which stage lines were printed. A git working-tree fingerprint, built in a temp index, catches files changed by any tool, Bash included. It is armed only after the skill loads in a session. Controls, each tied to the incident it exists for:
  - G1: no file change before `gate: pass`.
  - G2: at full/project rung, no change before `plan: pass` and `teardown/readiness: pass`.
  - G3: no `git commit` with files changed after the last `verify: pass`.
  - G4: no ending the turn with files changed after the last `verify:` line.
  - G5: no force push, `git reset --hard`, `git clean -f`, or `terraform|tofu apply` without a saved plan.
- Bypass: a `<stage>: bypass` line, or a G5 command, passes only after a human message in the session says "bypass". Kill-switch: `CODE_BETTER_GUARD=off`.
- Decision log, one JSON line per armed hook call, at `$(git rev-parse --git-path code-better)/harness.log`. It lives inside `.git`, so there is nothing to gitignore.
- Plugin packaging: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, and `hooks/hooks.json`. Install with `claude plugin install code-better --marketplace neeltom92/code-better`. Teams and orgs can require it with `extraKnownMarketplaces` + `enabledPlugins`.
- `skills/code-better/hooks/settings.json`: the hooks block for per-repo copy installs with no marketplace access.
- `tests/test_guard.py`: two-sided tests, so every rule both fires and stays quiet; 59 cases, stdlib `unittest`. CI runs them, plus the skill checks, in `.github/workflows/ci.yml`.
- This changelog.

### Changed

- SKILL.md: new "Harness (enforced by hooks)" section. Stage lines must be plain text in the exact `<stage>: pass|fail - <reason>` form. Added a red flag against routing around a block. Compressed a few one-line paragraphs to stay at 250 lines.
- README: install paths for plugin, team repo, org-managed, per-repo copy, and skill-only; plus harness operations.

### Fixed during live testing (before release)

- Live runs showed the agent editing through a Bash heredoc before printing `gate:`. Edit-tool tracking alone missed this, so the git sensor was added.
- Other plugins' state under `.claude/` (e.g. autoharness) no longer counts as a change.
- A temp index copied with a fresh mtime hid same-second, same-size edits. Fixed by preserving the mtime (git racy-clean check).
- A stage line printed in the same message as the tool call can land in the transcript after the hook runs. The guard now re-reads before denying, and Stop reads `last_assistant_message`. A `gate:` line that appears only in the final message does not count.
- Read-only and revert commands (`cat`, `grep`, `git status|diff|restore|checkout|stash`, ...) are always allowed, so a G1 block cannot deadlock the session.
- Stage lines are matched case-insensitively and tolerate `**bold**` or backticks. `<system-reminder>` text never counts as a user bypass.
- From an independent review, before release:
  - Arming: the skill-load match ignores look-alike skills (`code-better-*`).
  - Bypass: it must start a line of a human message, so "don't bypass" doesn't unlock it. A `gate: pass` needs `rung=`.
  - Pre-gate writes: obvious Bash writes are blocked on the first call, not only on the next one.
  - Bash bypasses closed: single `&`, `$(...)` and backticks in "safe" commands, `git --no-pager commit`, `+refspec` force push, `git clean --force`, `terragrunt apply`.
  - Snapshots are anchored to `tool_use_id`, so an edit made right after `verify:` is not missed.
  - The block message no longer tells the agent to revert files it may not own.
  - Copy-install hooks exit 0 when the script is missing, instead of blocking every call.
  - Stage lines can also be declared as their own `echo "gate: pass - ..."` Bash call. Output styles that forbid text between tool calls (seen live, e.g. caveman or "no narration" rules) led the model to "print" the gate only in thinking.
  - Common test/build caches (`__pycache__`, `.pytest_cache`, `node_modules`, ...) don't count as changes, even when a repo doesn't gitignore them.
  - The git sensor no longer turns off when `CLAUDE.local.md` is gitignored (an ignored pathspec made `git add` fail). Measured at 0.17 s on django.

## [0.6.0] - 2026-11-02

### Fixed

- Right-sized for very large repos: monorepos and repos over ~2000 files get a scoped code map (root layout plus the touched subtree). Additive-only public changes stay at the micro rung.
- Missing check tools run isolated (`uvx`, `npx`, `go run`) at the version the repo pins. The hot-files scan is capped.

## [0.5.0] - 2026-11-02

### Added

- Hardening for large existing codebases:
  - local rules first, and a blast-radius grep for identifiers and strings
  - compat rules: additive changes, deprecate on rename, Terraform `moved` blocks
  - a baseline test run before the first edit, and characterization tests for untested code
  - offline-first infra checks
  - the repo's CI checks for changed paths
  - `debug:` exit with a "not a bug" outcome
- LICENSE (MIT) and THIRD_PARTY_NOTICES.md.

## [0.4.0] - 2026-11-02

### Changed

- Plans (`.claude/plans/NN-<slice>.md`) and session state (`.claude/state.md`) live under the repo-root `.claude/`.

## [0.3.0] - 2026-11-02

### Added

- The Gate builds a ≤80-line `.claude/code-map.md` for existing repos and imports it via `CLAUDE.local.md`. It is personal by default, kept out of git via `info/exclude`. No graphify install is needed.

## [0.2.0] - 2026-11-02

### Added

- Review fan-out subagents: triage, scoped CLAUDE.md rules, parallel single-lens reviewers, a high-signal filter, and validation of every finding. Models are picked by job.

## [0.1.0] - 2026-11-02

### Added

- The code-better skill: obra/superpowers and bmtrnavsky/disciplined-vibe-coding merged into one gated pipeline. Gate → Plan → Teardown → Build (test-first, debug) → Verify → Commit, with stakes tiers, scope rungs, and rollback rules.

[1.0.0]: https://github.com/neeltom92/code-better/compare/3afcf07...main
[0.6.0]: https://github.com/neeltom92/code-better/compare/ef99ee5...3afcf07
[0.5.0]: https://github.com/neeltom92/code-better/compare/1b67a91...ef99ee5
[0.4.0]: https://github.com/neeltom92/code-better/compare/f2a47b0...1b67a91
[0.3.0]: https://github.com/neeltom92/code-better/compare/280faf8...f2a47b0
[0.2.0]: https://github.com/neeltom92/code-better/compare/ea409e3...280faf8
[0.1.0]: https://github.com/neeltom92/code-better/commit/ea409e3
