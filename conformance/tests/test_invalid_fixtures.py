import json
from pathlib import Path

import pytest

from hourplan_conformance.validate import validate_plan

REPO = Path(__file__).resolve().parents[2]
INVALID_DIR = REPO / "fixtures/hourplan/invalid"

MANIFEST = json.loads((INVALID_DIR / "manifest.json").read_text())


@pytest.mark.parametrize("name", sorted(MANIFEST.keys()))
def test_invalid_fixture_is_rejected(name):
    plan = json.loads((INVALID_DIR / name).read_text())
    errors = validate_plan(plan)
    assert errors, f"{name} should be rejected but validated clean"
    expect = MANIFEST[name]["expect"]
    assert any(expect in e for e in errors), f"{name}: expected an error containing {expect!r}, got {errors}"


def test_every_invalid_fixture_has_a_file():
    for name in MANIFEST:
        assert (INVALID_DIR / name).exists(), f"manifest references missing fixture {name}"


def test_every_invalid_fixture_is_in_manifest():
    files = {p.name for p in INVALID_DIR.glob("*.json")} - {"manifest.json"}
    assert files == set(MANIFEST.keys()), "invalid fixtures and manifest are out of sync"
