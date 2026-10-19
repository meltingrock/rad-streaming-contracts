import json
from pathlib import Path

import pytest

from hourplan_conformance.channel_event import EVENT_TYPES, validate_channel_event

REPO = Path(__file__).resolve().parents[2]
VALID_DIR = REPO / "fixtures/channel-event/valid"
INVALID_DIR = REPO / "fixtures/channel-event/invalid"

VALID = sorted(p.name for p in VALID_DIR.glob("*.json"))
MANIFEST = json.loads((INVALID_DIR / "manifest.json").read_text())


@pytest.mark.parametrize("name", VALID)
def test_valid_fixture_passes(name):
    event = json.loads((VALID_DIR / name).read_text())
    assert validate_channel_event(event) == [], name


@pytest.mark.parametrize("name", sorted(MANIFEST))
def test_invalid_fixture_is_rejected_for_the_stated_reason(name):
    event = json.loads((INVALID_DIR / name).read_text())
    errors = validate_channel_event(event)
    expect = MANIFEST[name]["expect"]
    assert any(expect in e for e in errors), f"{name}: expected an error containing {expect!r}, got {errors}"


def test_every_kind_has_a_valid_fixture():
    kinds = {json.loads((VALID_DIR / n).read_text())["event_type"] for n in VALID}
    assert kinds == set(EVENT_TYPES)


def test_invalid_fixtures_and_manifest_agree():
    files = {p.name for p in INVALID_DIR.glob("*.json")} - {"manifest.json"}
    assert files == set(MANIFEST)
