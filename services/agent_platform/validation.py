_TYPE_MAP: dict[str, type | tuple[type, ...]] = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "list": list,
}


def validate_payload(payload: dict, schema: dict[str, str]) -> list[str]:
    """Checks `payload` against a bounty's objective-criteria shape. Returns a list of
    human-readable errors (empty if valid) rather than raising, so callers can decide
    how to surface multiple problems at once."""
    errors: list[str] = []
    for field, type_name in schema.items():
        if field not in payload:
            errors.append(f"missing required field '{field}'")
            continue
        expected = _TYPE_MAP.get(type_name)
        if expected is None:
            errors.append(f"unknown expected type '{type_name}' for field '{field}'")
            continue
        # bool is a subclass of int in Python — exclude it explicitly so a stray
        # `true`/`false` doesn't silently satisfy an "integer" field.
        value = payload[field]
        if isinstance(value, bool) and expected is not bool:
            errors.append(f"field '{field}' expected type {type_name}, got boolean")
        elif not isinstance(value, expected):
            errors.append(f"field '{field}' expected type {type_name}, got {type(value).__name__}")
    return errors
