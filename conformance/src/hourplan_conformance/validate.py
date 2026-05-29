import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from hourplan_conformance.invariants import check_invariants

_SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schemas" / "hourplan.schema.json"


@lru_cache(maxsize=1)
def _validator() -> Draft202012Validator:
    schema = json.loads(_SCHEMA_PATH.read_text())
    Draft202012Validator.check_schema(schema)
    # `format` is annotation-only unless a format checker is attached. We make it
    # assertive so `uuid` / `date-time` are enforced — the contract validator is
    # the arbiter (spec §5), so a non-UUID id or garbage timestamp must be caught.
    # `date-time` requires the rfc3339-validator dependency (see pyproject.toml).
    return Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)


def validate_plan(plan: dict[str, Any]) -> list[str]:
    """Return a list of error messages; empty list means the plan is valid.

    Stage 1: JSON Schema (structure). Stage 2: cross-item invariants (only if
    stage 1 passed, since invariants assume a well-formed structure)."""
    schema_errors = [
        f"schema[{e.validator}]: {e.message} at {'/'.join(str(p) for p in e.absolute_path) or '<root>'}"
        for e in sorted(_validator().iter_errors(plan), key=lambda e: list(e.absolute_path))
    ]
    if schema_errors:
        return schema_errors
    return check_invariants(plan)
