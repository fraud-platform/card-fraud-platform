# Cross-Repo Summary

> Status: approved

## Purpose

This file is the cross-repo implementation summary for the control-plane design pack. It is the fastest way to understand which services expose which capabilities, which shared resources they own, and what the platform must aggregate.

When a per-repo plan and this summary overlap, this file is the suite-level summary and the per-repo plan supplies service-specific rationale and deltas.

## Service Capability Matrix

| Service | Runtime | Engine Family | Port | Canonical Health Path | Auth Model | Action Domains | DB Owner | Messaging Owner | Storage Owner | Notes |
|---|---|---|---:|---|---|---|---|---|---|---|
| `rule-management` | FastAPI | n/a | 8000 | `/api/v1/health` | in-process | `service`, `db`, `auth`, `seed`, `storage` | Yes | No | publishes ruleset artifacts | Owns compiler/publisher and rule governance |
| `rule-engine-auth` | Quarkus | `rule-engine` | 8081 | `/v1/evaluate/health` | gateway | `service`, `messaging`, `storage`, `runtime` | No | publishes decisions | reads ruleset artifacts | Latency-critical AUTH runtime |
| `rule-engine-monitoring` | Quarkus | `rule-engine` | 8082 | `/v1/evaluate/health` | gateway | `service`, `messaging`, `storage`, `runtime` | No | publishes monitoring decisions | reads ruleset artifacts | Engine-family sibling to AUTH |
| `transaction-management` | FastAPI | n/a | 8002 | `/api/v1/health` | in-process | `service`, `db`, `auth`, `messaging`, `seed` | Yes | consumes and manages topics/groups | No | Owns replay/idempotency state |
| `intelligence-portal` | React/Vite | n/a | 5173 | `/health` | SPA/in-browser | `service`, `auth` | No | No | No | Business UI, not control plane |
| `e2e-load-testing` | Python/Locust | n/a | 8089 | UI route only | test-client | `service`, `verify`, `seed` | No | No | consumes suite topology | Harness only; not a runtime owner |
| `ops-analyst-agent` | FastAPI | n/a | 8003 | `/api/v1/health/ready` | in-process | `service`, `db`, `auth`, `seed`, `verify` | Yes | indirect dependency via suite | No | Dual secret ownership model |
| `card-fraud-platform` | Python/Compose | n/a | n/a | aggregated | n/a | `service`, `db`, `auth`, `messaging`, `storage`, `runtime`, `diagnostics` | shared topology only | shared topology only | shared topology only | Control plane and orchestrator |
| `card-fraud-analytics` | deferred | n/a | n/a | n/a | n/a | deferred | deferred | deferred | deferred | Explicitly out of current planning scope |

## Shared Resource Ownership Summary

| Resource Class | Platform Role | Primary Service Owners |
|---|---|---|
| PostgreSQL topology and credentials | authoritative shared runtime owner | `rule-management`, `transaction-management`, `ops-analyst-agent` own table/migration semantics |
| MinIO bucket topology | authoritative shared runtime owner | `rule-management` publishes artifacts; rule engines consume |
| Redis runtime | authoritative shared runtime owner | rule-engine services own runtime usage semantics |
| Redpanda/Kafka runtime | authoritative shared runtime owner | rule-engine services publish; `transaction-management` owns major consumer semantics |
| Auth0 topology overview | authoritative suite doc owner | service repos own client/audience/role specifics |
| Doppler shared secret naming | authoritative shared config owner | service repos own service-only and standalone-only values |
| Prometheus/Grafana/Jaeger infra | authoritative shared observability runtime owner | services own emitted metrics, traces, and service-specific dashboards |

## Destructive Action Summary

| Service | Destructive Actions Expected | Notes |
|---|---|---|
| `rule-management` | `db-reset-schema`, `db-reset-data` | Service owns exact schema object boundaries |
| `rule-engine-auth` | none initially | Runtime-only service in this design phase |
| `rule-engine-monitoring` | none initially | Runtime-only service in this design phase |
| `transaction-management` | `db-reset-tables`, `db-reset-data` | Table-scoped reset must include DLQ/review state policy |
| `intelligence-portal` | none | No destructive data ownership in this phase |
| `e2e-load-testing` | none | Harness is not a data owner |
| `ops-analyst-agent` | `db-reset-tables`, `db-reset-data` | Scoped only to ops-agent-owned tables |

## Phase Summary

### Phase 1 - Declare

- publish the service registry
- publish the adapter manifest convention
- produce DB/table/index ownership maps
- publish topic/bucket/auth ownership maps
- realign docs to platform-first shared topics

### Phase 2 - Operate

- route service-owned actions through platform
- aggregate health, inventory, and ownership state in platform
- reduce duplicate shared infra wrappers in service repos
- upgrade platform status into a real suite control-plane view

### Future Horizon

- richer admin UI
- data drilldown views
- action history persistence and trends

## Implementation Notes

- This file is intentionally matrix-heavy so the per-repo docs do not have to repeat the entire suite structure.
- Any later implementation should keep this summary synchronized with `14-service-registry-format.md`.
