"""Summarize heuristic failure modes from detailed harness outputs."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize heuristic failure modes from experiment JSON files."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["data/private/experiments", ".output/experiments"],
        help="JSON files or directories to scan",
    )
    return parser.parse_args()


def iter_json_files(paths: list[str]) -> list[Path]:
    found: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_file() and path.suffix == ".json":
            found.append(path)
        elif path.is_dir():
            found.extend(sorted(path.rglob("*.json")))
    return sorted({path.resolve() for path in found})


def load_json(path: Path) -> dict[str, object] | None:
    try:
        data = json.loads(path.read_text())
    except Exception:  # noqa: BLE001
        return None
    return data if isinstance(data, dict) else None


def summarize_file(data: dict[str, object]) -> tuple[Counter[str], str | None]:
    results = data.get("results")
    if not isinstance(results, list):
        return Counter(), "summary_only_or_nonstandard_results"

    counts: Counter[str] = Counter()
    detailed_trials = 0
    for row in results:
        if not isinstance(row, dict):
            continue
        trials = row.get("trials")
        if not isinstance(trials, list):
            continue
        for trial in trials:
            if not isinstance(trial, dict):
                continue
            test_results = trial.get("test_results")
            if not isinstance(test_results, list):
                continue
            detailed_trials += 1
            failed = any(not bool(item.get("passed")) for item in test_results if isinstance(item, dict))
            if not failed:
                continue
            mode = trial.get("failure_mode_heuristic")
            if isinstance(mode, str) and mode and mode != "no_failure":
                counts[mode] += 1
            else:
                counts["unlabeled_failure"] += 1

    if detailed_trials == 0:
        return Counter(), "no_detailed_trial_artifacts"
    return counts, None


def render_counter(counter: Counter[str]) -> list[str]:
    if not counter:
        return ["- none"]
    return [f"- `{mode}`: {count}" for mode, count in counter.most_common()]


def main() -> None:
    args = parse_args()
    files = iter_json_files(args.paths)
    scanned = 0
    supported = 0
    skipped: Counter[str] = Counter()
    total_modes: Counter[str] = Counter()
    by_experiment: dict[str, Counter[str]] = defaultdict(Counter)
    by_model: dict[str, Counter[str]] = defaultdict(Counter)

    for path in files:
        data = load_json(path)
        scanned += 1
        if data is None:
            skipped["invalid_json"] += 1
            continue

        mode_counts, skip_reason = summarize_file(data)
        if skip_reason is not None:
            skipped[skip_reason] += 1
            continue

        supported += 1
        experiment = str(data.get("experiment") or path.stem)
        model_name = str(data.get("model_name") or data.get("model") or path.stem)
        total_modes.update(mode_counts)
        by_experiment[experiment].update(mode_counts)
        by_model[model_name].update(mode_counts)

    print("# Failure Taxonomy Summary")
    print()
    print(f"- scanned files: {scanned}")
    print(f"- files with detailed trial artifacts: {supported}")
    print(f"- skipped files: {sum(skipped.values())}")
    print()
    print("## Skipped")
    for line in render_counter(skipped):
        print(line)
    print()
    print("## Failure Modes")
    for line in render_counter(total_modes):
        print(line)
    print()
    print("## By Experiment")
    if not by_experiment:
        print("- none")
    for experiment, counts in sorted(by_experiment.items()):
        print(f"- `{experiment}`")
        for line in render_counter(counts):
            print(f"  {line}")
    print()
    print("## By Model")
    if not by_model:
        print("- none")
    for model_name, counts in sorted(by_model.items()):
        print(f"- `{model_name}`")
        for line in render_counter(counts):
            print(f"  {line}")


if __name__ == "__main__":
    main()
