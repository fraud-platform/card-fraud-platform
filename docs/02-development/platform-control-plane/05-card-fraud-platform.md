# Card Fraud Platform

> Status: approved

## Current Responsibilities

Today `card-fraud-platform` already owns the shared local runtime topology for the suite:

- shared Docker Compose files
- shared infrastructure containers
- application container topology for suite mode
- shared ports and container names
- platform-wide start, stop, reset, and status wrappers
- some secret sync helpers
- platform-level AGENTS and onboarding guidance

This is already the natural control-plane anchor for the suite.

## Current Duplication And Pain Points

Even with platform in place, several concerns are still scattered across sibling repos:

- service repos still carry fallback infra lifecycle scripts for shared PostgreSQL, MinIO, Redis, and Redpanda
- shared setup guidance for Doppler, Auth0, and infrastructure is spread across repos
- platform can start the suite but cannot yet act as the single operator surface for service-owned actions
- there is no unified inventory view for schemas, topics, buckets, auth resources, or secret ownership
- platform status is still container-oriented rather than ownership-oriented

## Target Future-State Ownership

`card-fraud-platform` should become the local suite control plane.

Target responsibilities:

- authoritative shared infra orchestration
- authoritative suite topology and dependency map
- authoritative platform admin CLI and future UI
- authoritative service registry and inventory aggregation
- authoritative action router for service adapters
- authoritative suite-level docs for shared infra, shared config, shared auth topology, and shared DB topology
- authoritative oversight dashboard for service health and dependency status

Platform should not own:

- service domain logic
- migration details
- service-specific Auth0 rules
- service-specific reset semantics
- service-specific seed semantics

## Platform Admin Backend/UI Boundaries

The future platform admin should be local-first and control-plane oriented.

The control plane must provide:

- suite overview page or screen
- service inventory and health aggregation
- dependency inventory and health aggregation
- guarded action entrypoints for service-owned operations
- links into Grafana, Jaeger, Prometheus, OpenAPI, and service logs
- DB/topic/bucket/secret ownership visibility

The control plane must not become:

- the business UI for fraud workflows
- the owner of service data semantics
- a shell executor for arbitrary commands
- a replacement for domain-specific consoles where those exist

## Tech Stack Constraints For The Admin Surface

The design does not commit to a final UI implementation, but it does constrain direction:

- the backend/control-plane runtime should remain in `card-fraud-platform`
- the first actionable operator surface should remain CLI-first
- if a web UI is added later, it should live under platform ownership, not inside `card-fraud-intelligence-portal`
- a Python-backed control-plane API in the platform repo is the preferred direction for a future UI
- a future web UI may be a lightweight React app or simple server-rendered admin surface inside the platform repo, but it must remain a distinct product from the portal

## Action Routing Model

Platform should maintain a registry of services and supported admin actions.

The registry should define for each service:

- canonical service id
- repo path
- runtime type
- health endpoints
- dependency list
- adapter entrypoints by domain/action
- destructive-action flags
- inventory capabilities

Platform action routing should support:

- `status` and `health` for all services
- DB actions where the service exposes them
- Auth actions where the service exposes them
- seed and verify actions where the service exposes them
- logs and restart helpers at the platform layer

## Inventory Aggregation Responsibilities

Platform should aggregate the following suite-wide views:

- service map
- infra map
- port map
- health map
- DB ownership map
- topic and consumer map
- bucket and artifact map
- auth ownership map
- Doppler ownership map
- action history map

Platform should own the model and presentation of these views, even when some metadata originates in service repos.

## Docs That Move Into Platform

Platform should become the canonical home for:

- suite operating model
- admin action contract
- inventory model
- shared secret ownership model
- docs governance model
- shared Auth0 topology
- shared DB topology
- cross-service resource ownership

## Implementation-Facing Repo Changes

Expected changes inside `card-fraud-platform` during implementation:

- add the concrete suite registry file (`services.yaml`)
- add registry loading and action routing logic
- upgrade status views from container-only to service/inventory-aware summaries
- add inventory collectors for DB, Kafka, Redis, MinIO, Auth0 metadata, and Doppler ownership
- make the concrete table/index ownership map the first implementation artifact
- deprecate duplicated suite explanations in docs now covered by platform-canonical docs

## Secret Ownership Split

Platform owns shared suite runtime secrets and shared local topology values.

Platform does not own:

- service-only provider secrets
- service-only Auth0 client details unless those are intentionally suite-governed
- service-specific feature flags that do not affect the shared runtime

## Implementation Phases

### Phase 1 - Declare

- publish `services.yaml`
- publish the concrete DB/table/index ownership map per service as the first prerequisite artifact
- publish topic, bucket, auth, and secret ownership maps
- align platform docs as the canonical suite entrypoint

### Phase 2 - Operate

- route service-owned admin operations through platform
- aggregate health, inventory, and ownership views
- reduce duplicate shared infra wrappers in service repos
- evolve platform status into a true suite control-plane surface

### Future Horizon

- richer platform admin UI
- optional data drilldown views
- action history persistence and trends

## Risks And Non-Goals

Risks:

- platform can become too large if it absorbs service internals
- action routing can become ad hoc if the contract is not enforced
- docs can regress into duplication if platform is not treated as canonical

Non-goals:

- production control plane in this phase
- CI/CD ownership
- business workflow UI ownership

