# Service Registry Format

> Status: approved

## Purpose

Define the concrete static metadata format that `card-fraud-platform` will use to discover services, health endpoints, supported action domains, and adapter entrypoints.

This file resolves the biggest implementation ambiguity in the design pack: how the platform discovers service capabilities without scraping repo internals.

## Phase 1 Recommendation

Use a **static registry plus per-repo adapter manifest**.

### Primary Mechanism

- Platform owns one suite registry file, recommended as `services.yaml`, in `card-fraud-platform`.
- Each service repo owns one static adapter manifest, recommended as `platform-adapter.yaml`, at the repo root.
- Platform reads `services.yaml`, then resolves the declared adapter manifest for the target service.
- Platform invokes only commands declared by the adapter manifest.

### Why This Is The Right Phase 1 Choice

- no running service is required for discovery
- works across Python, Java, and Node repos
- avoids brittle command scraping
- preserves standalone repo ownership
- gives the future admin UI a stable metadata source

## Deferred Mechanisms

These are explicitly deferred to later phases:

- REST-based adapter discovery from live services
- dynamic plugin loading
- arbitrary command execution from the platform repo

## `services.yaml` Shape

Recommended suite registry shape:

```yaml
services:
  rule-management:
    repo: ../card-fraud-rule-management
    runtime: fastapi
    port: 8000
    health:
      kind: http
      path: /api/v1/health
      readiness_path: /api/v1/health
    auth_model: in-process
    engine_family: null
    adapter_manifest: platform-adapter.yaml
    action_domains: [service, db, auth, seed, storage]
    destructive_actions: [db-reset-schema, db-reset-data]
  rule-engine-auth:
    repo: ../card-fraud-rule-engine-auth
    runtime: quarkus
    port: 8081
    health:
      kind: http
      path: /v1/evaluate/health
      readiness_path: /v1/evaluate/health
    auth_model: gateway
    engine_family: rule-engine
    adapter_manifest: platform-adapter.yaml
    action_domains: [service, messaging, storage, runtime]
    destructive_actions: []
```

## `platform-adapter.yaml` Shape

Each service repo should publish a static adapter manifest.

Recommended shape:

```yaml
service: rule-management
entrypoints:
  service:
    status:
      command: [uv, run, service-status]
      destructive: false
      timeout_seconds: 10
    health:
      command: [uv, run, service-health]
      destructive: false
      timeout_seconds: 10
  db:
    verify:
      command: [uv, run, db-verify]
      destructive: false
      timeout_seconds: 60
    reset-schema:
      command: [uv, run, db-reset-schema]
      destructive: true
      timeout_seconds: 300
      requires_confirmation: true
  auth:
    verify:
      command: [uv, run, auth0-verify]
      destructive: false
      timeout_seconds: 60
```

## Polyglot Command Convention

The manifest command convention is language-neutral even when examples use `uv run ...`.

Within this suite, that is acceptable for the Quarkus repos as well because the rule-engine repositories already expose Python/uv-backed wrapper commands around their Java workflows. The platform should call the stable wrapper declared in `platform-adapter.yaml`, not infer the underlying build tool.

## Registry Semantics

### Platform Registry Responsibilities

`services.yaml` should declare:

- canonical service id
- repo location
- runtime family
- canonical health endpoint mapping
- auth model classification
- engine family where applicable
- action domains the service claims to support
- destructive actions list
- adapter manifest file name

### Service Adapter Manifest Responsibilities

`platform-adapter.yaml` should declare:

- exact commands platform is allowed to call
- timeout policy per action
- destructive flag per action
- confirmation requirements
- whether the action is supported in suite mode, standalone mode, or both

## Adapter Output Format

Phase 1 should standardize on **JSON** for machine-readable adapter command output.

Rationale:

- works cleanly across Python, Java, and Node wrappers
- easy to parse from CLI execution
- easy to store or render in the future platform admin UI
- avoids custom text parsing and format drift

Human-readable CLI output can still be emitted, but the platform-facing structured result should be JSON.

## Timeout And Retry Policy

### Timeouts

Recommended default ranges:

- `status` / `health`: 10 seconds
- `verify`: 60 seconds
- `bootstrap`: 180 seconds
- `db-init`: 180 seconds
- `db-reset-*`: 300 seconds
- `seed`: 180 seconds
- `logs`: operator-controlled stream, no fixed completion timeout

### Retries

- Platform does **not** auto-retry mutating actions.
- Platform does **not** auto-retry destructive actions.
- Platform may retry read-only inventory probes once when the failure is clearly transport-level.
- Platform should surface action failures to the operator rather than guessing rollback behavior.

### Partial Success

- Service adapters must report partial success explicitly.
- Platform must surface partial success as operator-visible state.
- No implicit rollback is assumed unless the service adapter documents rollback behavior for that action.

## Health Endpoint Standard

Platform should normalize health aggregation, not force a single literal path across all runtimes.

### Runtime-Family Defaults

- FastAPI: prefer `/api/v1/health`
- Quarkus rule engines: current-state canonical path remains `/v1/evaluate/health` until an explicit migration is planned
- React/static UI: `/health`

### Aggregated Health Shape

Platform should normalize health into a common model with at least:

- `service`
- `runtime`
- `status`
- `checked_at`
- `dependencies` summary
- `source_path`

The registry is the source of truth for service-to-health-path mapping.

## Reset Scope Definitions

These definitions are required to avoid ambiguity across services.

- `db-reset-schema`: drop and recreate service-owned schema objects, then reinitialize via the service-owned migration path
- `db-reset-data`: truncate or otherwise clear service-owned data while preserving schema objects
- `db-reset-tables`: drop or recreate only the service-owned tables and related table-scoped objects, without implying a full schema recreation

Not every service must support every reset scope. The adapter manifest must declare which scopes are actually supported.

## Success Criteria

The registry and adapter format are successful when:

- platform can discover services deterministically
- service repos do not need custom parsing logic in platform
- action routing is stable across languages and runtimes
- timeouts, retries, health mapping, destructive behavior, and output format are explicit before implementation starts
