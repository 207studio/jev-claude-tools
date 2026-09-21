# Output style A/B: can Claude answer "like Jev"?

**Result: no. Use the built-in `Concise` output style instead.** Both styles in this folder lost to it. They are kept as a negative result, not for use.

## Question

Jev returns a verdict and a calibrated probability, with no deliberation text. Could an output style make Claude answer the same way — verdict · confidence · evidence, no narration — and save tokens without losing accuracy?

## Setup

- Claude Code 2.1.278, `claude -p`, model `claude-sonnet-5`
- Read-only tools only (`Read`, `Grep`, `Glob`), on a copy of [ddfeyes/jev-mode](https://github.com/ddfeyes/jev-mode)
- Three code questions with answers verified in the source: what `text_tokens` measures, what happens to an oversized batch item, where the API key is read from
- Answers graded against those references by Jev (`grade.sh`)
- Styles: Claude Code's `default`, the built-in `Concise`, and two custom styles in this folder

## Results

| Style | Runs | Output tokens (mean) | vs default | Correct | Invented confidence numbers |
|---|---:|---:|---:|---:|---:|
| default | 6 | 1,498 | — | 6/6 | 0 |
| **Concise** (built-in) | 6 | **1,234** | **−18%** | **6/6** | 0 |
| [jev-v1](jev-v1.md) | 3 | 1,114 | −26% | **2/3** | 2 |
| [jev-v2](jev-v2.md) | 6 | 1,554 | +4% | 6/6 | 0 |

Per-run numbers are in [results.tsv](results.tsv).

## What went wrong with v1

v1 told Claude to give "the decision, not the deliberation" as `verdict · confidence · evidence`. On the oversized-item question it read the usage docs instead of the source, then answered:

> `unspecified · 0.85 · …` … The CLI source may handle oversized items differently. I haven't read it, so I can't say.

It stopped investigating early (5.3 turns on average, against 6.5–6.8 for the others) and attached 0.85 to an answer it said it hadn't checked.

**Claude isn't Jev.** Jev's number is a probability from a model trained to calibrate it. Ask Claude to write one and you get a plausible-looking number, and it makes a wrong answer look certain. For a calibrated judgment, call Jev.

## What happened with v2

v2 dropped the confidence number and added "if something that decides the answer is unchecked, check it first". It got 6/6 right and invented no numbers, but used 4% **more** output tokens than default. Fixing the accuracy problem also removed the saving.

## Caveats

One model, one repository, three questions, 3–6 runs per style. Treat the percentages as a data point, not a benchmark. We measured output tokens and correctness, not total session cost across long tasks.

## Reproduce

```sh
./run.sh        # round 1: default, Concise, Jev — needs a style named "Jev" in ~/.claude/output-styles/
./round2.sh     # round 2
./grade.sh      # grade every answer with jev-mode
```

The scripts run headless Claude Code sessions and spend your usage (about $0.15–0.20 per run on Sonnet).
