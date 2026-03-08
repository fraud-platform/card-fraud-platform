# Admin Action Contract

> Status: approved

## Objective

Define the standard contract by which `card-fraud-platform` invokes service-owned administrative operations.

This contract is the core mechanism that allows platform to become the single operator surface without re-implementing the internals of each service.

The design principle is:

- platform owns discovery, routing, safeguards, aggregation, and operator UX
- services own the implementation and validation logic for their own actions

## Recommended Adapter Format

Phase 1 should use a **static adapter manifest plus declared CLI entrypoints**.

### Primary Mechanism

- Platform-owned service registry: `services.yaml` in `card-fraud-platform`
- Service-owned adapter manifest: `platform-adapter.yaml` in each service repo
- Platform calls only commands declared in the service's adapter manifest

This is the primary format for Phase 1 because it works across Python, Java, and Node repos without requiring the service to be running for discovery.

See `14-service-registry-format.md` for the concrete schema.

## Action Domains

Platform actions should be grouped by domain rather than by arbitrary command names.

Recommended domains:

- `service`
- `db`
- `auth`
- `messaging`
- `storage`
- `runtime`
- `seed`
- `diagnostics`

Example command shapes:

- `platform service status rule-management`
- `platform service health all`
- `platform db verify transaction-management`
- `platform db reset-schema rule-management`
- `platform auth bootstrap portal`
- `platform messaging verify transaction-management`
- `platform seed run ops-analyst-agent`
- `platform runtime logs rule-engine-auth`

## Standard Action Catalog

Every service does not need to support every action, but the action vocabulary must be standardized across the suite.

### Core Actions

- `status` - lightweight status of runtime or adapter availability
- `health` - deeper readiness/liveness/dependency state
- `verify` - confirm current setup is valid for the selected scope
- `bootstrap` - first-time setup for service-owned external resources
- `restart` - restart service-owned local runtime entrypoint or container target
- `logs` - resolve the canonical log source for the selected scope

### Database Actions

- `db-init` - initialize schema objects or perform first-time local DB setup
- `db-verify` - verify schema, connectivity, and service-owned expectations
- `db-reset-schema` - drop and recreate service-owned schema objects, then reinitialize via the service-owned migration path
- `db-reset-data` - clear service-owned data while preserving schema objects
- `db-reset-tables` - drop or recreate only service-owned tables and related table-scoped objects without implying full schema recreation

Not every service must support every reset scope. The adapter manifest must declare which scopes are actually supported.

### Auth Actions

- `bootstrap` - create or align service-owned Auth0 resources
- `verify` - verify audiences, clients, roles, scopes, callbacks, or grants

### Seed Actions

- `seed` - seed demo or test data within service-owned boundaries

## Adapter Model

Each service repo must expose a stable adapter surface that platform can call.

Platform should not scrape arbitrary repo scripts or hardcode ad hoc shell logic.

Each adapter must define:

- supported domains
- supported actions
- target scopes
- required inputs
- prechecks
- execution entrypoint
- output contract
- failure contract
- destructive flag
- timeout
- retry policy marker

Recommended metadata shape per action:

| Field | Meaning |
|---|---|
| `service` | canonical service id |
| `domain` | `db`, `auth`, `service`, `seed`, etc. |
| `action` | standardized action name |
| `scope` | target scope such as `service`, `schema`, `tables`, `infra`, `auth-resource` |
| `destructive` | whether the action mutates or deletes state |
| `supports_dry_run` | whether the action can validate impact before execution |
| `requires_confirmation` | whether explicit human confirmation is mandatory |
| `inputs` | required and optional arguments |
| `prechecks` | conditions platform or service must verify first |
| `entrypoint` | stable command that platform calls |
| `timeout_seconds` | maximum execution time before platform marks timeout |
| `output_format` | expected machine-readable and human-readable outputs |
| `failure_modes` | canonical failure classes |

## Health Endpoint Standard

Platform should normalize health aggregation, not force a single literal path across all runtimes.

### Runtime-Family Defaults

