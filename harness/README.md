# Harness

This directory is the canonical home of the prompt sensitivity benchmark harness.

The public harness currently exposes:

- `e7` — delimiter-only format comparison
- `e8` — prompt complexity sweep
- `e9` — specificity gradient
- `e15` — experimental context-budget decomposition (`length x density`)

External contribution intake is still `e9`-first. `e7` and `e8` are public and runnable now, but the lightweight public submission/validation path is still centered on E9 while the broader intake policy catches up. For the archived format and complexity findings, these public commands are comparable public sweeps rather than byte-for-byte replays of the original private runners.

```bash
uv run python validate.py e7 --model-name qwen2.5-coder:1.5b --host http://localhost:11434 --k 3
uv run python validate.py e8 --model-name qwen2.5-coder:1.5b --host http://localhost:11434 --k 3
uv run python validate.py e9 --model-name qwen2.5-coder:1.5b --host http://localhost:11434 --k 3
uv run python validate.py e15 --model-name qwen2.5-coder:1.5b --host http://localhost:11434 --k 3
uv run python validate.py e15 --model-name gemma4:26b --host http://localhost:11434 --k 1 --timeout 90 --progress --tasks fizzbuzz,two_sum
```

Results are written to `.output/experiments/` from the repository root. New runs also keep test-level trial artifacts for failed generations so future failure-taxonomy analysis can separate syntax, runtime, type, and likely edge-case failures instead of only tracking aggregate `pass_rate`.

For exploratory or operational diagnosis, `e15` also supports `--timeout`, `--progress`, `--tasks`, and `--conditions` so you can probe a smaller subset before committing to a full comparative run.
