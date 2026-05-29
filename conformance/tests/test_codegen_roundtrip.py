import importlib
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
GENERATED = REPO / "conformance/src/hourplan_conformance/models_generated.py"


@pytest.mark.skipif(not GENERATED.exists(), reason="run codegen/generate_pydantic.sh first")
def test_generated_model_parses_a_valid_fixture():
    mod = importlib.import_module("hourplan_conformance.models_generated")
    # datamodel-code-generator names the root model HourPlan (title) or Model.
    model = getattr(mod, "HourPlan", None) or getattr(mod, "Model")
    plan = json.loads((REPO / "fixtures/hourplan/valid/hard-anchors.json").read_text())
    obj = model.model_validate(plan)
    assert len(obj.items) == 4
