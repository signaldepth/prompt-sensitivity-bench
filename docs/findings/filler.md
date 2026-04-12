# Filler Words Are Load-Bearing

On qwen2.5-coder:1.5b, compressing verbose prompts dropped average pass rate from roughly 0.89 to 0.28 across the archived compression experiment.

![Compression sensitivity](../assets/charts/filler.svg)

## Key Numbers

| Model | Original | Compressed | Direction |
|---|---:|---:|---|
| qwen2.5-coder:1.5b | 0.89 | 0.28 | Compression hurt |
| gemma3:1b | 0.94 | 0.94 | Flat in this archive |

The destructive cases were not whitespace cleanup. They came from phrase simplification and filler deletion, where wording that looks redundant to humans appears to help small models keep task structure.

## Reproduce

The public repo ships the derived summary in `data/public/findings.json`. The contribution harness currently supports E9 first; a standalone public E4 runner is deferred until the compression layer is published as an independent public implementation.

The published summary is derived from a local/private archived run, not from a checked-in raw experiment dump.

## Sample Counts

- 1 archived E4 run
- 2 models
- 6 tasks
- 2 prompt variants
- 24 task/variant rows

## Uncertainty Notes

This archive records aggregated task/variant pass rates, not a normalized top-level call count like E7 and E8. Interpret the result as a strong within-archive contrast on small models, not as a claim that compression always hurts.

## Limitations

This finding is model-dependent. It should not be summarized as "compression hurts" or "compression helps" without naming the model size and task family.
