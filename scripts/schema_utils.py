"""Helpers for validating repo JSON against the small schema subset used here."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ValidationError:
    path: str
    message: str


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def load_schema(path: Path) -> dict[str, Any]:
    schema = load_json(path)
    if not isinstance(schema, dict):
        raise TypeError(f"schema must be an object: {path}")
    return schema


def validate_schema(instance: Any, schema: dict[str, Any], *, path: str = "$") -> list[ValidationError]:
    errors: list[ValidationError] = []

    enum_values = schema.get("enum")
    if enum_values is not None and instance not in enum_values:
        errors.append(ValidationError(path, f"must be one of {enum_values!r}"))

    if "const" in schema and instance != schema["const"]:
        errors.append(ValidationError(path, f"must equal {schema['const']!r}"))

    schema_type = schema.get("type")
    if schema_type is not None and not _matches_type(instance, schema_type):
        return [ValidationError(path, f"expected {schema_type}, got {_type_name(instance)}")]

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        minimum = schema.get("minimum")
        if minimum is not None and instance < minimum:
            errors.append(ValidationError(path, f"must be >= {minimum}"))
        maximum = schema.get("maximum")
        if maximum is not None and instance > maximum:
            errors.append(ValidationError(path, f"must be <= {maximum}"))

    if isinstance(instance, str):
        min_length = schema.get("minLength")
        if min_length is not None and len(instance) < min_length:
            errors.append(ValidationError(path, f"must have length >= {min_length}"))

    if isinstance(instance, list):
        min_items = schema.get("minItems")
        if min_items is not None and len(instance) < min_items:
            errors.append(ValidationError(path, f"must contain at least {min_items} items"))
        if schema.get("uniqueItems"):
            seen: list[Any] = []
            for item in instance:
                if item in seen:
                    errors.append(ValidationError(path, "must not contain duplicate items"))
                    break
                seen.append(item)
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(instance):
                errors.extend(validate_schema(item, item_schema, path=f"{path}[{index}]"))

    if isinstance(instance, dict):
        properties = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in instance:
                errors.append(ValidationError(path, f"missing required property {key!r}"))

        additional = schema.get("additionalProperties", True)
        for key, value in instance.items():
            child_path = f"{path}.{key}"
            if key in properties:
                child_schema = properties[key]
                if isinstance(child_schema, dict):
                    errors.extend(validate_schema(value, child_schema, path=child_path))
            elif additional is False:
                errors.append(ValidationError(child_path, "unexpected property"))

    return errors


def _matches_type(instance: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(instance, dict)
    if expected == "array":
        return isinstance(instance, list)
    if expected == "string":
        return isinstance(instance, str)
    if expected == "number":
        return isinstance(instance, (int, float)) and not isinstance(instance, bool)
    if expected == "integer":
        return isinstance(instance, int) and not isinstance(instance, bool)
    if expected == "boolean":
        return isinstance(instance, bool)
    if expected == "null":
        return instance is None
    raise ValueError(f"unsupported schema type: {expected}")


def _type_name(instance: Any) -> str:
    if instance is None:
        return "null"
    if isinstance(instance, bool):
        return "boolean"
    if isinstance(instance, int):
        return "integer"
    if isinstance(instance, float):
        return "number"
    if isinstance(instance, dict):
        return "object"
    if isinstance(instance, list):
        return "array"
    return type(instance).__name__
