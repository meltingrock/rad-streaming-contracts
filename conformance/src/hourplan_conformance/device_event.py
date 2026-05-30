import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

_SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schemas" / "device-event.schema.json"


@lru_cache(maxsize=1)
def _validator() -> Draft202012Validator:
    schema = json.loads(_SCHEMA_PATH.read_text())
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)


def validate_device_event(event: dict[str, Any]) -> list[str]:
    """Return a list of error messages; empty list means the event is valid.

    Validates a streams.device.{connected,disconnected} envelope against the
    shared device-event JSON Schema."""
    return [
        f"schema[{e.validator}]: {e.message} at {'/'.join(str(p) for p in e.absolute_path) or '<root>'}"
        for e in sorted(_validator().iter_errors(event), key=lambda e: list(e.absolute_path))
    ]
