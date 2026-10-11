from typing import Any

from hourplan_conformance._schemas import major_of, schema_errors
from hourplan_conformance.invariants import check_invariants

# Which schema reads a plan, by the major of its `schema_version`. 1.x plans are still read
# after 2.0.0: they are in flight until the compiler emits 2.0, and as-run data outlives them.
SCHEMA_BY_MAJOR = {
    1: "v1/hourplan.schema.json",
    2: "hourplan.schema.json",
}


def validate_plan(plan: dict[str, Any]) -> list[str]:
    """Return a list of error messages; empty list means the plan is valid.

    Stage 0: the major of `schema_version` picks the schema. Stage 1: JSON Schema
    (structure). Stage 2: cross-item invariants (only if stage 1 passed, since
    invariants assume a well-formed structure)."""
    if not isinstance(plan, dict):
        return [f"schema[type]: plan must be an object, got {type(plan).__name__} at <root>"]
    version = plan.get("schema_version")
    major = major_of(version)
    if major is None:
        return [f"schema_version: {version!r} is missing or not 'major.minor' at schema_version"]
    if major not in SCHEMA_BY_MAJOR:
        message = (
            f"schema_version: unsupported schema_version major {major} in {version!r} "
            f"(this package reads majors {sorted(SCHEMA_BY_MAJOR)}) at schema_version"
        )
        return [message]
    errors = schema_errors(SCHEMA_BY_MAJOR[major], plan)
    if errors:
        return errors
    return check_invariants(plan)
