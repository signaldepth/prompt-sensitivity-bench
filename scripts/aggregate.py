"""Aggregate local experiment JSON into data/public/findings.json."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DEFAULT_EXPERIMENTS = DATA / "private" / "experiments"
DEFAULT_OUTPUT = DATA / "public" / "findings.json"
LEVELS = ["vague", "task_only", "task_io", "full_spec"]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def aggregate_specificity(experiments: Path) -> dict:
    per_level: dict[str, list[float]] = defaultdict(list)
    per_model: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    source_count = 0

    for path in sorted(experiments.glob("e9_specificity*.json")):
        data = load_json(path)
        if data.get("experiment") != "e9_specificity":
            continue
        source_count += 1
        for row in data.get("results", []):
            level = row.get("level")
            rate = row.get("avg_pass_rate")
            model = row.get("model_name") or row.get("model")
            if level in LEVELS and rate is not None and model:
                per_level[level].append(float(rate))
                per_model[str(model)][level].append(float(rate))

    return {
        "levels": {
            level: round(mean(values), 4)
            for level, values in per_level.items()
            if values
        },
        "models": {
            model: {
                level: round(mean(values), 4)
                for level, values in levels.items()
                if values
            }
            for model, levels in sorted(per_model.items())
        },
        "source_count": source_count,
    }


def aggregate_complexity(experiments: Path) -> dict:
    path = experiments / "e8_complexity.json"
    if not path.exists():
        return {}
    data = load_json(path)
    return {
        "calls": data.get("calls"),
        "hardware": data.get("hardware"),
        "models": data.get("results", {}),
        "source_count": 1,
    }


def aggregate_format(experiments: Path) -> dict:
    path = experiments / "e7_crossval.json"
    if not path.exists():
        return {}
    data = load_json(path)
    return {
        "overall": data.get("overall", {}),
        "models": data.get("format_results", {}),
        "source_count": 1,
    }


def aggregate_filler(experiments: Path) -> dict:
    path = experiments / "e4_compression.json"
    if not path.exists():
        return {}
    data = load_json(path)
    per_model: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in data.get("results", []):
        model = str(row.get("model"))
        variant = str(row.get("variant"))
        if variant in {"original", "compressed"}:
            per_model[model][variant].append(float(row.get("pass_rate", 0.0)))
    return {
        "models": {
            model: {
                variant: round(mean(values), 4)
                for variant, values in variants.items()
            }
            for model, variants in sorted(per_model.items())
        },
        "source_count": 1,
    }


def build_findings(experiments: Path) -> list[dict]:
    specificity = aggregate_specificity(experiments)
    complexity = aggregate_complexity(experiments)
    filler = aggregate_filler(experiments)
    fmt = aggregate_format(experiments)
    return [
        {
            "id": "specificity",
            "title": "Specificity dwarfs everything",
            "headline": "Vague to task plus input/output spec is the largest measured effect.",
            "data": specificity,
        },
        {
            "id": "complexity",
            "title": "Complexity hurts small models",
            "headline": "The smallest coder model drops sharply at maximal prompt complexity.",
            "data": complexity,
        },
        {
            "id": "filler",
            "title": "Filler words are load-bearing",
            "headline": "Compression hurts some small models on deterministic coding tasks.",
            "data": filler,
        },
        {
            "id": "format",
            "title": "Format preference is noise",
            "headline": "XML, Markdown, and plain text were indistinguishable in delimiter-only tests.",
            "data": fmt,
        },
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_EXPERIMENTS,
        help="Directory containing local or private experiment JSON files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path for the generated findings JSON.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    experiments = args.input_dir
    if not experiments.exists():
        raise SystemExit(
            f"input directory not found: {experiments}. "
            "Pass --input-dir to point at your local/private experiment archive."
        )

    findings = build_findings(experiments)
    out = args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(findings, indent=2, ensure_ascii=False))
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
