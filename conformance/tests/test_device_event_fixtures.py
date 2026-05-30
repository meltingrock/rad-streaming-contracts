import json
from pathlib import Path

import pytest

from hourplan_conformance.device_event import validate_device_event

REPO = Path(__file__).resolve().parents[2]
VALID_DIR = REPO / "fixtures/device-event/valid"
INVALID_DIR = REPO / "fixtures/device-event/invalid"

VALID = sorted(p.name for p in VALID_DIR.glob("*.json"))
INVALID = sorted(p.name for p in INVALID_DIR.glob("*.json"))


def test_there_are_fixtures():
    assert VALID and INVALID


@pytest.mark.parametrize("name", VALID)
def test_valid_fixture_passes(name):
    event = json.loads((VALID_DIR / name).read_text())
    assert validate_device_event(event) == [], name


@pytest.mark.parametrize("name", INVALID)
def test_invalid_fixture_fails(name):
    event = json.loads((INVALID_DIR / name).read_text())
    assert validate_device_event(event) != [], name
