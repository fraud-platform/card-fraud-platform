# Inventory And Observability Model

> Status: approved

## Objective

Define the read-only oversight model for the platform control plane.

The platform admin must be able to show what exists across the suite, who owns it, whether it is healthy, and how the parts relate. This is the foundation for end-to-end oversight and later controlled actions.

The first phase is read-mostly. Data exploration can come later.

## Design Principle

Read-only inventory comes before write operations.

The platform should first answer these questions reliably:

- what services exist in the suite?
- what ports, health endpoints, and dependencies does each service use?
- which repo owns which capability?
- which schemas, tables, indexes, topics, buckets, or auth resources belong to which service?
- what is healthy, degraded, missing, or misconfigured?

Only after that baseline is reliable should the platform add richer control flows.

## Inventory Categories

### 1. Service Inventory

The platform must present a service registry with at least:

- canonical service id
- repo path
- runtime type (`FastAPI`, `Quarkus`, `React`, test harness, agent service)
- local host port
- health endpoint
- startup dependency list
- current runtime state
- whether the service supports standalone mode
- whether the service supports platform admin actions and which ones
- auth model classification
- engine family where applicable

Recommended initial services:

- rule-management
- rule-engine-auth
- rule-engine-monitoring
- transaction-management
- intelligence-portal
- ops-analyst-agent
- e2e-load-testing

### 2. Infrastructure Inventory

The platform must show the status and role of shared infra:

- PostgreSQL
- MinIO
- Redis
- Redpanda/Kafka
- Jaeger
- Prometheus
- Grafana

For each infra dependency, platform should track:

- container name
- port mapping
- basic health
- which services depend on it
- whether it is part of the platform-owned shared runtime
- baseline observability configuration ownership where relevant

### 3. Database Inventory

The platform admin should show database inventory at an operational level.

Initial read-only fields:

- database name
- schema ownership mapping
- per-service table count
- per-service index count
- per-service migration state summary
- service-owned tables list
- service-owned reset boundary summary

Deferred capabilities:

- row-level exploration
- query execution
- mutation from platform UI

The key design requirement is that platform can answer questions such as:

- how many tables does rule-management own?
- how many indexes does transaction-management own?
- what schemas or tables are currently present for ops-agent?
- which service owns the tables that a destructive reset would affect?

### 4. Messaging Inventory

Platform must expose Kafka/Redpanda inventory:

- broker status
- topics
- partitions
- replication data if applicable locally
- consumer groups
- lag where available
- topic ownership mapping by service

Key operator questions:

- which topics exist for the suite?
- which services publish and consume them?
- what is the health of the broker?
- where is lag accumulating?

### 5. Redis Inventory

Platform should expose Redis at a summary level:

- health
- memory usage summary
- keyspace summary
- known logical usage by service
- TTL and eviction risk summary where visible

This is not a requirement to display individual business keys in v1. The immediate need is platform-level visibility into whether Redis is present and whether the rule engines and future services are relying on it in the expected way.

### 6. Object Storage Inventory

Platform should expose MinIO inventory:

- bucket names
- bucket ownership
- artifact count or manifest count at a summary level
- latest ruleset artifact or manifest metadata where safe to expose
- storage health and accessibility

This gives platform operators visibility into ruleset publication and runtime artifact availability without turning platform into a business data browser.

### 7. Auth Inventory

Platform should provide Auth0 ownership visibility for services that own in-process auth configuration:

- API audiences where the service owns them
- client/application ownership
- callback and logout URI ownership for the portal where applicable
- roles and scope families by service
- whether bootstrap/verify is supported for the service

Gateway-auth services should still be represented, but as gateway-auth services rather than as in-process audience owners.

### 8. Doppler Inventory

Platform should show configuration linkage rather than secret values.

Required visibility:

- Doppler project per repo
- environment config names in use (`local`, `test`, `prod`)
- required secret names by ownership domain
- missing or drifted shared keys
- whether a service has service-only secrets outside platform ownership

Platform should never expose sensitive secret values in inventory views.

## Read-Only Inventory Versus Actionable Operations

### Read-Only Inventory

Read-only inventory answers what exists and what its state is.

Examples:

- show all services and their health
- show all topics and consumer groups
- show table/index counts by service
- show which bucket contains ruleset artifacts
- show which Auth0 audience belongs to which service
- show which Doppler project/config a service depends on

### Actionable Operations

Actionable operations change state.

Examples:

- reset schema
- bootstrap Auth0 resources
- create topics
- reseed demo data
- restart a service

The platform admin UI should present inventory and actions as separate concepts. Read-only overview should be the default landing model.

## Data Model For The Future Platform Admin

A practical control-plane model needs canonical entities:

- `Service`
- `EngineFamily`
- `Dependency`
- `AdminAction`
- `SchemaOwnership`
- `TopicOwnership`
- `BucketOwnership`
- `AuthOwnership`
- `SecretOwnership`
- `RuntimeStatus`
- `ActionResult`

`EngineFamily` exists to model shared-but-distinct runtimes such as the AUTH and MONITORING rule-engine services.

This entity model allows the future UI to show one unified suite map rather than a collection of unrelated dashboards.

## Observability Model

The platform admin is not a replacement for Prometheus, Grafana, or Jaeger. It is the control-plane entrypoint that links those systems with suite context.

The platform should aggregate:

- health and readiness
- service dependency state
- basic runtime status
- ownership metadata
- recent action outcomes
- baseline observability config ownership

It should then link out to deeper systems:

- Grafana for dashboard views
- Prometheus for raw metrics
- Jaeger for traces
- service-native logs where appropriate

## Priority Order

### Phase 1

- service registry and service inventory
- infra inventory
- health aggregation
- ownership mapping
- links to external observability tools
- concrete DB/table/index ownership artifact per service

### Phase 2

- DB schema/table/index counts by service
- Kafka topics and consumer groups
- Redis summary and MinIO summary
- Doppler ownership and drift checks
- Auth ownership registry

### Future Horizon

- optional data view and richer drilldown
- trend or event history where useful
- richer action telemetry

## Success Criteria

The inventory model is successful when a platform admin can answer, from one place:

- what is running?
- what is broken?
- who owns each dependency or resource?
- what can be safely reset, verified, or bootstrapped?
- where should deeper troubleshooting happen next?


