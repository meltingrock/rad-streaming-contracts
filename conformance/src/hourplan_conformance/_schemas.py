"""Loads the bundled schemas and builds validators for them.

Current schemas live in schemas/, frozen earlier majors in schemas/v<major>/. Every bundled
schema is registered under its `$id`, so one schema can `$ref` another (the channel event's
item family is the HourPlan's `$defs/family`) without any network fetch.
"""

import json
import re
from functools import cache, lru_cache
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

_ROOT = files("hourplan_conformance") / "schemas"
_VERSION = re.compile(r"^([0-9]+)\.[0-9]+$")


def load(rel: str) -> dict[str, Any]:
    """Return the bundled schema at `rel` (relative to schemas/, e.g. 'v1/hourplan.schema.json')."""
    schema: dict[str, Any] = json.loads((_ROOT / rel).read_text())
    return schema


def _bundled() -> list[str]:
    names = [f.name for f in _ROOT.iterdir() if f.name.endswith(".schema.json")]
    for d in _ROOT.iterdir():
        if d.is_dir() and d.name.startswith("v"):
            names += [f"{d.name}/{f.name}" for f in d.iterdir() if f.name.endswith(".schema.json")]
    return sorted(names)


@lru_cache(maxsize=1)
def _registry() -> Registry:
    resources = [(s["$id"], Resource.from_contents(s)) for s in map(load, _bundled())]
    return Registry().with_resources(resources)


@cache
def validator(rel: str) -> Draft202012Validator:
    schema = load(rel)
    Draft202012Validator.check_schema(schema)
    # `format` is annotation-only unless a format checker is attached. We make it
    # assertive so `uuid` / `date-time` are enforced -- the contract validator is
    # the arbiter (spec section 5), so a non-UUID id or garbage timestamp must be caught.
    # `date-time` requires the rfc3339-validator dependency (see pyproject.toml).
    return Draft202012Validator(
        schema, registry=_registry(), format_checker=Draft202012Validator.FORMAT_CHECKER
    )


def schema_errors(rel: str, instance: Any) -> list[str]:
    return [
        f"schema[{e.validator}]: {e.message} at {'/'.join(str(p) for p in e.absolute_path) or '<root>'}"
        for e in sorted(validator(rel).iter_errors(instance), key=lambda e: list(e.absolute_path))
    ]


def major_of(version: Any) -> int | None:
    """The major of a 'major.minor' string, or None if `version` is not one."""
    if not isinstance(version, str):
        return None
    m = _VERSION.match(version)
    return int(m.group(1)) if m else None
