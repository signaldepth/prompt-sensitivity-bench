# Prompt Sensitivity Bench

An open benchmark and derived findings set for measuring how prompt wording changes LLM outputs across local and frontier models.

This repository contains:

- the benchmark harness
- structured finding summaries and model metadata
- public schemas and a minimal contribution fixture
- static charts
- the documentation site published at `https://signaldepth.ai/`

## Scope

This is not a capability leaderboard. It measures sensitivity to prompt wording, format, complexity, compression, and sampling choices on deterministic programming tasks.

## Open-Source Boundary

Public by default:

- benchmark harness and task definitions
- prompt templates needed for reproducibility
- schemas, validators, and aggregation/plotting scripts
- derived findings, model metadata, charts, and minimal fixtures
- methodology and contribution docs

Private by default:

- full raw run archives
- per-trial model outputs beyond small public fixtures
- checkpoint dumps, scratch exports, and migration leftovers
- internal launch notes and `.local/` working context

## Repo Layout

- `harness/` - executable benchmark harness and task definitions
- `scripts/` - aggregation, plotting, validation, and repo-safety checks
- `data/public/` - publishable derived JSON artifacts
- `data/examples/` - minimal public fixtures for contributors and tests
- `data/schemas/` - public JSON schemas
- `data/private/` - local/private raw archives, gitignored
- `docs/` - MkDocs site content
- `.local/` - maintainer-only notes, gitignored

## Local Development

```bash
uv venv
uv pip install -e ".[dev]"
uv run python scripts/check_public_repo.py
uv run python scripts/plot.py
uv run mkdocs serve
```

If you have a local or private run archive, place it under `data/private/experiments/` or point the aggregator at another directory:

```bash
uv run python scripts/aggregate.py --input-dir /path/to/private/experiments
uv run python scripts/plot.py
```

## License

Code is MIT licensed. Data is CC-BY-4.0; see `data/LICENSE`.
