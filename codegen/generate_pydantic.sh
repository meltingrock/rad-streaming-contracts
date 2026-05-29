#!/usr/bin/env bash
# Generate Pydantic v2 models from the canonical JSON Schema.
# The schema is authoritative; this output is a convenience and is git-ignored.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
OUT="$REPO/conformance/src/hourplan_conformance/models_generated.py"
datamodel-codegen \
  --input "$REPO/schemas/hourplan.schema.json" \
  --input-file-type jsonschema \
  --output-model-type pydantic_v2.BaseModel \
  --target-python-version 3.11 \
  --output "$OUT"
echo "generated $OUT"
