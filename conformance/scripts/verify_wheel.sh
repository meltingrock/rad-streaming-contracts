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
from hourplan_conformance.validate import validate_plan
from hourplan_conformance.device_event import validate_device_event
from hourplan_conformance.channel_event import validate_channel_event
assert isinstance(validate_plan({}), list)
assert isinstance(validate_device_event({}), list)
assert isinstance(validate_channel_event({}), list)
print('wheel ships schemas: validate_plan + validate_device_event + validate_channel_event callable')
"
deactivate
rm -rf /tmp/wheelcheck
echo OK
