"""Validate a contributed experiment JSON file."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: validate_contribution.py <result.json>")

    path = Path(sys.argv[1])
    data = json.loads(path.read_text())
    errors: list[str] = []

    if data.get("experiment") != "e9_specificity":
        errors.append("experiment must be e9_specificity")
    if not data.get("model_name"):
        errors.append("model_name is required")
    if int(data.get("k", 0)) < 3:
        errors.append("k must be >= 3")
    if "temperature" not in data:
        errors.append("temperature is required")
    if not isinstance(data.get("results"), list) or not data["results"]:
        errors.append("results must be a non-empty list")

    for idx, row in enumerate(data.get("results", []), start=1):
        rate = row.get("avg_pass_rate")
        if rate is None or not 0 <= float(rate) <= 1:
            errors.append(f"row {idx}: avg_pass_rate must be between 0 and 1")
        if row.get("level") not in {"vague", "task_only", "task_io", "full_spec"}:
            errors.append(f"row {idx}: invalid level")

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        raise SystemExit(1)

    print(f"OK: {path}")


if __name__ == "__main__":
    main()
