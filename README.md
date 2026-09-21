# Jev Claude Tools

Experimental, opt-in **Claude Code** skills and configuration from **207 Studio** that use TypeSafe Jev for bounded decisions. The Claude Code companion to [jev-codex-tools](https://github.com/207studio/jev-codex-tools).

The idea is the same on both sides: code gathers observations and executes permitted actions; Jev selects from a finite set of choices. Judgments that never need to be read as text stay as judgments, and don't get pasted into the model's context.

**This repository does not establish a general token-saving percentage.** It records one measured context breakdown and several concrete failure modes we hit (see [findings](docs/FINDINGS.md)). It does not replace Claude Code's compaction, permission system, or model choice.

Independent community project. Not an official Anthropic or TypeSafe product. Jev is an external service with its own terms and pricing.

## What's included

| Path | What it is | Boundary |
|---|---|---|
| `skills/jev-mode` | Batch 5+ fixed-label judgments without loading record text into context | Needs [ddfeyes/jev-mode](https://github.com/ddfeyes/jev-mode) CLI. Not for prose, code, arithmetic, counting, or date comparison |
| `skills/jev-code-search` | Broad relevance search where ripgrep candidates are filtered by Jev **before** they enter context | Needs the `jev_context` MCP server from jev-codex-tools |
| `skills/jev-verify` | Decide whether an optional repeated verification is worth running | Never skips a required check; a SKIP means "not run", not "passed" |
| `skills/jev-action-control` | Delegate explicitly allowed repeated browser / macOS / iOS actions to bounded Jev choices. On iOS, runs `jev-ios` through `scripts/serve-sim.sh` | Stops on low confidence, stale state, or permission denial |
| `skills/jev-code-sweep` | Sweep a whole repository for likely defects: Jev triages every ~100-line chunk before any agent reads code, and only the top clusters go to reviewers | Triage only. Fixes come from reviewers who read the actual code |
| `config/agent-tier.json` | A Jev `choice` question that picks haiku / sonnet / opus for a subagent role | You own the policy; Jev only supplies the judgment |
| `templates/CLAUDE.md` | The user-scope policy we run, as a worked example to adapt | Paths generalized to `~` |
| `scripts/jevq.py` | Ask Jev a yes/no about a line range, or check a reviewer's claim against the code around a line. Prints one line; never prints code | Refuses ranges over 220 lines. Low confidence becomes `UNSURE` |
| `scripts/chunk.py` | Split git-tracked source into ~100-line JSONL records for `jev-mode batch` | Prints counts only |
| `scripts/serve-sim.sh` | Start, locate and stop the [serve-sim](https://github.com/EvanBacon/serve-sim) helper that `jev-ios` needs | Binds 127.0.0.1 only; won't touch a simulator another task already serves; won't stop without a UDID |
| `scripts/weekly-sweep.sh` | One-command health check + GitHub sweep for an unattended weekly task | Read-only. Installs nothing |
| `scripts/register-jev-context-mcp.sh` | Registers the `jev_context` MCP server at user scope | Keeps its metrics directory separate from Codex's |

The skills use **progressive disclosure**: a short `SKILL.md` (~700–900 bytes) that points to `references/*.md`, read only when the detail is actually needed. They were written in Codex first and ported here with wording changes only.

## Requirements

- Claude Code 2.1.274+ if you also use function-hook plugins
- The CLIs from [jev-codex-tools](https://github.com/207studio/jev-codex-tools) on your `PATH` (`jev-judge`, `jev-verify`, …) — the skills call them
- A TypeSafe API key in an env file, never in a prompt or a committed file
- Node.js 20+; Python 3.8+ for `jev-mode`

## Install

```sh
git clone https://github.com/207studio/jev-claude-tools
cp -R jev-claude-tools/skills/* ~/.claude/skills/
mkdir -p ~/.claude/jev
cp jev-claude-tools/config/agent-tier.json jev-claude-tools/scripts/{jevq.py,chunk.py,serve-sim.sh} ~/.claude/jev/
```

The skills call these by their `~/.claude/jev/` paths.

For iOS: `jev-ios` (from jev-codex-tools) accepts only serve-sim **0.1.46**. `serve-sim.sh` looks for it in the npx cache path jev-ios expects; if yours is elsewhere, set `JEV_SERVE_SIM` to its `dist/serve-sim.js`. Run `npx --yes serve-sim@0.1.46 --version` once to populate the cache.

Read `templates/CLAUDE.md` and take what fits — don't copy it wholesale; it names our own paths and projects.

**Don't `pip install` jev-mode on a machine with an old pip.** pip 21.x cannot read PEP 621 metadata, prints `Successfully installed UNKNOWN-0.0.0`, and installs a package with no code. Clone it and run it with `PYTHONPATH=src` instead. Details in [findings](docs/FINDINGS.md).

## The finding most people will want

If you run multi-agent workflows on an expensive parent model, check your agent definitions for `model: inherit`. Every subagent then runs on the parent's model. We found all five of ours set that way, which is what made a Fable 5.1 multi-agent run so costly. Setting explicit tiers fixed it without any proxy. `subagent_type: "fork"` ignores `model` entirely and always uses the parent.

## Want shorter replies? Use the built-in Concise style

We tried to make Claude answer "like Jev", as a verdict with a confidence number and no narration. It backfired. Claude stopped investigating early and attached a confidence of 0.85 to a wrong answer it hadn't checked. Claude Code's built-in `Concise` output style did better: 18% fewer output tokens than the default style, every answer correct.

```sh
/output-style concise
```

For a calibrated confidence, call Jev; don't ask Claude to write one. Method and numbers: [experiments/output-style-ab](experiments/output-style-ab).

## Related projects

See [THIRD_PARTY.md](THIRD_PARTY.md). In short: [fast-jev-compaction](https://github.com/tamaratran/fast-jev-compaction), [jev-router](https://github.com/gargpratyush/jev-router) and [jevprune](https://github.com/ibrahemid/jevprune) are separate projects we use alongside these skills. They are not bundled.

## License

MIT. See [LICENSE](LICENSE). The `jev-mode` skill's reference file adapts guidance from [ddfeyes/jev-mode](https://github.com/ddfeyes/jev-mode) (MIT).
