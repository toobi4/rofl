"""A minimal, lovingly hand-rolled JSON-Schema-ish validator."""

from __future__ import annotations

from typing import Any

from hwee.kernel.errors import SchemaViolation

_TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "null": type(None),
}


def validate(instance: Any, schema: dict, path: str = "$") -> None:
    expected = schema.get("type")
    if expected is not None:
        options = expected if isinstance(expected, list) else [expected]
        if not any(_matches(instance, option) for option in options):
            raise SchemaViolation(f"{path}: expected {expected}, got {type(instance).__name__}")
    if "enum" in schema and instance not in schema["enum"]:
        raise SchemaViolation(f"{path}: {instance!r} not in {schema['enum']!r}")
    if isinstance(instance, int) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            raise SchemaViolation(f"{path}: {instance} < {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            raise SchemaViolation(f"{path}: {instance} > {schema['maximum']}")
    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                raise SchemaViolation(f"{path}: missing required property {key!r}")
        for key, subschema in schema.get("properties", {}).items():
            if key in instance:
                validate(instance[key], subschema, f"{path}.{key}")
    if isinstance(instance, list) and "items" in schema:
        for index, item in enumerate(instance):
            validate(item, schema["items"], f"{path}[{index}]")


def _matches(instance: Any, type_name: str) -> bool:
    py = _TYPES[type_name]
    if type_name in ("integer", "number") and isinstance(instance, bool):
        return False
    return isinstance(instance, py)
