from hourplan_conformance._schemas import load as _load
from hourplan_conformance.as_run_record import AS_RUN_RECORD_SCHEMA_VERSION

__version__ = "2.1.0"

# The closed family vocabulary of the current contract, in schema order, read from the
# HourPlan schema's $defs/family (the channel event refers to the same definition).
# Consumers assert their own lists equal this so drift fails a test, not an air date.
FAMILIES: tuple[str, ...] = tuple(_load("hourplan.schema.json")["$defs"]["family"]["enum"])

__all__ = ["AS_RUN_RECORD_SCHEMA_VERSION", "FAMILIES", "__version__"]
