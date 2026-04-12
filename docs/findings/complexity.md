# Complexity Hurts Small Models

On qwen2.5-coder:1.5b, increasing prompt complexity from minimal to maximal dropped pass rate from 0.78 to 0.28.

![Complexity by model](../assets/charts/complexity.svg)

## Key Numbers

| Model | minimal | role + constraints | examples | maximal |
|---|---:|---:|---:|---:|
| qwen2.5-coder:1.5b | 0.78 | 0.94 | 0.83 | 0.28 |
| gemma3:1b | 0.94 | 0.94 | 0.83 | 0.83 |
| phi4-mini | 0.89 | 0.94 | 0.72 | 0.94 |
| gemma3:4b | 0.94 | 0.94 | 0.94 | 0.94 |

The strongest negative effect appears on the smallest coder model. Larger tested models were mostly flat.

## Reproduce

The public repo ships the derived summary in `data/public/findings.json`. The contribution harness currently supports E9 first; E8 reproduction commands will be promoted after the harness migration is complete.

## Limitations

Complexity is represented as four discrete prompt templates, not a continuous scale. The result should be read as a capacity warning for small models, not a universal rule to make every prompt shorter.
