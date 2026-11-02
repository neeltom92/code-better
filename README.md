# code-better

A single Claude Code skill for senior engineers. It merges [obra/superpowers](https://github.com/obra/superpowers) and [bmtrnavsky/disciplined-vibe-coding](https://github.com/bmtrnavsky/disciplined-vibe-coding) into one gated pipeline:

```text
Gate --> Plan --> Teardown --> Build (test-first, debug) --> Verify --> Commit
```

- **Gate**: understand the code, then declare a stakes tier (`sandbox` / `internal` / `prod`) and a scope rung (`one-liner` / `micro` / `full` / `project`). The rung sets how much process the later stages get.
- **Plan**: steps with check commands, reuse first, and a rollback line for every destructive step. Adds dry-run, idempotency, metric bands, and a kill-switch when relevant.
- **Teardown**: cold review of the plan before any code exists. Two passes at `micro`; five rounds by a fresh subagent at `full` and above.
- **Build**: lazy ladder (reuse, then stdlib, then minimum code), red-green TDD, `terraform plan` / `helm diff` as the failing check for infra, root-cause debugging with a 2-failed-fixes stop.
- **Verify**: fresh evidence by class (terminal, user-attested, integrity, metric). A near-miss is a fail. Drift is checked against the plan.
- **Commit**: only when asked. Secret scan the staged diff first. One logical change per commit.

A failed gate blocks the next stage unless the user explicitly bypasses it, and the bypass is stated.

## Install

```bash
git clone https://github.com/neeltom92/code-better
ln -s "$PWD/code-better/skills/code-better" ~/.claude/skills/code-better   # all projects
# or, for one repo only:
mkdir -p <repo>/.claude/skills && cp -R code-better/skills/code-better <repo>/.claude/skills/
```

Start a new `claude` session. If you also have the superpowers, caveman, or ponytail plugins enabled, disable them with `/plugin`; they inject overlapping rules.

## Use

In any repo, invoke it directly or let it trigger on coding tasks:

```text
/code-better add rate limiting to POST /login
/code-better CI is failing on the integration job since yesterday
```

At `full` and `project` rung it writes plans and session state under `.pipeline/` (formats in `skills/code-better/references/templates.md`). Commit that directory or add it to `.gitignore`.

## Layout

```text
skills/code-better/SKILL.md                  the skill
skills/code-better/references/templates.md   plan file and session-state formats
CLAUDE.md                                    editing rules for this repo
```

## Credits

Built on obra/superpowers (MIT, Jesse Vincent) and bmtrnavsky/disciplined-vibe-coding (MIT, Brad Trnavsky), with ideas from the ponytail and caveman Claude Code plugins.
