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

## 8. Subagents follow required output fields, not prose

Another session of ours ran the same defect-fix workflow three times on an iPad app repository. The first two told subagents in prose to use Jev first; measured Jev calls were 0–1. The third added one **required** field to the subagent's structured-output schema, holding the verbatim output of a `jevq.py claim` call. All 36 items came back with it filled — no blanks, no `ERROR`.

Three runs in one session, so treat it as a reproduced observation, not a law. The rule we took from it: don't ask a subagent to use a tool; require a field only that tool's output can fill, and have the parent check its format in code. A self-reported "checked with Jev: true" doesn't count — it can be filled without calling anything. Example schema and parent-side check in [`skills/jev-mode/references/delegation.md`](../skills/jev-mode/references/delegation.md).

That same session reused one repository-sweep recipe three times: 813 chunks → 282 after the first Jev pass → 117 after the second → 17 clusters assigned to reviewers. Reviewers read about 14% of the chunks. That is chunks not read, not a measured token saving. The recipe, both question sets and the exact scoring formula are in [`skills/jev-code-sweep`](../skills/jev-code-sweep).

Its two helper scripts had been rewritten from scratch three times that day. The cause was one hard-coded worktree path; they now find the repository root from git.

## 9. `jev-ios` runs on Claude Code once serve-sim is started

`jev-ios` needs a running, registered serve-sim 0.1.46. On Codex a plugin starts it; Claude Code had nothing that did, so we first recorded `jev-ios` as unusable there. serve-sim is just an npm package, though, and `scripts/serve-sim.sh` starts it.

Verified on a throwaway iPhone 15 / iOS 27.0 simulator, deleted afterwards: Jev chose the right Settings row out of four at 0.96, the tap navigated, and the run ended `status: done`.

The first live run found a bug our guard-path tests had missed. The launcher read serve-sim's boolean `running` flag as if it were a list, and reported "not registered" while the server was up. Test the success path, not only the refusals.

Things that made a correct run look like a failure:

- **Calling it right after the app launches.** The accessibility tree was still empty, so it stopped with `steps: 0`. It observes once; it doesn't wait for the UI.
- **Labels in the wrong language.** A simulator created on a Korean Mac has Korean labels; English `--element` values matched nothing. Some labels contain a non-breaking space (`\xa0`). Copy labels from the `/ax` output.
- **No `--done-label`.** A successful tap still reported `stopped` / `observation_or_provider_failed`, because the new screen had none of the allowed elements. Pass a done label that exists **only** on the destination screen; one that's also on the starting screen can end the run before it taps.
- **Reading `E3` as your third `--element`.** Candidate ids follow sorted element ids, not your argument order. Confirm the choice by the screen you land on.

`jev-ios` reads accessibility through serve-sim's own endpoint. That is a different path from Claude Code's native simulator `inspect`, which in the other session failed persistently on one app. `jev-ios` might work where `inspect` didn't; we haven't tested that app.

## 10. Don't make Claude imitate Jev — use the built-in Concise style

We wanted replies with no think-aloud: a verdict and nothing else, like Jev. The popular terse-output projects report modest effects on output tokens (caveman's skill alone: −8.5% across 86 tasks; claude-token-efficient: −4 to −12%). Claude Code's built-in `Concise` output style already skips preamble and narration. So we tested whether a Jev-shaped custom style could beat it.

It couldn't. Across three code questions on Sonnet, `Concise` cut output tokens 18% against the default style with every answer correct. Our first style, which asked for `verdict · confidence · evidence`, stopped investigating early. It gave one wrong answer, attaching a confidence of 0.85 to a conclusion it admitted it hadn't checked. The second version fixed accuracy and lost the saving (+4%).

A confidence number from Jev is a calibrated probability. One Claude writes because a format asks for it is decoration, and it makes wrong answers look certain. Get calibrated judgments from Jev. Get shorter replies from `Concise`. Full method and numbers in [`experiments/output-style-ab`](../experiments/output-style-ab).
