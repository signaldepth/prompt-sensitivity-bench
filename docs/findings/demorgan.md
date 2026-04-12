# DeMorgan Inversion On llama3.1:8b

On fizzbuzz, llama3.1:8b passed task_only and full_spec prompts but failed the task_io phrasing.

## Key Numbers

| Prompt level | Pass rate | Failure mode |
|---|---:|---|
| task_only | 1.00 | Canonical template |
| task_io | 0.33 | Natural-language "otherwise" phrasing triggered an inverted condition |
| full_spec | 1.00 | Explicit "check divisibility by 15 first" recovered |

## Why It Matters

More specificity is not always monotonically better. Overlapping rule systems need evaluation-order constraints, not only examples.

## Sample Counts

- 1 model
- 1 task
- 3 prompt levels shown
- `k=3` per level

## Uncertainty Notes

This is a single-model, single-task failure mode. It is useful because the behavior was deterministic in the archive, but it should be read as a concrete counterexample rather than a broad population claim.
