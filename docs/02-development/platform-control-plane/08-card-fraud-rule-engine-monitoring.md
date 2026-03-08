# Card Fraud Rule Engine MONITORING

> Status: approved

## Current Responsibilities

`card-fraud-rule-engine-monitoring` owns the MONITORING/analytics evaluation runtime:

- monitoring evaluation flow
- asynchronous Kafka publishing
- Redis-backed shared runtime concerns where used
- MinIO artifact consumption
- MONITORING-specific evaluation semantics and SLO expectations
- service-specific performance and runtime guidance

This service shares a large amount of runtime shape with AUTH, but its evaluation semantics and performance posture are not identical.

## Current Duplication And Pain Points

Similar to AUTH, the repo still carries local infra wrappers and repeated shared dependency guidance even though platform already owns suite-mode shared infra.

There is also a documentation risk: because AUTH and MONITORING are structurally similar, shared details can be copied too freely while service-specific differences become implicit.

## Target Future-State Ownership

MONITORING should continue to own:

- monitoring evaluation semantics
- ruleset namespace ownership for `CARD_MONITORING`
- service-specific performance/SLO policy
- dependency handling specific to this runtime
- service-level tests and diagnostics

Platform should own the suite-level control surface and inventory representation.

## Relationship To AUTH

For engine-family shared concerns, see `07-card-fraud-rule-engine-auth.md` together with `13-cross-repo-summary.md`.

This document is authoritative for MONITORING-specific deltas such as evaluation semantics, runtime role, and SLO context.

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

- ruleset registry status and administrative runtime operations if safely modeled

## Inventory Data Platform Can Read

Platform should show for MONITORING:

- service runtime status
- host port and health endpoint
- gateway-auth posture
- Redis/Kafka/MinIO dependency summary
- ruleset namespace ownership (`CARD_MONITORING`)
- MONITORING role within the suite
- service-specific SLO reference metadata
- engine-family membership (`rule-engine`)

## Docs That Move To Platform

- shared engine-family role in the suite topology
- shared infra dependency overview
- shared gateway-auth explanation
- shared port and startup conventions

## Docs That Remain Local

- monitoring evaluation semantics
- MONITORING-specific SLO policy
- runtime diagnostics and performance guidance
- service-specific API and management behavior

## Implementation-Facing Repo Changes

Expected changes inside `card-fraud-rule-engine-monitoring` during implementation:

- add `platform-adapter.yaml`
- declare `service`, `messaging`, `storage`, and `runtime` actions via stable wrappers
- publish dependency metadata for Redis, Kafka, and MinIO
- publish engine-family classification and gateway-auth classification for platform inventory
- reduce duplicated shared topology docs and point to platform-canonical docs

## Secret Ownership Split

Platform-owned shared runtime values:

- shared Redis/Kafka/MinIO topology
- shared bucket name and common local runtime credentials
- shared Auth0 domain metadata used in suite mode

MONITORING-owned values:

- standalone duplicates where needed
- service-specific runtime tuning and local-only settings
- any MONITORING-specific client/config values

## Implementation Phases

### Phase 1 - Declare

- define MONITORING registry entry and adapter manifest
- document what is shared with AUTH and what is not
- register platform-visible dependency metadata

### Phase 2 - Operate

- route health/status/logs through platform
- integrate dependency verification through platform
- present MONITORING-specific role and SLO metadata in the control plane

### Future Horizon

- unified engine-family inventory with service-specific drilldown in platform admin

## Risks And Non-Goals

Risks:

- over-merging AUTH and MONITORING documentation can erase important differences
- platform might accidentally treat both services as a single logical unit in ways that hurt operability

Non-goals:

- combining AUTH and MONITORING ownership into platform
- collapsing service-specific SLO and runtime semantics

