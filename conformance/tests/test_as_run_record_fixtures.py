import json
from pathlib import Path

import pytest

from hourplan_conformance import AS_RUN_RECORD_SCHEMA_VERSION
from hourplan_conformance.as_run_record import RECORD_TYPES, validate_as_run_record

REPO = Path(__file__).resolve().parents[2]
VALID_DIR = REPO / "fixtures/as-run-record/valid"
INVALID_DIR = REPO / "fixtures/as-run-record/invalid"

VALID = sorted(p.name for p in VALID_DIR.glob("*.json"))
MANIFEST = json.loads((INVALID_DIR / "manifest.json").read_text())


@pytest.mark.parametrize("name", VALID)
def test_valid_line_passes(name):
    line = json.loads((VALID_DIR / name).read_text())
    assert validate_as_run_record(line) == [], name


@pytest.mark.parametrize("name", sorted(MANIFEST))
def test_invalid_line_is_rejected_for_the_stated_reason(name):
    line = json.loads((INVALID_DIR / name).read_text())
    errors = validate_as_run_record(line)
    expect = MANIFEST[name]["expect"]
    assert any(expect in e for e in errors), (
        f"{name}: expected an error containing {expect!r}, got {errors}"
    )


def test_invalid_lines_and_manifest_agree():
    files = {p.name for p in INVALID_DIR.glob("*.json")} - {"manifest.json"}
    assert files == set(MANIFEST)


def test_a_bad_field_is_reported_alone():
    # A failing record-type branch leaves its keys unevaluated; the root must not then list
    # every key of the line as unexpected.
    line = json.loads((INVALID_DIR / "entry_local_time.json").read_text())
    errors = validate_as_run_record(line)
    assert len(errors) == 1 and "started_at" in errors[0], errors


def test_every_record_type_has_a_valid_line():
    types = {json.loads((VALID_DIR / n).read_text())["record_type"] for n in VALID}
    assert types == set(RECORD_TYPES)


def test_the_package_names_the_version_producers_write():
    # Producers stamp this on every line; the first release of the record is 1.0.
    assert AS_RUN_RECORD_SCHEMA_VERSION == "1.0"
    line = json.loads((VALID_DIR / "entry_music_completed.json").read_text())
    assert validate_as_run_record(dict(line, schema_version=AS_RUN_RECORD_SCHEMA_VERSION)) == []
