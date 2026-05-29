from typing import Any


def check_invariants(plan: dict[str, Any]) -> list[str]:
    """Cross-item rules not expressible in JSON Schema. Assumes `plan` already
    passed schema validation (so items/fields are well-typed)."""
    errors: list[str] = []
    items = plan["items"]

    # I1 — contiguous, 0-based sequence.
    for i, item in enumerate(items):
        if item["seq"] != i:
            errors.append(f"I1: items[{i}].seq is {item['seq']}, expected {i} (seq must be contiguous from 0)")

    # I2 — hard anchors non-decreasing in item order.
    last_hard: int | None = None
    for i, item in enumerate(items):
        if item["timing_rule"] == "hard":
            offset = item["start_offset_ms"]
            if last_hard is not None and offset < last_hard:
                errors.append(
                    f"I2: items[{i}].start_offset_ms {offset} < previous hard anchor {last_hard} (must be non-decreasing)"
                )
            last_hard = offset

    # I3 — declared total equals the sum of item durations.
    summed = sum(item["duration_ms"] for item in items)
    if plan["total_duration_ms"] != summed:
        errors.append(f"I3: total_duration_ms {plan['total_duration_ms']} != sum of item durations {summed}")

    return errors
