from datetime import datetime
from typing import Any

from hourplan_conformance._schemas import load, major_of, schema_errors

# What a producer writes in `schema_version` today. Versioned apart from the contract:
# adding an optional field or a state is a minor, removing, renaming or retyping one is a major.
STORE_HEALTH_EVENT_SCHEMA_VERSION = "1.0"

# Which schema reads an event, by the major of its `schema_version`. A later major's schema
# goes here, and this one moves under schemas/v1/, for as long as 1.x events can be in flight.
SCHEMA_BY_MAJOR = {
    1: "store-health-event.schema.json",
}

# The states, in schema order: what consumers map to their own messages.
STATES: tuple[str, ...] = tuple(load(SCHEMA_BY_MAJOR[1])["$defs"]["state"]["enum"])


def _check_invariants(event: dict[str, Any]) -> list[str]:
    """Rules JSON Schema cannot express. Assumes the event passed schema validation."""
    payload = event["payload"]
    errors: list[str] = []
    # H1: a state begins before (or when) the watcher reports it.
    if datetime.fromisoformat(payload["occurred_at"]) < datetime.fromisoformat(payload["since"]):
        errors.append(
            f"H1: payload.since {payload['since']} is after occurred_at {payload['occurred_at']}"
        )
    # H2: previous_state is the state this one replaced, so it is never the same state.
    if payload["previous_state"] == payload["state"]:
        errors.append(
            f"H2: payload.previous_state equals state {payload['state']!r} "
            "(previous_state is the state `state` replaced at `since`)"
        )
    return errors


def validate_store_health_event(event: dict[str, Any]) -> list[str]:
    """Return a list of error messages; empty list means the event is valid.

    Stage 0: the event's `schema_version` picks the schema by its major. Stage 1: that JSON
    Schema. Stage 2: invariants JSON Schema cannot express, only if stage 1 passed."""
    if not isinstance(event, dict):
        return [f"schema[type]: event must be an object, got {type(event).__name__} at <root>"]
    version = event.get("schema_version")
    major = major_of(version)
    if major is None:
        return [f"schema_version: {version!r} is not 'major.minor' at schema_version"]
    if major not in SCHEMA_BY_MAJOR:
        message = (
            f"schema_version: unsupported schema_version major {major} in {version!r} "
            f"(this package reads {sorted(SCHEMA_BY_MAJOR)}) at schema_version"
        )
        return [message]
    errors = schema_errors(SCHEMA_BY_MAJOR[major], event)
    if errors:
        return errors
    return _check_invariants(event)
