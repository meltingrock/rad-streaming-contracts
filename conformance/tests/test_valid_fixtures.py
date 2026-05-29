import json
from pathlib import Path

import pytest

from hourplan_conformance.validate import validate_plan

REPO = Path(__file__).resolve().parents[2]
VALID_DIR = REPO / "fixtures/hourplan/valid"

VALID_FILES = sorted(p.name for p in VALID_DIR.glob("*.json"))


@pytest.mark.parametrize("name", VALID_FILES)
def test_valid_fixture_passes(name):
    plan = json.loads((VALID_DIR / name).read_text())
    errors = validate_plan(plan)
    assert errors == [], f"{name} should be valid but got: {errors}"


def test_there_are_valid_fixtures():
    assert VALID_FILES, "no valid fixtures found"
