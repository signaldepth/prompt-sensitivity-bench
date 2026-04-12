# Format Preference Is Noise

Across the archived delimiter-only format test, XML, Markdown, and plain text produced indistinguishable aggregate pass rates.

## Key Numbers

| Format | Aggregate pass rate |
|---|---:|
| XML | 0.80 |
| Markdown | 0.80 |
| Plain text | 0.83 |

## Data

- Derived summary: `data/public/findings.json`

The published summary is derived from a local/private archived run, not from a checked-in raw experiment dump.

## Public Runner

```bash
cd harness
uv run python validate.py e7 --model-name qwen2.5-coder:1.5b --k 3
```

The public `e7` command runs a comparable delimiter-only format sweep for the same finding class. Use it to test your own model or archive, not as a byte-for-byte replay of the archived local run behind the published chart.

## Sample Counts

- 1 archived E7 run
- 4 local models
- 3 delimiter formats
- 96 scored calls

## Uncertainty Notes

This zero-signal result applies to delimiter-only coding prompts in one archived run. It does not claim that XML, Markdown, and plain text remain equivalent once prompts include multi-block context, examples, or tool metadata.

## Limitations

This finding tests delimiter-only formatting on coding tasks. It does not test multi-block prompts where XML or another container format separates examples, context, and instructions.
