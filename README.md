# code-better

A single Claude Code skill for senior engineers working in large existing codebases. It merges [obra/superpowers](https://github.com/obra/superpowers) and [bmtrnavsky/disciplined-vibe-coding](https://github.com/bmtrnavsky/disciplined-vibe-coding) into one gated pipeline:

```text
Gate --> Plan --> Teardown --> Build (test-first, debug) --> Verify --> Commit
```

- **Gate**: in an existing repo, first build or refresh a ≤80-line code map (`.claude/code-map.md`: stack, commands, layout, entry points, main flows, hubs, danger zones), imported from `CLAUDE.local.md` so every later session loads it. Personal by default (kept out of git via `.git/info/exclude`); no graphify install needed. Then understand the code, then declare a stakes tier (`sandbox` / `internal` / `prod`) and a scope rung (`one-liner` / `micro` / `full` / `project`). The rung sets how much process the later stages get.
- **Plan**: follow the repo's existing patterns; steps with check commands, reuse first, and a rollback line for every destructive step. Public-surface changes (env vars, config keys, Helm values, TF variables, schemas) stay additive. Adds dry-run, idempotency, metric bands, and a kill-switch when relevant.
- **Teardown**: cold review of the plan before any code exists. Two passes at `micro`; five rounds by a fresh subagent at `full` and above.
- **Build**: lazy ladder (reuse, then stdlib, then minimum code), a baseline test run before the first edit, red-green TDD with characterization tests for untested legacy code, offline-first infra checks (`terraform validate`, `helm lint`) before any live diff, root-cause debugging with a 2-failed-fixes stop.
- **Verify**: targeted tests plus the repo's own CI checks for changed paths; failures already on the baseline are reported, not "fixed". Evidence by class (terminal, user-attested, integrity, metric). A near-miss is a fail. Drift is checked against the plan.
- **Subagents**: review fan-out for full/prod work. Parallel reviewers each take one lens (scoped CLAUDE.md rules, diff bugs, introduced-code defects); every finding is validated by a separate subagent before it is reported. Models are picked by job.
- **Commit**: only when asked. Secret scan the staged diff first. One logical change per commit.

A failed gate blocks the next stage unless the user explicitly bypasses it, and the bypass is stated.

## Install

Requires [Claude Code](https://code.claude.com). Pick one variant; if the same skill is installed both globally and in a repo, the personal (global) one wins.

**All projects** (symlink, so `git pull` updates it):

```bash
git clone https://github.com/neeltom92/code-better ~/code-better
mkdir -p ~/.claude/skills
ln -sfn ~/code-better/skills/code-better ~/.claude/skills/code-better
```

**One repo only** (a copy you can commit for your team):

```bash
cd /path/to/your-repo
mkdir -p .claude/skills
rm -rf .claude/skills/code-better   # only when updating an existing copy
cp -R ~/code-better/skills/code-better .claude/skills/
```

Check it loaded: start `claude` in a repo and type `/code-better`, or run `/skills`. If the superpowers, caveman, or ponytail plugins are enabled, disable them with `/plugin`; they inject overlapping rules.

To update: `git -C ~/code-better pull` (symlink install picks it up; re-copy for the per-repo install).

## Use

In any repo, invoke it directly or let it trigger on coding tasks:

```text
/code-better add rate limiting to POST /login
/code-better CI is failing on the integration job since yesterday
```

Everything it writes lives under the target repo's root `.claude/`: `code-map.md`, `plans/NN-<slice>.md` (full and project rung), and `state.md` (project rung), plus one `@.claude/code-map.md` import line in `CLAUDE.local.md`. Formats are in `skills/code-better/references/`. These files stay out of git through the repo's `info/exclude` (worktree-safe) by default, so the team's `.gitignore` is untouched; commit them if you want them shared.

## Layout

```text
skills/code-better/SKILL.md                  the skill
skills/code-better/references/templates.md   plan file and session-state formats
skills/code-better/references/code-map.md    how the repo code map is built, wired in, and refreshed
CLAUDE.md                                    editing rules for this repo
LICENSE                                      MIT
THIRD_PARTY_NOTICES.md                       upstream copyright and license notices
```

## Credits and license

MIT, see `LICENSE`. Adapts material from obra/superpowers (MIT, Jesse Vincent), bmtrnavsky/disciplined-vibe-coding (MIT, Brad Trnavsky), and the ponytail plugin (MIT, DietrichGebert); their notices are in `THIRD_PARTY_NOTICES.md`. The review fan-out follows the logic of the `code-review` command in [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) (Apache-2.0); no text is copied.
