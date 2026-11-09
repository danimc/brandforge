"""Validate the JSON Schema vocabulary used by the bundled contracts."""
import hashlib
import json
from pathlib import Path
import re

SCHEMAS = Path(__file__).resolve().parents[1] / "schemas"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def decode(data):
    return json.loads(data.decode("utf-8"), object_pairs_hook=unique_object)


def check(value, schema, label):
    types = {"object": dict, "array": list, "string": str, "integer": int, "boolean": bool}
    if "type" in schema:
        require(type(value) is types[schema["type"]], f"{label}: expected {schema['type']}")
    if "const" in schema:
        require(value == schema["const"], f"{label}: unexpected value")
    if "enum" in schema:
        require(any(type(value) is type(x) and value == x for x in schema["enum"]),
                f"{label}: unexpected value")
    if isinstance(value, dict):
        require(set(schema.get("required", [])) <= value.keys(), f"{label}: missing required fields")
        require(len(value) >= schema.get("minProperties", 0), f"{label}: empty object")
        for key, child in value.items():
            if "propertyNames" in schema:
                check(key, schema["propertyNames"], f"{label} key")
            rule = schema.get("properties", {}).get(key, schema.get("additionalProperties", True))
            require(rule is not False, f"{label}: unknown field {key}")
            if isinstance(rule, dict):
                check(child, rule, f"{label}.{key}")
    if isinstance(value, list):
        require(len(value) <= schema.get("maxItems", len(value)), f"{label}: too many items")
        require(len(value) >= schema.get("minItems", 0), f"{label}: empty array")
        for i, child in enumerate(value):
            check(child, schema["items"], f"{label}[{i}]")
    if isinstance(value, str):
        require(len(value) >= schema.get("minLength", 0), f"{label}: empty string")
        if "pattern" in schema:
            require(re.search(schema["pattern"], value) is not None and
                    not (schema["pattern"].endswith("$") and value.endswith("\n")),
                    f"{label}: invalid format")
    if type(value) is int:
        require(value >= schema.get("minimum", value), f"{label}: below minimum")
        require(value <= schema.get("maximum", value), f"{label}: above maximum")


def validate(name, data):
    value = decode(data)
    schema = decode((SCHEMAS / f"{name}.schema.json").read_bytes())
    check(value, schema, name)
    return value
