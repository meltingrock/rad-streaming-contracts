from hourplan_conformance._schemas import load as _load

__version__ = "1.3.0"

# The closed family vocabulary of the current contract, in schema order, read from the
# HourPlan schema's $defs/family (the channel event refers to the same definition).
# Consumers assert their own lists equal this so drift fails a test, not an air date.
FAMILIES: tuple[str, ...] = tuple(_load("hourplan.schema.json")["$defs"]["family"]["enum"])

__all__ = ["FAMILIES", "__version__"]
