"""Validate tracked public JSON artifacts against repo schemas."""

from __future__ import annotations

import sys
from pathlib import Path

from schema_utils import ValidationError, load_json, load_schema, validate_schema

ROOT = Path(__file__).resolve().parent.parent

ARTIFACTS = (
    ("data/public/findings.json", "data/schemas/finding.schema.json", "id"),
    ("data/public/models.json", "data/schemas/model.schema.json", "id"),
    ("data/public/contributors.json", "data/schemas/contributor.schema.json", "id"),
)


def main() -> None:
    errors: list[str] = []

    for data_rel, schema_rel, unique_key in ARTIFACTS:
        data_path = ROOT / data_rel
        schema_path = ROOT / schema_rel
        schema = load_schema(schema_path)
        data = load_json(data_path)

        if not isinstance(data, list):
            errors.append(f"{data_rel}: expected top-level array")
            continue

        errors.extend(
            format_error(data_rel, err)
            for err in validate_array_items(data, schema, unique_key=unique_key)
        )

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        raise SystemExit(1)

    print("OK: public data schemas passed")


def validate_array_items(
    items: list[object],
    schema: dict[str, object],
    *,
    unique_key: str | None = None,
) -> list[ValidationError]:
    errors: list[ValidationError] = []
    seen_keys: set[object] = set()

    for index, item in enumerate(items):
        item_path = f"$[{index}]"
        errors.extend(validate_schema(item, schema, path=item_path))

        if unique_key is None or not isinstance(item, dict) or unique_key not in item:
            continue

        key = item[unique_key]
        if key in seen_keys:
            errors.append(ValidationError(item_path, f"duplicate {unique_key} {key!r}"))
        else:
            seen_keys.add(key)

    return errors


def format_error(data_rel: str, err: ValidationError) -> str:
    return f"{data_rel}: {err.path}: {err.message}"


if __name__ == "__main__":
    main()
