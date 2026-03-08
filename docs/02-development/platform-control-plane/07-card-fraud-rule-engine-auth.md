# Card Fraud Rule Engine AUTH

> Status: approved

## Current Responsibilities

`card-fraud-rule-engine-auth` owns the hot-path runtime for AUTH fraud decisioning:

- low-latency AUTH evaluation
- fail-open semantics where designed
- Redis-backed velocity checks
- MinIO artifact consumption
- Kafka decision publishing
- AUTH-specific management and replay endpoints
- performance-sensitive runtime behavior and load-test constraints

It is a service with strong runtime performance concerns and a different auth posture from the other APIs because token validation is offloaded to the gateway layer.

## Current Duplication And Pain Points

The repo still exposes local infra wrappers and repeated shared setup guidance for:

- Redis and other shared dependencies
- local infra startup patterns that overlap with platform
- shared Doppler and runtime guidance that could be centralized

At the same time, it has unique performance constraints that platform must not obscure.

## Target Future-State Ownership

AUTH runtime remains fully service-owned.

It must continue to own:

- AUTH request path and response semantics
- latency-sensitive runtime settings
- Redis usage semantics for velocity and outbox behavior
- Kafka publish semantics
- ruleset load and hot-reload logic
- performance verification methodology
- service-specific runtime diagnostics

Platform should own only the control-plane surface around this service.

## Special Auth Boundary

This service explicitly assumes gateway-enforced authentication and authorization.

That must be represented clearly in the control-plane model:

- platform inventory should show this as a gateway-auth service
- platform auth docs should state that AUTH does not validate tokens in-process
- platform should not attempt to normalize this service into the same auth runtime model as the FastAPI services

## Relationship To MONITORING

For engine-family shared concerns, see `08-card-fraud-rule-engine-monitoring.md` together with `13-cross-repo-summary.md`.

This document is authoritative for AUTH-specific deltas such as hot-path behavior, runtime role, and load-test expectations.

## Admin Actions To Expose To Platform

Recommended platform-callable actions:

- `service status`
- `service health`
- `verify` for runtime dependencies
- `messaging verify`
- `storage verify`
- `runtime restart`
- `logs`

Optional later actions:

- ruleset registry status
- ruleset load or hotswap operations if safely modeled as service-owned admin actions

Destructive DB actions are not a primary concern here because AUTH is not a DB-owning service in the same way as rule-management or transaction-management.

## Inventory Data Platform Can Read

Platform should surface for AUTH:

- service runtime status
- host port and health endpoint
- gateway-auth posture
- Redis dependency status
- Kafka dependency status
- MinIO artifact dependency status
- ruleset namespace ownership (`CARD_AUTH`)
- performance visibility pointers such as metrics endpoints or load-test constraints
- engine-family membership (`rule-engine`)

## Load-Test Hooks And Runtime Metrics

Because this service is performance-sensitive, platform should explicitly account for:

- packaged-JAR versus dev-mode distinction for valid performance testing
- runtime metrics or links required for latency validation
- dependency health relevant to load tests
- current SLO references from engine documentation

Platform should show this service as a latency-critical component rather than a generic API.

## Docs That Move To Platform

Platform should centralize:

- shared Redis/Kafka/MinIO topology
- suite-level gateway-auth explanation
- shared runtime port and dependency conventions
- how AUTH fits into the wider suite topology

## Docs That Remain Local

AUTH repo should keep:

- hot-path behavior documentation
- performance and profiling guidance
- Redis outbox and velocity semantics
- ruleset registry behavior
- service-specific evaluation and management API details

## Implementation-Facing Repo Changes

Expected changes inside `card-fraud-rule-engine-auth` during implementation:

- add `platform-adapter.yaml`
- declare `service`, `messaging`, `storage`, and `runtime` actions via stable wrappers
- publish dependency metadata for Redis, Kafka, and MinIO
- publish engine-family classification and gateway-auth classification for platform inventory
- reduce duplicated shared topology docs and point to platform-canonical docs

## Secret Ownership Split

Platform-owned shared runtime values:

- Redis topology
- Kafka topology
- MinIO credentials and bucket names
- shared Auth0 domain metadata used in suite mode

AUTH-owned values:

- standalone repo duplicates as required
- AUTH-specific client or service settings where they remain meaningful locally
- performance-tuning settings that are runtime-specific rather than suite-global

## Implementation Phases

### Phase 1 - Declare

- define AUTH registry entry and adapter manifest
- define gateway-auth classification
- define dependency inventory shape for Redis, Kafka, and MinIO

### Phase 2 - Operate

- route health/status/logs through platform
- route runtime dependency verification through platform
- expose platform-visible load-test and readiness metadata

### Future Horizon

- richer engine-family inventory and performance views in platform admin

## Risks And Non-Goals

Risks:

- treating AUTH like a generic CRUD service would hide important runtime constraints
- pulling performance logic into platform would create coupling and confusion

Non-goals:

- moving AUTH runtime logic into platform
- normalizing gateway-auth services into in-process auth semantics

