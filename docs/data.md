# Data

This repo publishes derived findings, schemas, model metadata, and a minimal public fixture.

The current `data/public/*.json` files are derived summaries generated from local/private raw run archives. The public repo includes those summaries, the benchmark machinery, and the validation rules, but it does not publish the full raw per-trial dumps by default.

Public artifacts:

- `data/public/findings.json`
- `data/public/models.json`
- `data/public/contributors.json`
- `data/schemas/*.json`
- `data/examples/e9_specificity_fixture.json`

Full raw experiment archives are not published by default. Keep local or private run files under `data/private/experiments/`, which is gitignored.

To regenerate the public findings from your own local/private run set:

```bash
uv run python scripts/aggregate.py --input-dir data/private/experiments
```

Then refresh the public charts:

```bash
uv run python scripts/plot.py
```

Validate the tracked public artifacts before a push:

```bash
uv run python scripts/validate_public_data.py
```

`data/public/models.json` now carries the canonical model id plus runtime, measurement hardware, known run dates, and aliases when the raw archive used older short names.

## Licenses

Code is MIT. Data is CC-BY-4.0.
