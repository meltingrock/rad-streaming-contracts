"""2.0.0 still reads 1.x: plans in flight during the rollout, and as-run data kept for years.

The 1.3.0 schemas ship frozen under schemas/v1/ and the 1.3.0 fixtures under fixtures/v1/.
"""
import hashlib
import json
from importlib.resources import files
from pathlib import Path

import pytest

from hourplan_conformance.channel_event import validate_channel_event
from hourplan_conformance.validate import validate_plan

REPO = Path(__file__).resolve().parents[2]
V1 = REPO / "fixtures/v1"

# sha256 of the schemas as tagged v1.3.0. A v1 schema never changes again.
FROZEN = {
    "hourplan.schema.json": "05d46cdff44528579830fc32e38341f02f62c5fef07ca5bff454bbb42e95829d",
    "channel-event.schema.json": "c7df2205e30f0d8d295778a9ff367f45a0f86bb227dbb61082ae86b4bb493f9e",
}


def _names(kind, which):
    return sorted(p.name for p in (V1 / kind / which).glob("*.json") if p.name != "manifest.json")


def _load(kind, which, name):
    return json.loads((V1 / kind / which / name).read_text())


def _manifest(kind):
    return json.loads((V1 / kind / "invalid/manifest.json").read_text())


@pytest.mark.parametrize("name", sorted(FROZEN))
def test_v1_schema_is_frozen(name):
    data = (files("hourplan_conformance") / "schemas" / "v1" / name).read_bytes()
    assert hashlib.sha256(data).hexdigest() == FROZEN[name]


@pytest.mark.parametrize("name", _names("hourplan", "valid"))
def test_v1_valid_plan_passes(name):
    assert validate_plan(_load("hourplan", "valid", name)) == []


@pytest.mark.parametrize("name", sorted(_manifest("hourplan")))
def test_v1_invalid_plan_is_rejected_for_the_stated_reason(name):
    errors = validate_plan(_load("hourplan", "invalid", name))
    expect = _manifest("hourplan")[name]["expect"]
    assert any(expect in e for e in errors), f"{name}: expected {expect!r}, got {errors}"


@pytest.mark.parametrize("name", _names("channel-event", "valid"))
def test_v1_valid_channel_event_passes(name):
    assert validate_channel_event(_load("channel-event", "valid", name)) == []


@pytest.mark.parametrize("name", sorted(_manifest("channel-event")))
def test_v1_invalid_channel_event_is_rejected_for_the_stated_reason(name):
    errors = validate_channel_event(_load("channel-event", "invalid", name))
    expect = _manifest("channel-event")[name]["expect"]
    assert any(expect in e for e in errors), f"{name}: expected {expect!r}, got {errors}"


def test_v1_plan_may_carry_prerec():
    plan = _load("hourplan", "valid", "prerec-family.json")
    assert plan["schema_version"].startswith("1.")
    assert validate_plan(plan) == []


def test_v1_channel_event_may_carry_prerec():
    assert validate_channel_event(_load("channel-event", "valid", "started_prerec.json")) == []


@pytest.mark.parametrize("version", ["9.0", "0.1"])
def test_plan_with_unknown_major_is_rejected(version):
    plan = _load("hourplan", "valid", "minimal-soft.json")
    plan["schema_version"] = version
    errors = validate_plan(plan)
    assert len(errors) == 1 and "unsupported schema_version major" in errors[0], errors


@pytest.mark.parametrize("version", [None, 1, "1", "one.zero", ""])
def test_plan_with_unreadable_schema_version_is_rejected(version):
    plan = _load("hourplan", "valid", "minimal-soft.json")
    if version is None:
        del plan["schema_version"]
    else:
        plan["schema_version"] = version
    errors = validate_plan(plan)
    assert errors and all("schema_version" in e for e in errors), errors


def test_non_object_plan_is_rejected_not_raised():
    assert validate_plan([]) != []  # type: ignore[arg-type]
    assert validate_plan({}) != []


def test_non_object_channel_event_is_rejected_not_raised():
    assert validate_channel_event([]) != []  # type: ignore[arg-type]
    assert validate_channel_event({}) != []
