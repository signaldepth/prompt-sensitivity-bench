"""Validate a contributed experiment JSON file."""

from __future__ import annotations

import sys
from pathlib import Path

from schema_utils import load_json, load_schema, validate_schema

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "data" / "schemas" / "contribution.schema.json"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: validate_contribution.py <result.json>")

    path = Path(sys.argv[1])
    data = load_json(path)
    schema = load_schema(SCHEMA)
    errors = [
        f"{err.path}: {err.message}"
        for err in validate_schema(data, schema)
    ]

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        raise SystemExit(1)

    print(f"OK: {path}")


if __name__ == "__main__":
    main()
