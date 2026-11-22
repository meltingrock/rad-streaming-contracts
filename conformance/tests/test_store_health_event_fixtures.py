import json
from pathlib import Path

import pytest

from hourplan_conformance import STORE_HEALTH_EVENT_SCHEMA_VERSION
from hourplan_conformance.store_health_event import STATES, validate_store_health_event

REPO = Path(__file__).resolve().parents[2]
VALID_DIR = REPO / "fixtures/store-health-event/valid"
INVALID_DIR = REPO / "fixtures/store-health-event/invalid"

VALID = sorted(p.name for p in VALID_DIR.glob("*.json"))
MANIFEST = json.loads((INVALID_DIR / "manifest.json").read_text())


def _load(path: Path) -> dict:
    event: dict = json.loads(path.read_text())
    return event


@pytest.mark.parametrize("name", VALID)
def test_valid_fixture_passes(name):
    assert validate_store_health_event(_load(VALID_DIR / name)) == [], name


@pytest.mark.parametrize("name", sorted(MANIFEST))
def test_invalid_fixture_is_rejected_for_the_stated_reason(name):
    errors = validate_store_health_event(_load(INVALID_DIR / name))
    expect = MANIFEST[name]["expect"]
    assert any(expect in e for e in errors), f"{name}: expected an error containing {expect!r}, got {errors}"


def test_invalid_fixtures_and_manifest_agree():
    files = {p.name for p in INVALID_DIR.glob("*.json")} - {"manifest.json"}
    assert files == set(MANIFEST)


def test_every_state_has_a_valid_fixture():
    states = {_load(VALID_DIR / n)["payload"]["state"] for n in VALID}
    assert states == set(STATES)


def test_fixtures_carry_the_version_producers_write():
    assert {_load(VALID_DIR / n)["schema_version"] for n in VALID} == {STORE_HEALTH_EVENT_SCHEMA_VERSION}


def test_a_minor_this_package_predates_is_accepted():
    # Consumers roll first: a 1.0 reader must not reject a 1.1 event on its version alone.
    event = _load(VALID_DIR / "off_air_alert.json")
    event["schema_version"] = "1.9"
    assert validate_store_health_event(event) == []


def test_a_non_object_is_one_error():
    assert len(validate_store_health_event([])) == 1  # type: ignore[arg-type]