- FastAPI: prefer `/api/v1/health`
- Quarkus rule engines: current-state canonical path remains `/v1/evaluate/health` until an explicit migration is planned
- React/static UI: `/health`

### Aggregated Health Fields

Platform should normalize health into a common model with at least:

- `service`
- `runtime`
- `status`
- `checked_at`
- `dependencies` summary
- `source_path`

The service registry is the source of truth for service-to-health-path mapping.

## Output Contract

All service adapters should return a normalized result shape so platform can aggregate results consistently.

Minimum fields:

- `service`
- `domain`
- `action`
- `target`
- `status` - `ok`, `warn`, `error`, `partial`, `skipped`, `timeout`
- `summary`
- `details`
- `destructive`
- `started_at`
- `completed_at`
- `artifacts` - optional paths, URLs, report files, or identifiers
- `next_steps` - optional human guidance

The output contract must support both:

- CLI output for humans
- machine-readable structured output for the future platform admin UI

## Failure Contract

Platform should not have to parse arbitrary error text to understand failures.

Each adapter should classify failures into stable categories such as:

- `precheck_failed`
- `dependency_unavailable`
- `auth_required`
- `invalid_configuration`
- `destructive_action_blocked`
- `runtime_failed`
- `verification_failed`
- `timeout`
- `unsupported_action`
- `partial_success`

Each failure should include:

- a short operator-readable message
- the failing step
- whether retry is safe
- whether the action is idempotent
- the likely remediation path

## Timeout And Retry Policy

### Timeouts

Recommended default timeout ranges:

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

### Partial Success And Rollback

- Service adapters must report partial success explicitly.
- Platform must surface partial success as operator-visible state.
- No implicit rollback is assumed unless the service adapter documents rollback behavior for that action.

## Safeguards

### Destructive Operations

Actions such as `db-reset-schema`, `db-reset-data`, and `db-reset-tables` must be treated as governed operations.

Required safeguards:

- service scope is explicit; no implicit cross-service destructive operations
- service adapter confirms the exact objects it owns
- platform requires confirmation before execution
- platform records who triggered the action and when
- platform captures the result and whether the action fully completed
- platform distinguishes local-only destructive actions from future shared-environment operations

### Prechecks

Platform should run lightweight prechecks before invoking a service adapter:

- repo exists at the expected sibling path
- adapter manifest exists
- declared command exists in the repo wrapper surface
- Doppler configuration is present for the target service
- required shared infra is available when the action depends on it
- target service name is valid

Service adapters should run service-specific prechecks such as:

- migration directory exists
- DB connection is resolvable
- required Auth0 secret values are present
- Kafka topics or buckets are reachable where relevant

## Auditability

Even in local-only mode, platform should capture an action log conceptually.

The future platform admin console should be able to show:

- action name
- target service
- target scope
- actor or triggering session
- start and end timestamps
- result status
- summary and remediation notes

This does not require a production-grade audit backend in the first implementation, but the design must assume that action history matters.

## Service Mapping Guidance

### Services likely to expose DB actions

- `card-fraud-rule-management`
- `card-fraud-transaction-management`
- `card-fraud-ops-analyst-agent`

### Services likely to expose Auth actions

- `card-fraud-rule-management`
- `card-fraud-transaction-management`
- `card-fraud-intelligence-portal`
- `card-fraud-ops-analyst-agent`

### Services likely to expose messaging/storage verification

- `card-fraud-rule-engine-auth`
- `card-fraud-rule-engine-monitoring`
- `card-fraud-transaction-management`
- `card-fraud-rule-management`

### Services likely to expose seed actions

- `card-fraud-rule-management`
- `card-fraud-transaction-management`
- `card-fraud-ops-analyst-agent`
- `card-fraud-e2e-load-testing`

## Non-Goals

This contract intentionally does not define:

- CI/CD orchestration
- production environment orchestration
- arbitrary shell execution from platform
- data browsing semantics for service business data
- hardcoded implementation details for service internals

## Success Criteria

The admin action contract is successful when:

- platform can route operator intent consistently across all services
- destructive operations are scoped and governable
- service repos keep implementation ownership
- the future platform admin UI can consume action results without custom per-service parsing

