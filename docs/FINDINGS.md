# Findings

What we measured or hit while setting this up. One machine, one person's workflow, September 2026. Treat the numbers as a data point, not a benchmark.

## 1. Where the context actually went

One Claude Code session, 268k tokens used out of 1M:

| Category | Tokens | Share of used |
|---|---:|---:|
| Messages (conversation + tool output) | 206,320 | 77% |
| System tools | 24,523 | 9% |
| MCP tools | 21,692 | 8% |
| Skills | 9,962 | 3.7% |
| System prompt | 5,260 | 2% |

Removing **every** MCP server and **every** skill would have saved about 12%. Deferred tool loading was already keeping MCP definitions small. So we stopped pruning skills and MCP servers and aimed at tool output instead: output limits in `CLAUDE.md`, delegating broad searches to subagents, compaction, and filtering search results before they enter context.

This also changed how we judged new skills. We swept 101 third-party Jev skills from 63 repositories. Installing the 41 that passed a risk screen would have added roughly 22,500 tokens to every session, more than tripling the skill cost, for skills that mostly duplicated what we had.

## 2. `model: inherit` makes multi-agent runs expensive

All five of our agent definitions had `model: inherit`. With a Fable 5.1 parent, every subagent ran on Fable 5.1, so a multi-agent workflow multiplied the parent's price by the number of agents.

We had Jev read each role definition and pick the minimum tier with `config/agent-tier.json`:

| Role | Tier | Confidence |
|---|---|---|
| game designer | opus | 0.91 |
| engine implementer | sonnet | 0.98 |
| harness librarian | sonnet | 1.00 (second pass; first pass was 0.43) |
| art director | sonnet | 0.71 |
| playtester | sonnet | 0.70 |

The low first-pass confidence on one role is the point of checking confidence: we asked again with sharper criteria instead of accepting it.

We did this statically in the agent frontmatter. No proxy. We found three projects that route subagents through a proxy between Claude Code and the API; all had 0–1 stars, and one had no license at all. A proxy there sees every request and your API key.

**`subagent_type: "fork"` ignores `model`.** Forks always use the parent model, so explicit tiers don't help if you fork a lot from an expensive parent.

## 3. `text_tokens` is not a measurement of context inflow

`jev-mode batch` reports `text_tokens`. In v1.2.0 it is `sum(estimate_tokens(item_text))`: an estimate of the input records' size. It grows with the number of items even when not one line of raw text reaches the agent. We first described it as a gauge of what entered context; that was wrong, and the Codex-side port caught it. Compare against a control run of the same task if you want the real saving.

## 4. pip 21.x installs an empty package without an error

On macOS, Xcode's bundled Python 3.9 ships pip 21.2.4. It can't read PEP 621 `[project]` metadata. Given such a package it prints:

```
Successfully built UNKNOWN
Successfully installed UNKNOWN-0.0.0
```

and installs a `dist-info` directory with **no module and no console script**. Check with `python3 -c "import <module>"` and `which <command>`, not the success message. `pip3 show UNKNOWN` returning anything is the tell.

## 5. `jev-router` ships a `jev-codex` binary

`npm i -g jev-router` installs three commands: `jev-claude`, `jev-codex` and `jev-explain`. If you already have a different `jev-codex` on your `PATH` (jev-codex-tools has one), installing into the same prefix overwrites it. We installed jev-router into its own prefix and linked only `jev-claude` and `jev-explain`.

## 6. Unattended scheduled tasks stall on permission prompts

Our weekly sweep task stopped for 24 hours at the first shell command that needed approval; nobody was there to approve it. We moved every mechanical step into one script (`scripts/weekly-sweep.sh`) so the task needs a single approval, and we run it once by hand so the approval is stored.

## 7. Subagents don't see host hooks

This one is not ours. The jev-mode author observed on Codex that subagent sessions received no pre-action hooks at all: 339 sessions, 29,146 tool calls, zero hook invocations. We haven't measured it on Claude Code and don't assume it transfers. It's still a reason to give subagents narrow work and check their results afterwards, instead of trusting a hook to have covered them.
