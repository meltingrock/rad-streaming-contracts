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
from hourplan_conformance import FAMILIES
assert len(FAMILIES) == 15 and FAMILIES[-1] == 'other', FAMILIES
assert any('prerec' in e for e in validate_plan(dict(plan, schema_version='2.0')))
event = {'schema_version': '2.0', 'event_id': 'e0e0e0e0-0000-5000-8000-000000000010',
         'event_type': 'playout.channel.started', 'timestamp': '2026-09-21T13:15:02Z',
         'payload': {'store_id': plan['store_id'], 'channel_instance_id': plan['store_id'], 'seq': 0,
                     'occurred_at': '2026-09-21T13:15:00Z', 'rid': 1, 'crossfade_ms': 0,
                     'item': {'media_id': item['media_id'], 'seq': 0, 'family': 'music',
                              'hour_bucket': plan['hour_bucket'], 'schedule_revision': 'sha256:abc',
                              'format_clock_version': 3, 'timezone': plan['timezone'],
                              'duration_ms': 100, 'timing_rule': 'soft', 'start_offset_ms': None}}}
assert validate_channel_event(event) == [], validate_channel_event(event)
from hourplan_conformance import AS_RUN_RECORD_SCHEMA_VERSION
from hourplan_conformance.as_run_record import validate_as_run_record
gap = {'record_type': 'gap', 'schema_version': AS_RUN_RECORD_SCHEMA_VERSION,
       'store': {'id': plan['store_id']}, 'run': {'channel_instance_id': plan['store_id']},
       'first_seq': 1, 'last_seq': 2, 'dropped_count': 2, 'occurred_at': '2026-10-11T09:12:00.500Z',
       'dropped_from_at': '2026-10-11T09:01:10.000Z', 'dropped_to_at': '2026-10-11T09:11:58.250Z'}
assert validate_as_run_record(gap) == [], validate_as_run_record(gap)
assert any('jingle' in e for e in validate_as_run_record({'record_type': 'header', 'schema_version': '1.0',
    'export_id': plan['store_id'], 'generated_at': '2026-10-12T06:00:01.250Z', 'service': 'x',
    'filters': {'families': ['jingle']}, 'range': {'from': '2026-07-01T00:00:00.000Z',
    'to': '2026-10-01T00:00:00.000Z'}, 'archived_months': []}))
print('wheel ships the as-run record: a gap validates, its family filter resolves the shared family')
print('wheel ships schemas: validate_plan + validate_device_event + validate_channel_event callable')
print('wheel ships v1 schemas: a 1.0 plan validates')
print('wheel resolves the shared family: FAMILIES exported, a 2.0 channel event validates')
"
deactivate
rm -rf /tmp/wheelcheck
echo OK
