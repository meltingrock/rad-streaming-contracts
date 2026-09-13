import json
from datetime import datetime
from functools import lru_cache
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator

_SCHEMA_PATH = files("hourplan_conformance") / "schemas" / "channel-event.schema.json"

EVENT_TYPES = (
    "playout.channel.started",
    "playout.channel.ended",
    "playout.channel.skip_requested",
    "playout.channel.flushed",
    "playout.channel.went_silent",
    "playout.channel.gap",
)


@lru_cache(maxsize=1)
def _validator() -> Draft202012Validator:
    schema = json.loads(_SCHEMA_PATH.read_text())
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)


def _check_invariants(event: dict[str, Any]) -> list[str]:
    """Rules JSON Schema cannot express. Assumes the event passed schema validation."""
    if event["event_type"] != "playout.channel.gap":
        return []
    payload = event["payload"]
    errors: list[str] = []
    # C1: a gap names a seq range, oldest first.
    if payload["last_seq"] < payload["first_seq"]:
        errors.append(
            f"C1: payload.last_seq {payload['last_seq']} < first_seq {payload['first_seq']} "
            "(a gap's seq range runs oldest to newest)"
        )
    # C2: the dropped events' time span runs forwards, so a consumer can place the gap on a day.
    started = datetime.fromisoformat(payload["dropped_from_at"])
    ended = datetime.fromisoformat(payload["dropped_to_at"])
    if ended < started:
        errors.append(
            f"C2: payload.dropped_to_at {payload['dropped_to_at']} is before "
            f"dropped_from_at {payload['dropped_from_at']}"
        )
    return errors


def validate_channel_event(event: dict[str, Any]) -> list[str]:
    """Return a list of error messages; empty list means the event is valid.

    Stage 1: the shared channel-event JSON Schema. Stage 2: invariants, only if
    stage 1 passed."""
    schema_errors = [
        f"schema[{e.validator}]: {e.message} at {'/'.join(str(p) for p in e.absolute_path) or '<root>'}"
        for e in sorted(_validator().iter_errors(event), key=lambda e: list(e.absolute_path))
    ]
    if schema_errors:
        return schema_errors
    return _check_invariants(event)
