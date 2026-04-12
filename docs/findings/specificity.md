# Specificity Dwarfs Everything

Across the 12 currently aggregated E9 run archives, moving a prompt from vague to task plus input/output spec raised average pass rate from 9% to 95%.

![Specificity gradient](../assets/charts/specificity.svg)

## Key Numbers

| Prompt level | Average pass rate | Notes |
|---|---:|---|
| vague | 0.09 | Task name only |
| task_only | 0.46 | The task is stated, but shape is missing |
| task_io | 0.95 | Input/output shape and one example |
| full_spec | 0.97 | Adds constraints and edge cases |

The jump from task_only to task_io is the cliff. More detail after that helps much less on the current task set.

## Reproduce

```bash
cd harness
uv run python validate.py e9 --model-name qwen2.5-coder:1.5b --k 3
```

## Data

- Public fixture: `data/examples/e9_specificity_fixture.json`
- Aggregated finding: `data/public/findings.json`
- Task definitions: `harness/data.py`

The full raw run archive for this finding is curated privately; the public repo ships the derived summary, plotting code, and fixture instead of the per-trial dumps.

## Sample Counts

- 12 archived E9 run files
- 12 models
- 4 tasks
- 48 task-model rows per prompt level
- 576 total graded calls
- `k=3` per condition

## Uncertainty Notes

The headline numbers are point estimates averaged across task-model rows from the archived runs. The site does not yet publish confidence intervals, and the archive is still limited to deterministic Python coding tasks rather than open-ended or multi-turn workloads.

## Limitations

The task set is deterministic Python coding tasks. This finding does not claim the same effect size for open-ended writing, long-context retrieval, or multi-turn conversations.
