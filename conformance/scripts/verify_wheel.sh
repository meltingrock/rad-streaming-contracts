#!/usr/bin/env bash
# Build the wheel, install it (NOT editable) into a clean venv, and CALL the
# validators — proves the schemas ship in the wheel (regression guard for the
# parents[3] bug where validate_* raised FileNotFoundError on wheel installs).
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf dist /tmp/wheelcheck
python -m build --wheel -o dist
python3.11 -m venv /tmp/wheelcheck
. /tmp/wheelcheck/bin/activate
pip install --upgrade pip -q
pip install dist/*.whl -q
cd /tmp
python -c "
from importlib.resources import files
from hourplan_conformance.validate import validate_plan
from hourplan_conformance.device_event import validate_device_event
from hourplan_conformance.channel_event import validate_channel_event
assert isinstance(validate_plan({}), list)
assert isinstance(validate_device_event({}), list)
assert isinstance(validate_channel_event({}), list)
schemas = files('hourplan_conformance') / 'schemas'
for name in ('hourplan.schema.json', 'channel-event.schema.json'):
    assert (schemas / 'v1' / name).is_file(), 'v1/' + name + ' missing from wheel'
item = {'seq': 0, 'family': 'prerec', 'media_id': '11110000-0000-4000-8000-000000000003',
        'uri': 's3://x/a.mp3', 'duration_ms': 100, 'timing_rule': 'soft', 'start_offset_ms': None}
plan = {'schema_version': '1.0', 'store_id': 'f1e2d3c4-0000-4000-8000-000000000001',
        'hour_bucket': '2026-05-29T14:00:00Z', 'timezone': 'Africa/Johannesburg',
        'format_clock_id': 'ab120000-0000-4000-8000-000000000002', 'format_clock_version': 3,
        'schedule_revision': 'sha256:abc', 'compiled_at': '2026-05-29T13:42:01Z',
        'total_duration_ms': 100, 'items': [item]}
assert validate_plan(plan) == [], validate_plan(plan)
print('wheel ships schemas: validate_plan + validate_device_event + validate_channel_event callable')
print('wheel ships v1 schemas: a 1.0 plan validates')
"
deactivate
rm -rf /tmp/wheelcheck
echo OK
