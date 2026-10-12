from datetime import datetime
from typing import Any

from hourplan_conformance._schemas import major_of, schema_errors

RECORD_TYPES = ("header", "entry", "gap", "silence")

# What a producer writes in `schema_version` today. Versioned apart from the contract:
# adding an optional field is a minor, removing, renaming or retyping one is a major.
AS_RUN_RECORD_SCHEMA_VERSION = "1.0"

# Which schema reads a line, by the major of its `schema_version`. Archived lines are never
# rewritten, so every major stays here, its schema frozen under schemas/v<major>/, for as
# long as lines with it exist (5 years). A reader dispatches on the major alone.
SCHEMA_BY_MAJOR = {
    1: "as-run-record.schema.json",
}


def _at(value: str | None) -> datetime | None:
    return None if value is None else datetime.fromisoformat(value)


def _entry_invariants(line: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    started, ended = _at(line["started_at"]), _at(line["ended_at"])
    # A1: an airing ends after it starts.
    if started is not None and ended is not None and ended < started:
        errors.append(f"A1: ended_at {line['ended_at']} is before started_at {line['started_at']}")
    # A5-A8: the outcome is the one rad-api-schedules derives from the entry's facts
    # (app/asrun/assembly.py derive_outcome), so a reader can trust either.
    outcome = line["outcome"]
    closed = line["ended_at"] is not None or line["silenced_at"] is not None
    if outcome == "flushed" and (line["flushed_at"] is None or started is not None):
        errors.append("A5: a flushed entry has flushed_at and never started (started_at null)")
    if outcome in ("completed", "ended_early", "skipped") and not closed:
        errors.append(f"A6: a {outcome} entry has ended_at or silenced_at")
    if outcome == "skipped" and line["skip_requested_at"] is None:
        errors.append("A7: a skipped entry has skip_requested_at")
    if outcome == "open" and closed:
        errors.append("A8: an open entry has neither ended_at nor silenced_at")
    return errors


def _gap_invariants(line: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    # A2: a gap's seq range runs oldest to newest.
    if line["last_seq"] < line["first_seq"]:
        errors.append(f"A2: last_seq {line['last_seq']} < first_seq {line['first_seq']}")
    # A3: the dropped events' time span runs forwards.
    if _at(line["dropped_to_at"]) < _at(line["dropped_from_at"]):  # type: ignore[operator]
        errors.append(
            f"A3: dropped_to_at {line['dropped_to_at']} is before dropped_from_at {line['dropped_from_at']}"
        )
    return errors


def _header_invariants(line: dict[str, Any]) -> list[str]:
    # A4: an export's range is non-empty: from inclusive, to exclusive.
    if _at(line["range"]["to"]) <= _at(line["range"]["from"]):  # type: ignore[operator]
        return [
            f"A4: range.to {line['range']['to']} is not after range.from {line['range']['from']}"
        ]
    return []


_INVARIANTS = {
    "header": _header_invariants,
    "entry": _entry_invariants,
    "gap": _gap_invariants,
    "silence": lambda line: [],
}


def validate_as_run_record(line: dict[str, Any]) -> list[str]:
    """Return a list of error messages; empty list means the line is valid.

    Stage 0: the line's `schema_version` picks the schema by its major. Stage 1: that JSON
    Schema. Stage 2: invariants JSON Schema cannot express, only if stage 1 passed."""
    if not isinstance(line, dict):
        return [f"schema[type]: line must be an object, got {type(line).__name__} at <root>"]
    version = line.get("schema_version")
    major = major_of(version)
    if major is None:
        return [f"schema_version: {version!r} is not 'major.minor' at schema_version"]
    if major not in SCHEMA_BY_MAJOR:
        message = (
            f"schema_version: unsupported schema_version major {major} in {version!r} "
            f"(this package reads {sorted(SCHEMA_BY_MAJOR)}) at schema_version"
        )
        return [message]
    errors = schema_errors(SCHEMA_BY_MAJOR[major], line)
    # A record type's keys count as evaluated only when its branch passes, so one bad field
    # also makes the root report every key of the line as unexpected. Report the field; a
    # real extra key still shows once nothing else is wrong.
    specific = [e for e in errors if not e.startswith("schema[unevaluatedProperties]")]
    if errors:
        return specific or errors
    return _INVARIANTS[line["record_type"]](line)
