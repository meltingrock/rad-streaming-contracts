# rad-streaming-contracts

Canonical, versioned contracts for the per-store streaming platform:

- **HourPlan**: the data contract between the Playout Compiler and the stream worker.
- **Device event** (`streams.device.*`): store device presence.
- **Channel event** (`playout.channel.*`, since 1.3.0): what a store's channel in the
  stream worker actually did. The raw material for the as-run log
  (spec: meltingrock/fck-svc-stream#15).
- **As-run record** (since 2.1.0): one line of the as-run JSON Lines files, the archive's
  per-store monthly objects and the export (meltingrock/fck-svc-stream#49). Versioned on its
  own `schema_version`.

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
invariants) and enforces the `uuid` / `date-time` formats. Since 2.0.0 it picks the schema
by the **major** of `schema_version`: `1.x` is read by the frozen 1.3.0 schema
(`schemas/v1/`), `2.x` by the current one, and any other major is one
`unsupported schema_version major` error. It does **not** gate the `minor` *acceptance*
described above; that is consumer-side logic (the worker accepting `minor <=` its
built-against version).

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

Fixtures live in `fixtures/{hourplan,device-event,channel-event,as-run-record}/{valid,invalid}/` (current
major) and `fixtures/v1/{hourplan,channel-event}/` (the 1.3.0 suite, frozen). Both
this repo and each consumer should run their validator against this suite so all sides agree.

## Channel events

```python
from hourplan_conformance.channel_event import validate_channel_event
errors = validate_channel_event(event_dict)   # [] means valid
```

One message per fact on the `playout.events.<env>` topic exchange, routing key equal to
`event_type`: `playout.channel.started`, `.ended`, `.skip_requested`, `.flushed`,
`.went_silent`, `.gap`. `event_id` is `uuid5(channel_instance_id, seq)` and is what consumers
dedupe on. `payload.occurred_at` is when the channel recorded the fact; the envelope
`timestamp` is publish time and is never air time. Item kinds carry the plan item as
`payload.item` (set by the player as request annotations); `gap` carries the dropped `seq`
range and the dropped events' time span. Invariants beyond the schema: C1 (a gap's
`last_seq >= first_seq`) and C2 (`dropped_to_at >= dropped_from_at`).

Since 2.0 the envelope carries `schema_version` (`major.minor`, required from 2.0). An event
without it is a 1.x event and is read by the v1 schema; a present `1.x` is an error, since
1.x producers never sent it.

## Family

`family` is the content kind of an aired item (docs/adr/0001-family-is-content-kind.md), one
closed list for HourPlan items and channel-event items, defined once as `$defs/family` in
`hourplan.schema.json`:

`music, advert, announcement, special, promo, news, weather, traffic, station_id, sweeper,
presenter_link, psa, feature, sponsorship_bumper, other`

An item may carry `family_source` (non-empty string) only when `family` is `other`: the source
value the compiler could not map. Consumers that keep their own list assert it against the
package so drift fails a test:

```python
from hourplan_conformance import FAMILIES   # tuple, schema order, current major
assert set(SegmentFamily) == set(FAMILIES)
```

## As-run records

```python
from hourplan_conformance import AS_RUN_RECORD_SCHEMA_VERSION   # "1.0": what producers write
from hourplan_conformance.as_run_record import validate_as_run_record
errors = validate_as_run_record(line_dict)   # [] means valid
```

Schema: `schemas/as-run-record.schema.json`. Each line of an as-run JSON Lines file is one
record, picked by `record_type`:

- **`header`**: the first line of an export, and only there. `export_id`, `generated_at`,
  `service` (our service name, named once per export), `filters` (`store_ids`, `client_ids`,
  `schedule_codes`, `families`), `range` `{from, to}` (an entry's actual start, from
  inclusive, to exclusive) and `archived_months` `[{store_id, month, sha256}]`.
- **`entry`**: one airing, or a pushed item that never aired (`outcome: flushed`). It nests
  `store`, `item`, `placing_schedule` (null for clock content), `plan` and `run` around the
  airing's times and outcome. Every key is present: a time or duration that has not happened
  is `null`.
- **`gap`**: channel events dropped before they reached the log (`first_seq`, `last_seq`,
  `dropped_count`, `dropped_from_at`, `dropped_to_at`).
