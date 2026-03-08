# Card Fraud Transaction Management

> Status: approved

## Current Responsibilities

`card-fraud-transaction-management` owns the transaction persistence and downstream workflow layer:

- decision event ingestion
- Kafka consumption and publishing patterns where applicable
- transaction persistence and review-state storage
- idempotency and replay semantics
- service-specific DB migrations and reset boundaries
- service-specific Auth0 setup and verification
- transaction query and analyst-facing backend workflows

## Current Duplication And Pain Points

This repo still carries duplicated local wrappers for:

- PostgreSQL lifecycle
- Redis lifecycle
- Kafka/Redpanda lifecycle
- MinIO lifecycle
- combined infra-up/down patterns

Those concerns overlap heavily with `card-fraud-platform`, which already owns the shared infra stack in suite mode.

## Target Future-State Ownership

Transaction management should remain the owner of:

- transaction schema and migration semantics
- idempotency model
- replay and backfill semantics
- transaction review workflow data model
- service-specific DB init/verify/reset semantics
- transaction-management-specific Auth0 configuration
- Kafka topic usage semantics for this service

Platform should become the single operator surface and inventory aggregator for those responsibilities.

## Admin Actions To Expose To Platform

Recommended platform-callable actions:

- `service status`
- `service health`
- `db-init`
- `db-verify`
- `db-reset-tables`
- `db-reset-data`
- `verify`
- `auth bootstrap`
- `auth verify`
- `messaging verify`
- `seed`
- `logs`

Transaction management is one of the strongest candidates for scoped destructive operations from platform because it owns tables and Kafka-facing operational state that a platform admin may legitimately need to verify or reset.

## Kafka And Topic Verification Boundaries

Transaction management should continue to define:

- which topics it consumes and publishes
- what topic bootstrap or verification means for this service
- how consumer groups and replay semantics are interpreted

Platform should show topic ownership and broker state, but should not redefine topic semantics on behalf of the service.

## Reset Scope Boundary

This service needs especially precise reset semantics.

- `db-reset-data` should clear service-owned rows while preserving schema objects
- `db-reset-tables` should drop or recreate only transaction-management-owned tables and related table-scoped objects
- DLQ-, replay-, and review-state tables must be explicitly classified as transaction-management-owned or external before implementation starts

Platform must never infer those table boundaries. The service-owned ownership map must declare them.

## Inventory Data Platform Can Read

Platform should expose for transaction management:

- service runtime status and health endpoint
- owned DB tables and index counts
- migration state summary
- Kafka topic ownership or dependency map
- consumer-group ownership and lag summary where available
- Auth0 ownership summary
- reset boundary metadata

## Docs That Move To Platform

- shared DB topology overview
- shared Kafka/Redpanda topology
- shared Doppler ownership model
- suite-level Auth0 architecture overview
- shared startup and operator workflows

## Docs That Remain Local

- idempotency model
- replay/backfill rules
- transaction query API details
- service-specific auth model
- service-specific DB and table semantics
- DLQ and retention specifics

## Implementation-Facing Repo Changes

Expected changes inside `card-fraud-transaction-management` during implementation:

- add `platform-adapter.yaml`
- declare `db`, `auth`, `messaging`, `service`, and `seed` actions through stable wrappers
- publish the concrete table/index ownership map including DLQ and replay-state tables
- publish topic and consumer-group ownership metadata
- reduce duplicated shared infra guidance and link back to platform-canonical suite docs
- preserve standalone workflows while making platform the primary suite operator surface

## Secret Ownership Split

Platform-owned shared runtime values:

- shared DB credentials
- shared Kafka/Redpanda topology
- shared Redis/MinIO topology as consumed in suite mode
- shared Auth0 domain metadata

Transaction-management-owned values:

- standalone duplicates required for isolated repo use
- service-specific auth configuration
- service-only runtime flags and integration values

## Implementation Phases

### Phase 1 - Declare

- document transaction-management table and index ownership
- document Kafka topic and consumer-group ownership
- add adapter manifest metadata
- classify DLQ/replay/reset boundaries explicitly

### Phase 2 - Operate

- route DB verify/reset and Kafka verify actions through platform
- show transaction-management DB/table/index counts in platform inventory
- show owned topics, consumer groups, and health indicators in platform admin

### Future Horizon

- richer replay/backfill oversight and topic health visualization in platform admin

## Risks And Non-Goals

Risks:

- if platform reimplements Kafka setup or DB reset semantics, the service boundary becomes unclear
- if topic ownership is not explicitly documented, platform inventory will be incomplete

Non-goals:

- moving transaction workflow logic into platform
- using platform as a data browser for transaction business data in this phase

