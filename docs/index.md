# Prompt Sensitivity Bench

An open benchmark measuring how prompt wording changes model outputs across the model size spectrum.

The largest measured effect so far is specificity. On 1-4B local models, moving from a vague prompt to a task plus input/output spec raised pass rate from 8% to 82%.

[:octicons-graph-16: Findings](findings/specificity.md){ .md-button .md-button--primary }
[:octicons-beaker-16: Methodology](methodology.md){ .md-button }
[:octicons-database-16: Data](data.md){ .md-button }
[:octicons-git-pull-request-16: Contribute](contribute.md){ .md-button }

## What This Is

This is a versioned benchmark with derived prompt sensitivity findings. Each finding links to the public summary, the task definitions, and the command needed to reproduce or extend the measurement on your own run archive.

## What This Is Not

This is not a capability leaderboard. LMArena, Artificial Analysis, HELM, LiveBench, and coding leaderboards already measure model strength. This project measures how much model behavior changes when the prompt changes.

This is not a product page. It is not an evaluation framework. It is not a benchmark submission tracker.

## Current Findings

| Finding | Headline |
|---|---|
| [Specificity](findings/specificity.md) | Vague prompts fail; input/output specs create the largest measured jump. |
| [Complexity](findings/complexity.md) | More prompt detail can hurt small models. |
| [Filler words](findings/filler.md) | Text humans treat as filler can be structure for small models. |
| [Format preference](findings/format.md) | XML, Markdown, and plain text were indistinguishable in delimiter-only coding tests. |
| [k=1 trap](findings/k1-trap.md) | Single-shot measurements can reverse conclusions on boundary models. |
| [DeMorgan inversion](findings/demorgan.md) | One phrasing caused a deterministic logic inversion on llama3.1:8b. |
