# Docs And Governance Model

> Status: approved

## Objective

Define the documentation governance model that supports the platform control plane architecture.

The current suite has improved docs structure, but shared operational topics still tend to appear in multiple repos. The next step is not to write more docs everywhere. It is to make platform the canonical location for suite-level knowledge and keep service repos focused on service-specific information.

## Publishing Principle

Document once at the suite level when the steps or rules are genuinely shared.

Document in the service repo only when the behavior is service-specific.

This rule reduces duplication without losing service-level correctness.

## Canonical Docs That Must Live In Platform

`card-fraud-platform` should become the authoritative home for all suite-level guidance, including:

- shared infrastructure topology
- shared ports, container names, and service discovery conventions
- suite startup/shutdown/status flow
- suite-level Doppler ownership model
- shared Auth0 topology overview
- shared DB topology overview
- platform control plane operating model
- admin action contract
- cross-service inventory model
- future platform admin UI model
- cross-repo documentation standards

These topics should not be fully duplicated in service repos.

## Docs That Must Remain In Service Repos

Service repos should keep documentation that is materially specific to that service.

Examples:

- domain models
- service-specific API contracts
- service-specific data semantics
- migration and schema semantics
- service-specific auth rules and enforcement behavior
- service-specific setup deltas
- service-specific runbooks and failure modes
- service-specific performance and testing guidance

## Shared Topic Handling Rules

### Auth0

Platform should own the suite-level Auth0 overview:

- which services use Auth0
- which use gateway auth versus in-process validation
- which audiences/clients exist conceptually
- ownership boundaries and action routing

Service repos should keep:

- exact service-specific scopes, roles, callbacks, grants, or enforcement semantics
- service-specific bootstrap and verify details when they differ materially

### Database

Platform should own:

- the shared local DB topology
- the single-database shared-suite model
- service-to-schema/table ownership map
- operator guidance for safe scoped DB actions from the platform

Service repos should keep:

- migration details
- reset semantics for service-owned objects
- schema verification logic
- data model details tied to service behavior

### Doppler

Platform should own:

- the suite ownership model for secrets and configs
- shared key naming conventions
- how suite mode and standalone mode relate

Service repos should keep:

- service-only secret requirements
- standalone-specific delta guidance

### Infra

Platform should own all documentation for:

- PostgreSQL
- MinIO
- Redis
- Redpanda/Kafka
- Jaeger
- Prometheus
- Grafana

Service repos may link to platform docs instead of restating the same infra setup steps.

## Publishing Rules For Service Repos

When a service repo references a shared topic, it should:

- link to the canonical platform doc
- document only the service-specific delta
- avoid repeating the full shared setup unless the steps truly diverge

A good service-repo pattern is:

- short shared dependency note
- link to canonical platform suite doc
- service-specific behavior section

## Docs Structure Standard

The existing curated docs structure remains the standard:

- `docs/01-setup`
- `docs/02-development`
- `docs/03-api`
- `docs/04-testing`
- `docs/05-deployment`
- `docs/06-operations`
- `docs/07-reference`

Platform-specific control-plane design lives in:

- `docs/02-development/platform-control-plane/`

This is appropriate because the material is architecture and operating-model design, not temporary scratch planning.

## Files That Must Not Be Published

Tracked docs must not include:

- todo files
- status files
- archive folders
- `SESSION_HANDOFF.md`
- session handoff notes under any other name
- transient scratch plans
- raw report dumps unless a repo explicitly carves out a governed area for generated reports

The platform repo should set the standard and other repos should follow it.

## Review Standard For Published Design Docs

A platform design doc is publishable only when it is:

- current-state aware
- future-state explicit
- ownership-complete
- free of implementation ambiguity
- free of temporary brainstorming language
- aligned with actual repo boundaries
- testable by implementation, meaning an implementer can verify the resulting work against the document

## What Moves To Platform In The Next Documentation Realignment

- full shared infra setup explanations
- suite-level Auth0 architecture
- suite-level DB topology and ownership map
- suite-level Doppler model
- suite-level operator workflows
- platform admin and control-plane terminology

## What Stays Local After Realignment

- rule-management compiler/publisher specifics
- rule-engine hot-path, Redis, and runtime specifics
- transaction-management idempotency/replay semantics
- portal user workflows and frontend-specific contracts
- ops-agent model/provider/runtime specifics
- e2e/load-testing scenario design and performance methodology

## Success Criteria

The docs governance model is successful when:

- a new engineer can understand the suite from platform docs first
- service docs become shorter and more specific
- repeated shared setup guides stop proliferating
- cross-repo ownership boundaries are obvious from the docs
- coding agents have one canonical source for suite-level behavior

