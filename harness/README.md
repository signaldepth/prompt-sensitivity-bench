# Harness

This directory is the canonical home of the prompt sensitivity benchmark harness.

The initial public harness supports E9 specificity runs for external contributors.

```bash
uv run python validate.py e9 --model-name qwen2.5-coder:1.5b --host http://localhost:11434 --k 3
```

Results are written to `.output/experiments/` from the repository root.
