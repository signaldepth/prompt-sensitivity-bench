# Contribute A Run

If you can run a model that is missing from the dataset, submit one benchmark run and get credited in the data.

## Run E9 Specificity

```bash
git clone https://github.com/signaldepth/prompt-sensitivity-bench.git
cd prompt-sensitivity-bench/harness
uv venv
uv pip install -e ".[dev]"
uv run python validate.py e9 --model-name <model-name> --host http://localhost:11434 --k 3
```

The result is written to `.output/experiments/`.

## Validate

```bash
uv run python ../scripts/validate_contribution.py .output/experiments/<file>.json
```

The public repo validates contribution shape and public artifact shape separately. Maintainers merge selected results into derived public findings; raw run dumps do not get committed automatically.

## Other Public Experiments

The harness now also exposes:

```bash
uv run python validate.py e7 --model-name <model-name> --host http://localhost:11434 --k 3
uv run python validate.py e8 --model-name <model-name> --host http://localhost:11434 --k 3
```

Those experiments are public and runnable, but the lightweight public contribution path is still E9-first until the intake policy and fixtures for the other families are tightened.

## Submit

Open a GitHub issue with the JSON file pasted into the template, or attach/link a gist if it is large. Maintainers review submissions and fold selected results into derived findings; raw run dumps are not automatically committed to the public repo.

For a minimal valid shape, see `data/examples/e9_specificity_fixture.json`.

## Requirements

- `k >= 3`
- temperature specified
- model name and hardware specified
- no private data in notes or outputs
