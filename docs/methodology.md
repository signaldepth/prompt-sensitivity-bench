# Methodology

The benchmark uses deterministic programming tasks with executable tests. A model receives a prompt, returns Python code, and the harness runs the generated function against fixed test cases.

## Public Evidence Model

Signal Depth publishes the benchmark method, schemas, plotting code, and derived findings by default. The current public `data/public/*.json` artifacts are generated from local/private raw run archives that stay outside the tracked repo unless they are explicitly curated for release.

This means the public site is reproducible at the method and aggregation layer, while the per-trial raw dumps remain local/private for now. Finding pages should say when a result comes from a private archived run rather than a checked-in raw file, and when a public command is a comparable rerun of the same experiment class rather than a byte-for-byte replay of the archived runner.

## Current Task Set

- fizzbuzz
- reverse_words
- flatten
- two_sum
- run_length_encode
- chunk_list

## Sampling

The default is `k=3` per condition. Single-shot measurements are not accepted for contributed runs because boundary models can flip conclusions between k=1 and repeated trials.

## Temperature

The default temperature is `0.0` to isolate prompt effects from sampling variance.

## Evaluation

The harness extracts a Python function from the model response, executes it in a subprocess, and compares the printed representation of the result with the expected value.

## Current Public Findings

The published summaries currently combine:

- E9 specificity aggregates generated from 12 local/private run archives
- four archived E15 context-budget runs
- one archived E8 complexity run
- one archived E7 format run
- one archived E4 compression run

The public repo exposes the derived summaries and public rerun tooling for those experiment families, not the full raw archive itself. In the current public repo, E9 and E15 are source-complete, E7/E8 are published as comparable public experiment classes, and E4 remains summary-first until its compression layer is published independently.

## Scope

In scope: prompt specificity, delimiter format, prompt complexity, prompt density versus length, compression sensitivity, and deterministic coding tasks.

Out of scope: human preference, safety evaluation, multi-turn chat dynamics, image/audio tasks, and general capability ranking.

## Limitations

- Most currently published findings are derived from private/local archived runs rather than raw per-trial dumps committed to the repo.
- The current site reports point estimates and source counts, not confidence intervals.
- Experiment family coverage is still uneven: E9 and E15 are source-complete in the public repo, E7/E8 are runnable as comparable public sweeps, and E4 is still summary-first while the older archived families catch up.
