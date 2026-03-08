# Phase 2 Platform Internals

> Status: review

## Objective

Define the internal technical design for Phase 2 implementation inside `card-fraud-platform`.

This document is intentionally narrower than the broader control-plane architecture pack. The broader pack locks the operating model and ownership decisions. This document defines how the platform repo should implement those decisions without re-deciding architecture during coding.

Scope of this document:

- exact metadata and ownership artifact paths in the platform repo
- exact Python module layout for the control-plane implementation
- exact CLI shape for the platform operator surface
- exact action execution flow
- exact inventory collector strategy
- exact health aggregation behavior
- exact timeout, retry, confirmation, and audit behavior
- exact structured output contract expected from platform internals

This remains design only. No code changes are introduced here.

## Design Constraints

The design must align to the current repo shape:

- the repo already exposes `platform-up`, `platform-down`, `platform-status`, and `platform-reset` via `pyproject.toml`
- the repo already has a `scripts/` package
- the repo currently uses simple Python subprocess-based orchestration
- Phase 2 should extend that structure, not replace it with a separate framework

The design must also preserve:

- suite mode and standalone mode from the approved operating model
- registry-driven discovery from `14-service-registry-format.md`
- service-owned implementation behind `platform-adapter.yaml`

## Technical Decisions

### Metadata Location

Use a single top-level metadata area in the platform repo:

- `C:/Users/kanna/github/card-fraud-platform/control-plane/services.yaml`
- `C:/Users/kanna/github/card-fraud-platform/control-plane/ownership/database.yaml`
- `C:/Users/kanna/github/card-fraud-platform/control-plane/ownership/messaging.yaml`
- `C:/Users/kanna/github/card-fraud-platform/control-plane/ownership/storage.yaml`
- `C:/Users/kanna/github/card-fraud-platform/control-plane/ownership/auth.yaml`
- `C:/Users/kanna/github/card-fraud-platform/control-plane/ownership/secrets.yaml`
- `C:/Users/kanna/github/card-fraud-platform/control-plane/logs/action-history.jsonl`

Rationale:

- keeps control-plane metadata out of the repo root clutter
- keeps runtime metadata separate from docs
- gives Phase 1 and Phase 2 a stable shared location

Service-owned adapter manifests remain at the repo root of each service:

- `../card-fraud-rule-management/platform-adapter.yaml`
- `../card-fraud-rule-engine-auth/platform-adapter.yaml`
- etc.

### Dependency Choices

Phase 2 should keep the platform runtime lean.

Recommended additions:

- `PyYAML` for reading `services.yaml`, ownership artifacts, and adapter manifests
- `boto3` for MinIO/S3 inventory queries

Everything else should stay standard-library-first where possible.

Do not add a web framework in Phase 2. Phase 2 is CLI and internal service-layer work only.

## Python Module Layout

Create a dedicated internal package under `scripts/`:

```text
scripts/
  control_plane/
    __init__.py
    models.py
    registry.py
    adapter_manifest.py
    action_runner.py
    health.py
    result.py
    audit.py
    confirm.py
    timeouts.py
    inventory/
      __init__.py
      base.py
      services.py
      docker_runtime.py
      database.py
      messaging.py
      redis_runtime.py
      storage.py
      auth.py
      secrets.py
    presenters/
      __init__.py
      table.py
      json_output.py
      summary.py
  platformctl.py
  platform_status.py
  platform_up.py
  platform_down.py
  constants.py
```

### Responsibilities By Module

#### `scripts/control_plane/models.py`

Defines internal typed models for:

- `ServiceRegistryEntry`
- `HealthSpec`
- `ActionSpec`
- `AdapterManifest`
- `InventorySnapshot`
- `InventoryRecord`
- `ActionResult`
- `AuditRecord`
- `CollectorResult`

Use dataclasses plus explicit validation rather than introducing a heavier validation framework.

#### `scripts/control_plane/registry.py`

Responsibilities:

- load `control-plane/services.yaml`
- validate required fields
- resolve sibling repo paths relative to the platform repo
- provide lookup by service id
- provide grouped service views by runtime, engine family, and action domain

#### `scripts/control_plane/adapter_manifest.py`

Responsibilities:

- load a target repo's `platform-adapter.yaml`
- validate declared commands and required fields
- map logical action names to executable command arrays
- expose destructive flags, timeouts, and supported execution modes

#### `scripts/control_plane/action_runner.py`

