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
E15_CONDITIONS = ["short_sparse", "long_sparse", "short_dense", "long_dense"]
MODEL_ALIASES = {
    "qcoder": "qwen2.5-coder:1.5b",
    "gemma1b": "gemma3:1b",
    "phi4-mini": "phi4-mini:latest",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def normalize_model_name(name: str | None) -> str | None:
    if not name:
        return None
    return MODEL_ALIASES.get(name, name)


def aggregate_specificity(experiments: Path) -> dict:
    per_level: dict[str, list[float]] = defaultdict(list)
    per_model: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    task_names: set[str] = set()
    source_count = 0
    total_calls = 0

    for path in sorted(experiments.glob("e9_specificity*.json")):
        data = load_json(path)
        if data.get("experiment") != "e9_specificity":
            continue
        source_count += 1
        total_calls += int(data.get("total_calls", 0))
        for row in data.get("results", []):
            level = row.get("level")
            rate = row.get("avg_pass_rate")
            model = normalize_model_name(row.get("model_name") or row.get("model"))
            task = row.get("task")
            if level in LEVELS and rate is not None and model:
                per_level[level].append(float(rate))
                per_model[str(model)][level].append(float(rate))
                if task:
                    task_names.add(str(task))

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
        "sample_counts": {
            "source_archives": source_count,
            "model_count": len(per_model),
            "task_count": len(task_names),
            "rows_per_level": len(next(iter(per_level.values()))) if per_level else 0,
            "total_rows": sum(len(values) for values in per_level.values()),
            "calls_per_level": total_calls // len(LEVELS) if total_calls else 0,
            "total_calls": total_calls,
            "k": 3,
        },
    }


def aggregate_complexity(experiments: Path) -> dict:
    path = experiments / "e8_complexity.json"
    if not path.exists():
        return {}
    data = load_json(path)
    models = {
        normalize_model_name(model): values
        for model, values in data.get("results", {}).items()
    }
    return {
        "calls": data.get("calls"),
        "hardware": data.get("hardware"),
        "models": models,
        "source_count": 1,
        "sample_counts": {
            "source_archives": 1,
            "model_count": len(models),
            "prompt_count": len(next(iter(models.values()))) if models else 0,
            "total_calls": int(data.get("calls", 0)),
        },
    }


def aggregate_context_budget(experiments: Path) -> dict:
    per_condition: dict[str, list[float]] = defaultdict(list)
    per_model: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    per_task: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    per_length: dict[str, list[float]] = defaultdict(list)
    per_density: dict[str, list[float]] = defaultdict(list)
    failure_modes: defaultdict[str, int] = defaultdict(int)
    task_names: set[str] = set()
    source_count = 0
    total_calls = 0

    for path in sorted(experiments.glob("e15_context_budget*.json")):
        data = load_json(path)
        if data.get("experiment") != "e15_context_budget":
            continue
        source_count += 1
        total_calls += int(data.get("total_calls", 0))
        for row in data.get("results", []):
            condition = row.get("condition")
            rate = row.get("avg_pass_rate")
            model = normalize_model_name(row.get("model_name") or row.get("model"))
            task = row.get("task")
            length_bucket = row.get("length_bucket")
            density_bucket = row.get("density_bucket")
            if condition not in E15_CONDITIONS or rate is None or not model or not task:
                continue

            score = float(rate)
            per_condition[condition].append(score)
            per_model[str(model)][str(condition)].append(score)
            per_task[str(task)][str(condition)].append(score)
            task_names.add(str(task))

            if isinstance(length_bucket, str):
                per_length[length_bucket].append(score)
            if isinstance(density_bucket, str):
                per_density[density_bucket].append(score)

            for trial in row.get("trials", []):
                if not isinstance(trial, dict):
                    continue
                test_results = trial.get("test_results")
                if not isinstance(test_results, list):
                    continue
                failed = any(
                    not bool(item.get("passed"))
                    for item in test_results
                    if isinstance(item, dict)
                )
                if not failed:
                    continue
                mode = trial.get("failure_mode_heuristic")
                if isinstance(mode, str) and mode and mode != "no_failure":
                    failure_modes[mode] += 1

    return {
        "conditions": {
            condition: round(mean(per_condition[condition]), 4)
            for condition in E15_CONDITIONS
            if per_condition[condition]
        },
        "marginals": {
            "length": {
                bucket: round(mean(values), 4)
                for bucket, values in (("short", per_length["short"]), ("long", per_length["long"]))
                if values
            },
            "density": {
                bucket: round(mean(values), 4)
                for bucket, values in (("sparse", per_density["sparse"]), ("dense", per_density["dense"]))
                if values
            },
        },
        "models": {
            model: {
                condition: round(mean(conditions[condition]), 4)
                for condition in E15_CONDITIONS
                if conditions[condition]
            }
            for model, conditions in sorted(per_model.items())
        },
        "tasks": {
            task: {
                condition: round(mean(conditions[condition]), 4)
                for condition in E15_CONDITIONS
                if conditions[condition]
            }
            for task, conditions in sorted(per_task.items())
        },
        "failure_modes": dict(sorted(failure_modes.items())),
        "source_count": source_count,
        "sample_counts": {
            "source_archives": source_count,
            "model_count": len(per_model),
            "task_count": len(task_names),
            "condition_count": len(E15_CONDITIONS),
            "rows_per_condition": len(next(iter(per_condition.values()))) if per_condition else 0,
            "total_rows": sum(len(values) for values in per_condition.values()),
            "calls_per_condition": total_calls // len(E15_CONDITIONS) if total_calls else 0,
            "total_calls": total_calls,
            "k": 3,
        },
    }


def aggregate_format(experiments: Path) -> dict:
    path = experiments / "e7_crossval.json"
    if not path.exists():
        return {}
    data = load_json(path)
    models = {
        normalize_model_name(model): values
        for model, values in data.get("format_results", {}).items()
    }
    return {
        "overall": data.get("overall", {}),
        "models": models,
        "source_count": 1,
        "sample_counts": {
            "source_archives": 1,
            "model_count": len(models),
            "format_count": len(data.get("overall", {})),
            "total_calls": int(data.get("calls", 0)),
        },
    }


def aggregate_filler(experiments: Path) -> dict:
    path = experiments / "e4_compression.json"
    if not path.exists():
        return {}
    data = load_json(path)
    per_model: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    task_names: set[str] = set()
    variants: set[str] = set()
    for row in data.get("results", []):
        model = str(normalize_model_name(row.get("model")))
        variant = str(row.get("variant"))
        if variant in {"original", "compressed"}:
            per_model[model][variant].append(float(row.get("pass_rate", 0.0)))
            task = row.get("task")
            if task:
                task_names.add(str(task))
            variants.add(variant)
    return {
        "models": {
            model: {
                variant: round(mean(values), 4)
                for variant, values in variants.items()
            }
            for model, variants in sorted(per_model.items())
        },
        "source_count": 1,
        "sample_counts": {
            "source_archives": 1,
            "model_count": len(per_model),
            "task_count": len(task_names),
            "variant_count": len(variants),
            "rows": len(data.get("results", [])),
        },
    }


def build_findings(experiments: Path) -> list[dict]:
    specificity = aggregate_specificity(experiments)
    context_budget = aggregate_context_budget(experiments)
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
            "id": "context-budget",
            "title": "Density beats length",
            "headline": "Longer prompts did not help when the task contract stayed sparse.",
            "data": context_budget,
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
