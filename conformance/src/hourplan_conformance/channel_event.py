from datetime import datetime
from typing import Any

from hourplan_conformance._schemas import major_of, schema_errors

EVENT_TYPES = (
    "playout.channel.started",
    "playout.channel.ended",
    "playout.channel.skip_requested",
    "playout.channel.flushed",
    "playout.channel.went_silent",
    "playout.channel.gap",
)

# Which schema reads an event, by the major of its envelope `schema_version`. Events carried
# no version before 2.0, so an event without one is a 1.x event; a 2.0 producer must send it.
# 1.x events stay readable: the as-run log is assembled from them for years.
SCHEMA_BY_MAJOR = {
    1: "v1/channel-event.schema.json",
    2: "channel-event.schema.json",
}


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

    Stage 0: the envelope `schema_version` picks the schema (absent means 1.x). Stage 1:
    the shared channel-event JSON Schema. Stage 2: invariants, only if stage 1 passed."""
    if not isinstance(event, dict):
        return [f"schema[type]: event must be an object, got {type(event).__name__} at <root>"]
    if "schema_version" not in event:
        major = 1
    else:
        version = event["schema_version"]
        found = major_of(version)
        if found is None:
            return [f"schema_version: {version!r} is not 'major.minor' at schema_version"]
        # 1.x events never carry schema_version, so a present one must name a later major.
        if found == 1 or found not in SCHEMA_BY_MAJOR:
            message = (
                f"schema_version: unsupported schema_version major {found} in {version!r} "
                f"(an event without schema_version is 1.x; this package reads "
                f"{sorted(m for m in SCHEMA_BY_MAJOR if m > 1)} when present) at schema_version"
            )
            return [message]
        major = found
    errors = schema_errors(SCHEMA_BY_MAJOR[major], event)
    if errors:
        return errors
    return _check_invariants(event)