- **`silence`**: the channel's queue ran dry at `occurred_at`.

Gaps and silences are the log's health records, not airings: their `store` is `{id}` only.

**Times** are UTC ISO 8601 with milliseconds and a `Z` (`2026-10-11T08:00:00.123Z`).
Durations are integer milliseconds. `timezone` is IANA. No line carries a local time;
renderers compute it.

**Item fields depend on `family`**, and fields that do not apply are left out, never null.
Music carries `title`, `artist`, `album_name`, `isrc_code`, `composer`, `publisher`,
`copyright`, `code`, `media_number`, `record_label`, `arranger`. An advert carries `title`,
`code` (the creative code), `job_code`, `production_code`, `client` (the store's retailer)
and `product` (the brand it promotes). Every other family carries `title`, `code`,
`media_number` and `client`.

**Snapshots.** `store` and `item` each carry `snapshot`: `taken` (the names as they were),
`pending` (not yet: only the ids are present) or `unavailable` (given up after about a day:
only the ids, plus `snapshot_reason`). A taken item has a `title`; a taken store has its
`code`, `name` and `client`, and an `account` when it has one.

**Fields readers misread:**

- **`elapsed_ms`** is media played through, including both crossfades. A natural end reports
  the full decoded length, a skip reads about 2 s ahead of what went out, and a channel stop
  uses wall-clock time. It is not the audible time.
- **`crossfade_ms`** is the configured crossfade, not a measured overlap.
- **A play**, for royalty returns, is an aired entry with `elapsed_ms` of at least 30 s, or a
  `completed` item shorter than 30 s. `open`, `unknown` and `flushed` entries never count. It
  is applied when a return is rendered and never stored on a line
  (meltingrock/fck-svc-stream#62).

Invariants beyond the schema: A1 an entry ends after it starts; A2 and A3 a gap's seq range
and time span run forwards; A4 an export's range is non-empty; A5 to A8 an entry's `outcome`
agrees with its times, as rad-api-schedules derives it (`flushed` never started, `completed`,
`ended_early` and `skipped` have ended or gone silent, `skipped` was skip-requested, `open`
has neither ended nor gone silent).

### `schema_version` of an as-run record

`"MAJOR.MINOR"` on every line, versioned apart from the contract's own semver:

- **minor**: adds an optional field. A reader built for `1.0` reading a `1.1` line must accept
  it, so readers move before producers, as for the HourPlan.
- **major**: removes, renames or retypes a field.
- Archived lines are never rewritten. Every major's schema stays published, frozen under
  `schemas/v<major>/`, for as long as lines with it exist (5 years), and the validator picks the
  schema by the line's major.

## 1.3.0 rollout order

1.3.0 adds an optional, nullable `schedule: {id, code}` to HourPlan items (the placing
schedule; soft items carry null) and the channel-event contract.

1. The player moves to 1.3.0 **first**: a player pinned below 1.3.0 rejects any plan whose
   items carry `schedule` (`additionalProperties: false`).
2. Only then may the compiler emit `schedule`.
3. The as-run consumer and the worker's sidecar pin 1.3.0 to validate channel events.

## 2.0.0 rollout order

2.0.0 closes `family` (no `jingle`, no `prerec`; `PRC-` items carry `advert`), adds
`family_source`, sets HourPlan `schema_version` to `2.0` and adds `schema_version` to the
channel-event envelope. The package reads both majors.

1. Every reader moves to 2.0.0 **first**: the stream worker's player and sidecar, and the
   rad-api-schedules as-run consumer. 2.0.0 still accepts 1.x plans and events, so nothing
   changes on the wire yet.
2. Only then does the compiler emit `2.0` plans, and the player `2.0` channel events.
3. Once no 1.x plan can be in flight, the v1 schemas stay only to read old as-run data.

Adding a family later is a minor release (consumers before the compiler); removing one is
major.

## 2.1.0

2.1.0 adds the as-run record schema (`as_run_record`, `AS_RUN_RECORD_SCHEMA_VERSION`) and
changes nothing else, so any 2.0.0 pin can move to it. rad-api-schedules pins it to write the
archive and the export.

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