Responsibilities:

- execute declared adapter commands
- inject execution context such as `--format json` where required
- enforce timeout rules
- capture stdout/stderr
- parse JSON output into `ActionResult`
- normalize failure categories on timeout, parse failure, or process failure

#### `scripts/control_plane/health.py`

Responsibilities:

- resolve health path from the registry
- execute HTTP health checks against declared endpoints
- normalize responses into a common health model
- degrade gracefully to runtime/container state when an endpoint is unavailable

#### `scripts/control_plane/result.py`

Responsibilities:

- define JSON serialization rules for `ActionResult` and inventory output
- convert internal results into human or JSON presenter payloads

#### `scripts/control_plane/audit.py`

Responsibilities:

- append action records to `control-plane/logs/action-history.jsonl`
- write both start and completion records for mutating actions
- support later querying of recent action history

#### `scripts/control_plane/confirm.py`

Responsibilities:

- enforce destructive action confirmation semantics
- support interactive confirmation in TTY mode
- reject destructive actions in non-interactive mode unless explicit confirmation flags are supplied

#### `scripts/control_plane/timeouts.py`

Responsibilities:

- centralize default timeout values by action type
- allow registry or manifest overrides where permitted

## Inventory Collector Layout

All collectors should implement a common interface in `scripts/control_plane/inventory/base.py`.

Recommended interface shape:

- `name()` -> collector id
- `collect(context)` -> `CollectorResult`
- `supports(service_or_scope)` -> bool

### `services.py`

Combines:

- registry metadata
- adapter manifest availability
- declared runtime/auth/action-domain metadata

This collector is purely metadata-driven.

### `docker_runtime.py`

Uses Docker CLI to gather:

- container existence
- running/exited state
- health status where available
- mapped ports
- compose project labels

This extends the current `platform_status.py` container-centric behavior into a reusable collector.

### `database.py`

Uses containerized `psql` via `docker exec card-fraud-postgres ...`.

Responsibilities:

- validate Postgres reachability
- query table counts by ownership map
- query index counts by ownership map
- expose schema presence and reset boundary metadata

Reason for this choice:

- avoids adding a direct Postgres driver to the platform repo
- reuses the platform-owned Postgres container and its bundled tools

### `messaging.py`

Uses Redpanda `rpk` via `docker exec card-fraud-redpanda ...`.

Responsibilities:

- list topics
- list partitions
- list consumer groups
- fetch lag where available
- overlay topic and group ownership from `control-plane/ownership/messaging.yaml`

### `redis_runtime.py`

Uses `redis-cli` via `docker exec card-fraud-redis ...`.

Responsibilities:

- health and ping
- basic INFO summary
- memory and keyspace summary
- role and eviction indicators where available

### `storage.py`

Uses MinIO/S3 API through `boto3`.

Responsibilities:

- list buckets
- fetch bucket existence/health
- optionally summarize object counts or manifests where affordable
- overlay bucket and artifact ownership from `control-plane/ownership/storage.yaml`

### `auth.py`

Phase 2 should be manifest-driven, not Auth0-API-driven.

Responsibilities:

- read auth ownership from `control-plane/ownership/auth.yaml`
- read auth model classification from `services.yaml`
- surface gateway-auth versus in-process-auth distinctions
- expose which services support auth bootstrap/verify actions

Do not integrate live Auth0 API calls in Phase 2.

### `secrets.py`

Uses Doppler CLI in name-only mode.

Responsibilities:

- confirm project/config presence
- fetch secret names only, never values
- compare required shared keys from ownership metadata
- surface drift and missing-key states

## CLI Shape

Phase 2 should introduce one root operator CLI while preserving the existing `platform-up`, `platform-down`, `platform-status`, and `platform-reset` entrypoints.

Recommended new entrypoint:

- `uv run platformctl`

### `platformctl` Commands

```text
uv run platformctl status
uv run platformctl inventory services
uv run platformctl inventory infra
uv run platformctl inventory db
uv run platformctl inventory messaging
uv run platformctl inventory storage
uv run platformctl inventory auth
uv run platformctl inventory secrets
uv run platformctl action <domain> <action> <service>
uv run platformctl registry validate
```

### Relationship To Existing Commands

- `platform-up`, `platform-down`, and `platform-reset` remain focused on runtime lifecycle
- `platform-status` becomes a thin wrapper over the shared control-plane status/inventory presenter
- `platformctl` becomes the root control-plane command for Phase 2 operations

