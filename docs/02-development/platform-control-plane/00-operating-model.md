# Operating Model

> Status: approved

## Objective

Define the enterprise operating model for the Card Fraud suite so `card-fraud-platform` becomes the control plane for the service estate without collapsing ownership boundaries between the services.

The central principle is:

**platform orchestrates; services implement.**

That principle means the platform owns runtime topology, governance, operator UX, and shared visibility, while each service repository continues to own the service-specific logic that only that service can safely define.

## Scope Of The Control Plane

The control plane model covers the full local suite:

- `card-fraud-platform`
- `card-fraud-rule-management`
- `card-fraud-rule-engine-auth`
- `card-fraud-rule-engine-monitoring`
- `card-fraud-transaction-management`
- `card-fraud-intelligence-portal`
- `card-fraud-e2e-load-testing`
- `card-fraud-ops-analyst-agent`

`card-fraud-analytics` is explicitly deferred. It remains a future service reference but is not part of the current implementation planning scope.

It also covers the shared infrastructure that those services depend on:

- PostgreSQL
- MinIO
- Redis
- Redpanda/Kafka
- Jaeger
- Prometheus
- Grafana

## Sequencing Rule

The single most important sequencing rule for implementation is:

**prefer read-only inventory before adding control operations.**

That means the first implementation pass should establish ownership maps, service registry metadata, and accurate status/health/inventory views before expanding the action surface. The platform should know what exists and who owns it before it is trusted to mutate anything.

## Two Supported Execution Modes

### Suite Mode

Suite mode is the default enterprise workflow for local end-to-end work.

In suite mode:

- `card-fraud-platform` is the authoritative entrypoint.
- Platform owns shared infra lifecycle, service topology, port conventions, and cross-service visibility.
- Platform can execute governed admin actions against individual services.
- Platform aggregates inventory and status across repos.
- Shared Doppler secrets come from the platform project unless a secret is explicitly service-owned.
- Users and coding agents should not need to manually reason about container startup order or duplicate infra scripts.

Suite mode is the preferred path for:

- end-to-end validation
- multi-service debugging
- onboarding new engineers
- platform health reviews
- cross-service inventory and admin operations
- future platform admin UI workflows

### Standalone Mode

Standalone mode remains first-class. It is not a fallback or a deprecated path.

In standalone mode:

- a service repo can be cloned, configured, tested, and run independently
- service-local commands continue to exist for service runtime, tests, migrations, and service-owned admin operations
- the service may use the same shared port and dependency conventions as suite mode
- the service can either connect to platform-owned shared infra or to its own narrowly scoped local fallback if that remains necessary

Standalone mode exists for:

- focused service development
- service-only debugging
- isolated testing
- service repo usability for contributors who are not running the full suite

## Ownership Boundaries

### Platform-Owned Concerns

Platform owns concerns that must be coherent across the suite:

- shared infrastructure lifecycle
- shared container topology and service discovery
- canonical local ports and container names
- shared runtime conventions for Docker Compose and service boot order
- suite-level health aggregation
- cross-service inventory and operational visibility
- cross-service action routing and guardrails
- suite-level documentation for shared infra, shared DB topology, shared Auth0 topology, and shared Doppler model
- platform admin UI and API for local oversight
- audit trail and confirmation model for destructive operations

### Service-Owned Concerns

Each service repository owns concerns that are specific to its domain, runtime, or data:

- migration files and migration ordering
- schema/table reset semantics for its own tables
- service-specific verification logic
- service-specific seed data
- Auth0 audiences, roles, scopes, and resource-specific expectations for that service
- domain API contracts and request/response semantics
- runtime behavior and dependency handling inside the service
- service-level tests and quality gates
- service-only secrets that should not be duplicated into platform ownership
- service dashboards, emitted metrics, and emitted traces specific to service behavior

### Shared But Governed By Platform

Some concerns are shared across repos but should still be centrally governed:

- canonical host ports
- infrastructure service names
- health endpoint conventions and service registry mapping
- naming conventions for shared environment variables
- shared Doppler key naming
- cross-repo docs standards
- platform-visible metadata contracts
- baseline Prometheus/Grafana/Jaeger runtime topology and scrape/discovery configuration

These concerns should be standardized in platform docs and surfaced through platform tooling, even if the consuming code lives in the service repos.

## Concern Matrix

| Concern | Platform Owns | Service Owns | Notes |
|---|---|---|---|
| Docker Compose and shared infra | Yes | No | Single source of truth in `card-fraud-platform` |
| Shared local ports | Yes | No | Services consume, platform governs |
| Service runtime code | No | Yes | No movement to platform |
| Migrations and DB semantics | No | Yes | Platform may invoke, not reimplement |
| Shared DB topology docs | Yes | No | One suite-level explanation |
| Auth0 topology overview | Yes | No | Central overview; service details remain local |
| Auth0 resource rules per service | No | Yes | Audience/scope/role specifics remain service-owned |
| Doppler shared secrets | Yes | Partly | Platform owns shared runtime keys |
| Doppler service-only secrets | No | Yes | LLM, service-only APIs, or service-only credentials |
| Inventory and read-only status | Yes | Partly | Platform aggregates; services expose metadata |
| Admin action implementation | No | Yes | Platform routes to service adapters |
| Admin action orchestration | Yes | No | Platform is the single operator surface |
| Observability infra configuration | Yes | Partly | Platform owns scrape/discovery baseline; services own emitted telemetry and service dashboards |

## Why Not Move Everything Into Platform

Moving Auth0 setup logic, DB reset logic, or service-specific verification into platform would reduce one kind of duplication while creating a worse coupling problem:

- service logic would be copied or mirrored in another repo
- platform would need to track service-specific data model changes directly
- ownership would become ambiguous
- service repos would lose standalone correctness
- the platform would become a brittle script collection rather than a control plane

The correct model is not "move everything to platform". The correct model is "move the operator surface to platform and keep implementation ownership with the service".

## Control Plane Interaction Model

The platform must expose one operator surface for all repos.

That surface can be CLI-only at first and later backed by a local UI. The platform should be able to drive actions such as:

- status and health for all services
- scoped DB verification for a single service
- scoped schema reset for a single service
- Auth0 bootstrap and verification for a single service
- Kafka and Redis dependency verification for services that need them
- seeding and replay operations that remain service-owned but platform-triggered

The platform does not need to know the service internals to do this. It needs a stable registry plus adapter contract, defined in `14-service-registry-format.md`.

## Design Rules For The Next Phase

1. Keep suite mode and standalone mode equally supported.
2. Centralize orchestration and visibility in platform.
3. Do not duplicate service-specific logic in platform.
4. Establish registry, ownership maps, and read-only inventory before adding destructive actions.
5. Treat destructive actions as governed operations with scope, auditability, and explicit confirmation.
6. Standardize metadata, command shape, and docs structure before refactoring implementation.

## Success Criteria

This operating model is successful when:

- a new engineer can run the full suite from platform alone
- a service engineer can still work from a single repo without platform lock-in
- platform can show end-to-end status and topology across the suite
- repeated infra/bootstrap logic shrinks substantially
- docs duplication around shared concerns is reduced
- service ownership remains explicit and enforceable

