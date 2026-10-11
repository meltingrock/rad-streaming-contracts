"""`family` is the content kind of an aired item: one closed list, defined once (ADR 0001)."""
import json
from pathlib import Path

import pytest

from hourplan_conformance import FAMILIES
from hourplan_conformance.channel_event import validate_channel_event
from hourplan_conformance.validate import validate_plan

REPO = Path(__file__).resolve().parents[2]
SCHEMAS = REPO / "conformance/src/hourplan_conformance/schemas"

EXPECTED = (
    "music", "advert", "announcement", "special", "promo", "news", "weather", "traffic",
    "station_id", "sweeper", "presenter_link", "psa", "feature", "sponsorship_bumper", "other",
)


def _plan(**item):
    plan = json.loads((REPO / "fixtures/hourplan/valid/minimal-soft.json").read_text())
    plan["items"][0].update(item)
    return plan


def _event(**item):
    event = json.loads((REPO / "fixtures/channel-event/valid/started.json").read_text())
    event["payload"]["item"].update(item)
    return event


def test_families_is_the_adr_list_in_order():
    assert isinstance(FAMILIES, tuple)
    assert FAMILIES == EXPECTED


def test_families_is_read_from_the_hourplan_schema():
    schema = json.loads((SCHEMAS / "hourplan.schema.json").read_text())
    assert tuple(schema["$defs"]["family"]["enum"]) == FAMILIES


def test_channel_event_family_is_a_ref_to_the_hourplan_family_not_a_copy():
    text = (SCHEMAS / "channel-event.schema.json").read_text()
    item = json.loads(text)["$defs"]["item"]["properties"]["family"]
    assert set(item) == {"$ref"} and item["$ref"].endswith("hourplan.schema.json#/$defs/family")
    assert '"sponsorship_bumper"' not in text


@pytest.mark.parametrize("family", EXPECTED)
def test_every_family_is_accepted_by_both_contracts(family):
    assert validate_plan(_plan(family=family)) == []
    assert validate_channel_event(_event(family=family)) == []


@pytest.mark.parametrize("family", ["prerec", "jingle", "Music", ""])
def test_an_unlisted_family_is_rejected_by_both_contracts(family):
    assert any("family" in e for e in validate_plan(_plan(family=family)))
    assert any("family" in e for e in validate_channel_event(_event(family=family)))


def test_family_source_is_carried_only_with_other():
    assert validate_plan(_plan(family="other", family_source="jingle")) == []
    assert validate_plan(_plan(family="music", family_source="jingle")) != []
    assert validate_channel_event(_event(family="other", family_source="jingle")) == []
    assert validate_channel_event(_event(family="music", family_source="jingle")) != []


def test_other_without_family_source_is_allowed():
    assert validate_plan(_plan(family="other")) == []


def test_v2_plan_with_prerec_fails_but_v1_plan_with_prerec_passes():
    v2 = _plan(family="prerec")
    assert v2["schema_version"] == "2.0" and validate_plan(v2) != []
    v1 = dict(v2, schema_version="1.0")
    assert validate_plan(v1) == []


def test_v2_plan_must_not_claim_a_v1_major_to_carry_family_source():
    v1 = _plan(family="other", family_source="jingle")
    v1["schema_version"] = "1.3"
    assert any("family_source" in e for e in validate_plan(v1))


def test_channel_event_without_schema_version_is_read_as_v1():
    event = _event(family="prerec")
    del event["schema_version"]
    assert validate_channel_event(event) == []
