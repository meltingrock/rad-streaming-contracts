from typing import Any

from hourplan_conformance._schemas import schema_errors


def validate_device_event(event: dict[str, Any]) -> list[str]:
    """Return a list of error messages; empty list means the event is valid.

    Validates a streams.device.{connected,disconnected} envelope against the
    shared device-event JSON Schema."""
    return schema_errors("device-event.schema.json", event)
