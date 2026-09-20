import itertools
from typing import Any

_HOUR_MS = 3_600_000


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

    # I4a — hard anchors must not overlap.
    #
    # I1-I3 bound the shape of a plan and not how much it contains: a plan whose
    # hard anchors all sit at the same offset satisfies every one of them. That is
    # not a hypothetical. Five leaflet lines sharing a placement window were
    # anchored at the identical instant, four times a day, and nothing anywhere
    # objected -- the plan was emitted, written and consumed in silence.
    #
    # An overlap is unplayable rather than merely crowded, which is why this is an
    # error: a worker cannot start the next advert before the current one has
    # finished, so something has to be dropped, and a paid advert vanishing with
    # no trace is the failure this contract exists to prevent.
    #
    # Compared in offset order rather than item order. I2 requires hard anchors to
    # be non-decreasing as items, but it reports that separately and a plan that
    # violates it would otherwise have its overlaps hidden behind the I2 error.
    hard = sorted(
        (i for i in items if i["timing_rule"] == "hard"),
        key=lambda i: i["start_offset_ms"],
    )
    for earlier, later in itertools.pairwise(hard):
        ends = earlier["start_offset_ms"] + earlier["duration_ms"]
        if ends > later["start_offset_ms"]:
            errors.append(
                f"I4a: hard anchor at {earlier['start_offset_ms']}ms runs to {ends}ms, "
                f"past the next at {later['start_offset_ms']}ms "
                f"(seq {earlier['seq']} overlaps seq {later['seq']})"
            )

    return errors


def check_warnings(plan: dict[str, Any]) -> list[str]:
    """Things worth saying about a plan that do not make it unplayable.

    Separate from `check_invariants` so that `validate_plan` keeps returning
    errors alone: both the compiler and the streaming worker treat a non-empty
    result as a refusal, and a warning must not take a store off air.
    """
    warnings: list[str] = []
    items = plan["items"]

    # I4b — hard anchors alone should not fill the hour.
    #
    # The softer half of I4. Everything still plays, in order, so it is not a
    # refusal -- but an hour whose anchors alone account for the whole hour has no
    # room for the music the clock calls for, and is far likelier to be a mis-set
    # advert budget than an intention.
    hard_ms = sum(i["duration_ms"] for i in items if i["timing_rule"] == "hard")
    if hard_ms > _HOUR_MS:
        warnings.append(
            f"I4b: hard anchors total {hard_ms}ms, past the {_HOUR_MS}ms hour "
            f"({len([i for i in items if i['timing_rule'] == 'hard'])} anchors)"
        )

    return warnings
