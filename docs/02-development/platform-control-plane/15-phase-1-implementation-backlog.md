# Implementation Backlog

> Status: approved

## Purpose

Convert the approved control-plane design pack into a phased implementation backlog that can be executed repo by repo without reopening architecture decisions.

This backlog remains plan-only. It does not change code.

## Execution Model

Implementation is intentionally split into two active phases and one future horizon:

- **Phase 1 - Declare**: publish metadata, ownership maps, registry, and docs realignment
- **Phase 2 - Operate**: implement routing, inventory aggregation, and suite control-plane behavior
- **Future Horizon**: richer admin UI, data drilldown, persistent action history

## Workstream 1 - Platform Foundation (`card-fraud-platform`)

### Phase 1 - Declare

1. Create the concrete `services.yaml` suite registry.
2. Finalize the `platform-adapter.yaml` schema and author a reference example.
3. Produce the concrete DB/table/index ownership artifact for all DB-owning services.
4. Produce the topic ownership and consumer-group ownership artifact.
5. Produce the MinIO bucket/artifact ownership artifact.
6. Produce the Auth0 ownership artifact showing gateway-auth versus in-process-auth services.
7. Produce the Doppler ownership artifact showing platform-owned versus service-owned keys.
8. Realign platform docs to point to the new registry and ownership artifacts.

### Phase 2 - Operate

1. Implement registry loading.
2. Implement adapter manifest loading and validation.
3. Implement platform action routing for non-destructive actions first.
4. Implement platform health aggregation using the registry health mapping.
5. Implement suite inventory views for services and shared infra.
6. Implement DB/topic/bucket/auth/secret ownership views.
7. Add guarded destructive action routing only after ownership artifacts are in place.
8. Upgrade `platform-status` into a suite-aware control-plane summary.

## Workstream 2 - Highest-Value Service Repos

These repos come first because they expose the most important admin actions and own the most concrete DB/messaging boundaries.

### `card-fraud-rule-management`

Phase 1:

- add `platform-adapter.yaml`
- declare service/db/auth/seed/storage actions
- publish rule-management DB/table/index ownership
- publish artifact ownership metadata
- realign shared docs back to platform

Phase 2:

- make platform-routed verify/bootstrap/reset actions work through the declared wrappers
- surface rule-management inventory in platform

### `card-fraud-transaction-management`

Phase 1:

- add `platform-adapter.yaml`
- declare service/db/auth/messaging/seed actions
- publish DB/table/index ownership including replay/review/DLQ boundaries
- publish Kafka topic and consumer-group ownership
- realign shared docs back to platform

Phase 2:

- make platform-routed DB and messaging actions work through the declared wrappers
- surface transaction-management ownership and health in platform inventory

## Workstream 3 - Engine Family

Treat the rule-engine services as a coordinated pair because they share a runtime family and dependency shape.

### `card-fraud-rule-engine-auth`

Phase 1:

- add `platform-adapter.yaml`
- declare service/messaging/storage/runtime actions
- publish dependency metadata for Redis, Kafka, and MinIO
- publish gateway-auth classification and engine-family membership

Phase 2:

- route health/status/logs and dependency verification through platform
- surface AUTH runtime role and dependency state in platform inventory

### `card-fraud-rule-engine-monitoring`

Phase 1:

- add `platform-adapter.yaml`
- declare service/messaging/storage/runtime actions
- publish dependency metadata for Redis, Kafka, and MinIO
- publish gateway-auth classification and engine-family membership

Phase 2:

- route health/status/logs and dependency verification through platform
- surface MONITORING role and dependency state in platform inventory

## Workstream 4 - Remaining Service Repos

### `card-fraud-ops-analyst-agent`

Phase 1:

- add `platform-adapter.yaml`
- declare service/db/auth/seed/verify actions
- publish DB ownership metadata
- publish dual secret ownership metadata
- realign shared docs back to platform

Phase 2:

- route readiness/preflight and owned actions through platform
- surface dual ownership and readiness in platform inventory

### `card-fraud-intelligence-portal`

Phase 1:

- add `platform-adapter.yaml`
- declare service/auth actions
- publish dependency metadata for backend APIs and SPA auth ownership
- realign shared docs back to platform

Phase 2:

- route verify/auth actions through platform
- surface portal dependency and auth metadata in platform inventory

### `card-fraud-e2e-load-testing`

Phase 1:

- add `platform-adapter.yaml`
- declare service/verify/seed actions where applicable
- publish scenario dependency metadata
- align harness docs to consume platform topology

Phase 2:

- surface harness readiness and coverage metadata in platform inventory
- integrate the existing Locust/profile path into platform control-plane workflows

## Phase 1 Deliverables Checklist

Phase 1 is complete only when all of the following exist:

- `services.yaml`
- adapter manifest schema and examples
- `platform-adapter.yaml` in each in-scope service repo
- DB/table/index ownership artifact
- topic/consumer-group ownership artifact
- bucket/artifact ownership artifact
- Auth0 ownership artifact
- Doppler ownership artifact
- shared docs realigned to platform-first guidance

## Phase 2 Deliverables Checklist

Phase 2 is complete only when all of the following work end to end:

- platform loads the registry and adapter manifests
- platform aggregates service and infra health
- platform shows ownership-aware inventory
- platform routes non-destructive service actions through declared adapters
- platform routes destructive actions only for services with explicit ownership maps and manifest support
- duplicate shared infra orchestration in service repos is reduced in suite mode

## Execution Order

Recommended sequence:

1. `card-fraud-platform` foundation artifacts
2. `card-fraud-rule-management`
3. `card-fraud-transaction-management`
4. `card-fraud-rule-engine-auth` and `card-fraud-rule-engine-monitoring` together
5. `card-fraud-ops-analyst-agent`
6. `card-fraud-intelligence-portal`
7. `card-fraud-e2e-load-testing`

## Acceptance Criteria

This backlog is successful when an implementer can start Phase 1 without making new architecture decisions and can start Phase 2 without redefining ownership boundaries.
