# Platform Control Plane

> Status: approved

Authoritative architecture and design set for evolving `card-fraud-platform` from a Docker Compose orchestrator into the suite control plane for the full Card Fraud service estate.

## Purpose

This folder defines the target operating model only. It does not implement code, command refactors, or UI changes.

The design goal is to make `card-fraud-platform` the single local control plane for:

- shared infrastructure lifecycle
- cross-service operational visibility
- governed admin actions
- shared documentation and configuration standards
- inventory and health oversight across the full suite

while preserving first-class standalone operation for each service repository.

## Document Index

| File | Purpose | Status |
|---|---|---|
| `README.md` | control-plane design pack index | approved |
| `00-operating-model.md` | control-plane operating model and ownership boundaries | approved |
| `01-admin-action-contract.md` | standard admin action contract and guardrails | approved |
| `02-inventory-and-observability-model.md` | inventory, topology, and read-only observability model | approved |
| `03-secrets-and-configuration-ownership.md` | Doppler ownership and shared configuration rules | approved |
| `04-docs-and-governance-model.md` | documentation consolidation and publishing model | approved |
| `05-card-fraud-platform.md` | future-state plan for the platform repository itself | approved |
| `06-card-fraud-rule-management.md` | future-state plan for rule management | approved |
| `07-card-fraud-rule-engine-auth.md` | future-state plan for AUTH runtime | approved |
| `08-card-fraud-rule-engine-monitoring.md` | future-state plan for MONITORING runtime | approved |
| `09-card-fraud-transaction-management.md` | future-state plan for transaction management | approved |
| `10-card-fraud-intelligence-portal.md` | future-state plan for the business UI | approved |
| `11-card-fraud-e2e-load-testing.md` | future-state plan for suite validation and load testing | approved |
| `12-card-fraud-ops-analyst-agent.md` | future-state plan for ops-agent integration | approved |
| `13-cross-repo-summary.md` | cross-repo capability, ownership, and runtime summary | approved |
| `14-service-registry-format.md` | concrete service registry and adapter manifest format | approved |
| `15-phase-1-implementation-backlog.md` | phased execution backlog derived from the approved design pack | approved |
| `16-phase-2-platform-internals-design.md` | detailed technical design for Phase 2 platform internals | review |
| `17-platform-adapter-schema.md` | canonical schema and validation rules for `platform-adapter.yaml` | approved |
| `18-db-ownership.md` | platform-owned database ownership matrix (tables and indexes) | approved |
| `19-kafka-ownership.md` | platform-owned Kafka topic and consumer group ownership matrix | approved |
| `20-minio-ownership.md` | platform-owned MinIO bucket and artifact ownership matrix | approved |
| `21-auth0-ownership.md` | platform-owned Auth0 ownership boundaries and responsibilities | approved |
| `22-doppler-ownership.md` | platform-owned Doppler key ownership matrix and governance | approved |
| `23-phase-implementation-validation.md` | validation report for Phase 1 and Phase 2 implementation status | approved |

## Design Boundaries

- Scope is local-first platform architecture and operator workflow.
- CI/CD is intentionally out of scope.
- Data exploration beyond high-level inventory is deferred.
- Service business logic remains service-owned.
- The control plane orchestrates and governs; it does not absorb domain internals.
- `card-fraud-analytics` is explicitly deferred; it is referenced as a future service but not included in the implementation planning scope of this design pack.
