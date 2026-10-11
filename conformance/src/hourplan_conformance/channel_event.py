from datetime import datetime
from typing import Any

from hourplan_conformance._schemas import schema_errors

EVENT_TYPES = (
    "playout.channel.started",
    "playout.channel.ended",
    "playout.channel.skip_requested",
    "playout.channel.flushed",
    "playout.channel.went_silent",
    "playout.channel.gap",
)


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
    if not isinstance(event, dict):
        return [f"schema[type]: event must be an object, got {type(event).__name__} at <root>"]
    errors = schema_errors("v1/channel-event.schema.json", event)
    if errors:
        return errors
    return _check_invariants(event)
