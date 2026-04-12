# Signal Depth

## Making prompts longer did not help. Making the task contract explicit did.

On the current E15 context-budget sweep:

- `short_sparse = 0.25`
- `long_sparse = 0.25`
- `short_dense = 1.00`
- `long_dense = 1.00`

Deterministic Python code tasks, 4 local-model runs, `k=3`, temperature `0.0`.

[:octicons-graph-16: See The E15 Result](findings/context-budget.md){ .md-button .md-button--primary }
[:octicons-beaker-16: Methodology](methodology.md){ .md-button }
[:octicons-mark-github-16: Repo](https://github.com/signaldepth/prompt-sensitivity-bench){ .md-button }

![Context budget by model](assets/charts/context-budget.svg)

## At A Glance

| Models | Tasks | Graded calls | Repeats | Public harness | Raw archive policy |
|---:|---:|---:|---:|---|---|
| 4 | 4 | 192 | `k=3` | Source-complete for E15 | Derived findings public, raw runs local/private by default |

## Why This Matters

This benchmark is trying to separate failure modes that usually get blurred together.

On this task family, adding words without adding contract information did nothing. Making the task contract explicit fully recovered the measured runs. That is a different diagnosis from "the prompt was too short" or "the model needs a larger context window."

The strongest earlier public result is still [Specificity](findings/specificity.md): across 12 aggregated E9 run archives, moving from a vague prompt to a task plus input/output spec raised average pass rate from 9% to 95%.

## What This Is

Signal Depth is a versioned benchmark for prompt sensitivity. It measures how much model behavior changes when the prompt changes.

Each finding links to the public summary, the task definitions, and the command needed either to reproduce the measurement where the public runner is source-complete or to rerun a comparable public experiment for the same finding class.

The current public findings are derived from local/private raw run archives. The public repo publishes the aggregated artifacts, schemas, plots, and harness code by default rather than the full raw dump history.

## What This Is Not

This is not a capability leaderboard. LMArena, Artificial Analysis, HELM, LiveBench, and coding leaderboards already measure model strength.

This is not a universal long-context claim. The current E15 result is about deterministic Python code tasks, not retrieval, document synthesis, or multi-turn chat.

This is not a benchmark submission portal or a product marketing page.

## Current Findings

| Finding | Headline |
|---|---|
| [Context budget](findings/context-budget.md) | Longer prompts did not help when the task contract stayed sparse. |
| [Specificity](findings/specificity.md) | Vague prompts fail; input/output specs create the largest measured jump. |
| [Complexity](findings/complexity.md) | More prompt detail can hurt small models. |
| [Filler words](findings/filler.md) | Text humans treat as filler can be structure for small models. |
| [Format preference](findings/format.md) | XML, Markdown, and plain text were indistinguishable in delimiter-only coding tests. |
| [k=1 trap](findings/k1-trap.md) | Single-shot measurements can reverse conclusions on boundary models. |
| [DeMorgan inversion](findings/demorgan.md) | One phrasing caused a deterministic logic inversion on llama3.1:8b. |
