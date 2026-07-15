# rad-streaming-contracts

Canonical, versioned contracts for the per-store streaming platform. Currently:
the **HourPlan** — the data contract between the Playout Compiler (sub-project A)
and the Liquidsoap worker (sub-project B).

- Spec: `2026-05-29-hourplan-interface-design.md` (in rad-web-controlcenter).
- Canonical artifact: `schemas/hourplan.schema.json` (JSON Schema draft 2020-12).
  This file is the single source of truth. Pydantic models are generated from it.

## Versioning

The contract uses semver, carried in each plan's `schema_version` and in the git
tag of this repo.

- **major** — breaking. A worker reading a higher major than it supports treats
  the plan as unreadable and falls back.
- **minor** — additive. Because both objects are `additionalProperties: false`,
  **roll consumers before producers**: a worker accepts `minor <=` the one it was
  built against; the compiler must not emit a new minor until the worker fleet
  supports it.
- **patch** — docs/fixtures only; no wire change.

The conformance validator (`validate_plan`) checks a plan's **structure** (schema +
invariants) and enforces the `uuid` / `date-time` formats. It does **not** gate the
`major`/`minor` *acceptance* described above — that version-range decision is
consumer-side logic (the worker accepting `minor <=` its built-against version), not a
property of the plan itself, so there is intentionally no "unknown-major" rejection
fixture.

## Consuming this contract

Pin a tagged version (git submodule or dependency). Validate every plan:

```python
from hourplan_conformance.validate import validate_plan
errors = validate_plan(plan_dict)   # [] means valid
```

Optionally generate Pydantic v2 models (convenience only; the schema is authoritative):

```bash
codegen/generate_pydantic.sh   # writes conformance/src/hourplan_conformance/models_generated.py
```

## Conformance suite

```bash
cd conformance
python3.11 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest -v
```

Fixtures live in `fixtures/hourplan/{valid,invalid}/`. Both this repo and each
consumer should run their validator against this suite so all sides agree.

## Change process

Edit schema → bump semver → update fixtures → consumers update their pin
deliberately. No silent drift.

## Releasing a new contract version

This package is consumed via a `git+https` **tag pin** (no package index). To cut a release:

1. Bump `version` in `conformance/pyproject.toml` (keep it equal to the git tag you will create).
2. Commit on `master`.
3. Create an annotated tag: `git tag -a vX.Y.Z -m "hourplan-conformance vX.Y.Z"` and push: `git push origin master vX.Y.Z`.
4. Bump the pin in each consumer's `pyproject.toml` to `@vX.Y.Z`.

The **git tag is the source of truth** for what consumers fetch; pip checks out the tag and does not verify the declared version, so always keep `version` == the tag.

Consumers pin:

    hourplan-conformance @ git+https://github.com/meltingrock/rad-streaming-contracts.git@vX.Y.Z#subdirectory=conformance
