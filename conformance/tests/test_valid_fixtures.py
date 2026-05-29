import json
from pathlib import Path

from hourplan_conformance.validate import validate_plan

REPO = Path(__file__).resolve().parents[2]


def test_minimal_soft_fixture_is_valid():
    plan = json.loads((REPO / "fixtures/hourplan/valid/minimal-soft.json").read_text())
    errors = validate_plan(plan)
    assert errors == [], f"expected no errors, got {errors}"