## Action Execution Flow

For `uv run platformctl action <domain> <action> <service>`:

1. load and validate `control-plane/services.yaml`
2. resolve the target service
3. load and validate the target repo's `platform-adapter.yaml`
4. confirm the requested domain/action exists for that service
5. run platform-level prechecks:
   - repo path exists
   - manifest exists
   - declared command exists
   - required shared infra is available where needed
6. for destructive actions, run confirmation gating
7. write an action-start audit record
8. execute the adapter command with timeout enforcement
9. parse JSON stdout into `ActionResult`
10. write an action-complete audit record
11. render human or JSON output

If parsing fails, platform must convert that to a normalized `runtime_failed` or `invalid_output` failure rather than returning raw stdout only.

## Adapter Invocation Rules

Platform should call declared wrapper commands only.

It should not:

- infer Maven, pnpm, or Python internals from repo contents
- call undocumented scripts directly
- guess equivalent commands when the adapter manifest is missing

For structured output, platform should require adapter commands to support:

- `--format json` or an equivalent declared JSON mode

If a repo has not yet implemented JSON output, platform should treat that as Phase 1 incomplete and refuse Phase 2 routing for that action.

## JSON Output Contract

The platform-facing action result should be JSON.

Minimum required shape:

```json
{
  "service": "rule-management",
  "domain": "db",
  "action": "verify",
  "target": "service",
  "status": "ok",
  "summary": "Database verification passed",
  "details": [],
  "destructive": false,
  "started_at": "2026-03-07T12:00:00Z",
  "completed_at": "2026-03-07T12:00:02Z",
  "artifacts": [],
  "next_steps": []
}
```

Rules:

- machine-readable JSON goes to stdout
- human/log output goes to stderr when needed
- platform presenters re-render JSON into tables or summaries for human CLI mode

## Health Aggregation Design

### Source Of Truth

Health path and runtime family come from `control-plane/services.yaml`.

### Aggregation Rules

For each service:

1. check the Docker/runtime state from `docker_runtime.py`
2. if the service is expected to be running, execute the HTTP health probe using the declared path
3. normalize the result into one of:
   - `healthy`
   - `degraded`
   - `unreachable`
   - `not-running`
   - `unknown`
4. attach dependency summary where known

### Probe Timeouts

- health HTTP timeout: 5 seconds per service
- no retry for individual service action invocations
- one retry allowed for read-only health or inventory probes when the failure is clearly transport-level

## Timeout And Retry Behavior

### Action Timeouts

Action timeouts come from the adapter manifest with fallback defaults from `scripts/control_plane/timeouts.py`.

### Retry Rules

- no auto-retry for mutating actions
- no auto-retry for destructive actions
- at most one retry for read-only inventory probes
- timeouts should produce normalized `timeout` failures

## Confirmation And Audit Design

### Confirmation Rules

For destructive actions, require:

- explicit `--yes`
- explicit `--confirm <service>:<domain>:<action>` token

If running in a TTY, platform may also show an interactive summary before execution.

If not running in a TTY and the flags are missing, the action must fail fast.

### Audit Persistence

Write JSONL audit records to:

- `C:/Users/kanna/github/card-fraud-platform/control-plane/logs/action-history.jsonl`

Each record should include:

- timestamp
- service
- domain
- action
- scope
- destructive flag
- actor/session marker if available
- outcome status
- summary

## Presenter Design

Two presenter modes are required:

- human table/summary mode
- `--json` mode

Human mode is the default for CLI interaction.

JSON mode is the default for machine integration and should be used by other tooling or future UI backends.

## File-Level Refactor Plan For Existing Scripts

### `scripts/platform_status.py`

Refactor into a thin wrapper that:

- loads the registry
- invokes runtime and service collectors
- renders a suite-aware summary using shared presenter code

### `scripts/platform_up.py` and `scripts/platform_down.py`

Keep their primary lifecycle responsibility.

Only extract reusable helpers when shared by `platformctl`.

### `scripts/constants.py`

Keep only true constants here.

Move richer registry and metadata behavior into `scripts/control_plane/registry.py`.

## Acceptance Criteria

This technical design is sufficient when an implementer can answer, without making new design decisions:

- where metadata files live
- which Python modules to create
- how the CLI is shaped
- how actions are executed and parsed
- how inventory is collected per dependency class
- how health is normalized
- how timeouts, retries, confirmations, and audit logging work
