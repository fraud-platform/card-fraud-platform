# AGENTS.md - Card Fraud Platform

This is the **shared infrastructure orchestrator** for the Card Fraud suite of services.

> **IMPORTANT:** This project uses **Doppler** as the secrets manager.
> Local startup requires Doppler-injected secrets.

---

## Cross-Repo Agent Standards

- Secrets: Doppler-only workflows. Do not create or commit `.env` files.
- Commands: use repository wrappers from `pyproject.toml` or `package.json`; avoid ad-hoc commands.
- Git hooks: run `git config core.hooksPath .githooks` after clone to enable pre-push guards.
- Docs publishing: keep only curated docs in `docs/01-setup` through `docs/07-reference`, plus `docs/README.md` and `docs/codemap.md`.
- Docs naming: use lowercase kebab-case for docs files. Exceptions: `README.md`, `codemap.md`, and generated contract files.
- Never commit docs/planning artifacts named `todo`, `status`, `archive`, or session notes.
- If behavior, routes, scripts, ports, or setup steps change, update `README.md`, `AGENTS.md`, `docs/README.md`, and `docs/codemap.md` in the same change.
- Keep health endpoint references consistent with current service contracts (for APIs, prefer `/api/v1/health`).
- Preserve shared local port conventions from `card-fraud-platform` unless an explicit migration is planned.
- Before handoff, run the repo's local lint/type/test gate and report the exact command + result.

## Quick Start

```powershell
# 1. Install uv if not already installed
winget install --id Astral-sh.uv

# 2. Clone this repo alongside the service repos
cd C:\Users\kanna\github
git clone <platform-repo-url> card-fraud-platform

# 3. Install dependencies
cd card-fraud-platform
uv sync

# 4. Start full platform stack (shared infra + applications)
doppler run -- uv run platform-up

# 5. Check status
uv run platform-status

# 6. Run the local quality gate
uv run platform-check
```

## What This Project Manages

### Shared Infrastructure (docker-compose.yml)

| Service | Container | Port(s) | Used By |
|---------|-----------|---------|---------|
| PostgreSQL 18 | `card-fraud-postgres` | 5432 | rule-management, transaction-management, portal, ops-analyst-agent, analytics |
| MinIO (S3) | `card-fraud-minio` | 9000, 9001 | rule-management (write), rule-engine (read), analytics |
| Redis 8.4 | `card-fraud-redis` | 6379 | rule-engine (velocity counters) |
| Redpanda (Kafka) | `card-fraud-redpanda` | 9092, 9644 | rule-engine (publish), transaction-management (consume) |
| Redpanda Console | `card-fraud-redpanda-console` | 8083 | Browser (topic management) |
| Jaeger | `card-fraud-jaeger` | 16686, 4317, 4318 | All services (distributed tracing) |
| Prometheus | `card-fraud-prometheus` | 9090 | Metrics scraping from all services |
| Grafana | `card-fraud-grafana` | 3000 | Metrics visualization dashboards |

### Application Containers (docker-compose.apps.yml)

| Service | Container | Host Port | Container Port | Source Repo |
|---------|-----------|-----------|----------------|-------------|
| Rule Management API | `card-fraud-rule-management` | 8000 | 8000 | ../card-fraud-rule-management |
| Rule Engine AUTH | `card-fraud-rule-engine-auth` | 8081 | 8081 | ../card-fraud-rule-engine-auth |
| Rule Engine MONITORING | `card-fraud-rule-engine-monitoring` | 8082 | 8081 | ../card-fraud-rule-engine-monitoring |
| Transaction Management API | `card-fraud-transaction-management` | 8002 | 8002 | ../card-fraud-transaction-management |
| Intelligence Portal | `card-fraud-intelligence-portal` | 5173 | 5173 | ../card-fraud-intelligence-portal |
| Ops Analyst Agent | `card-fraud-ops-analyst-agent` | 8003 | 8003 | ../card-fraud-ops-analyst-agent |
| Locust (load testing) | `card-fraud-locust` | 8089 | 8089 | ../card-fraud-e2e-load-testing |

## Commands

| Command | Description |
|---------|-------------|
| `doppler run -- uv run platform-up` | Start full platform stack (shared infra + applications) |
| `doppler run -- uv run platform-up -- --load-testing` | Start platform stack + Locust load-testing profile |
| `uv run platform-down` | Stop all containers (keep data) |
| `uv run platform-status` | Show suite-aware control-plane service status summary |
| `uv run platform-status --json` | Emit machine-readable service health summary |
| `uv run platformctl status` | Show control-plane status via root control-plane CLI |
| `uv run platformctl inventory <scope>` | Show ownership-aware inventory (`all`, `services`, `infra`, `redis`, `db`, `messaging`, `storage`, `auth`, `secrets`) |
| `uv run platformctl registry validate` | Validate registry entries and adapter manifest presence |
| `uv run platform-reset` | Stop and remove all data (fresh start) |
| `uv run platform-check` | Run the repo's local lint/type/test gate |
| `uv run platform-sync-secrets` | Sync shared local secrets across platform/rule-mgmt/txn-mgmt |
| `doppler run -- python scripts/infra_only.py` | Infra orchestrator (checks status, starts only if down) |

### E2E Run Guardrail (ops-agent)

For ops-agent e2e runs, run infra and guardrails in one session before any matrix/scenario tests:

```powershell
doppler run --project card-fraud-platform --config local -- `
  docker compose -f C:/Users/kanna/github/card-fraud-platform/docker-compose.yml `
  -f C:/Users/kanna/github/card-fraud-platform/docker-compose.apps.yml `
  --profile platform up -d --build transaction-management ops-analyst-agent
```

Validation steps:

- `curl http://localhost:8003/api/v1/health/ready`
- `curl http://localhost:8002/api/v1/health`
- `(cd C:/Users/kanna/github/card-fraud-ops-analyst-agent; doppler run --config local -- uv run pytest tests/e2e/test_scenarios.py::test_llm_chat_preflight -v)`

Do not skip the preflight before running `run_e2e_matrix_detailed.py` or full `tests/e2e/test_scenarios.py`.

## Architecture

```
card-fraud-network (Docker bridge)
│
│  Infrastructure
├── card-fraud-postgres        (5432)  ← rule-mgmt, txn-mgmt, portal, ops-analyst-agent, analytics
├── card-fraud-minio           (9000)  ← rule-mgmt (write), rule-engine (read)
├── card-fraud-redis           (6379)  ← rule-engine, analytics (future)
├── card-fraud-redpanda        (9092)  ← rule-engine (pub), txn-mgmt (sub)
├── card-fraud-redpanda-console(8083)
├── card-fraud-jaeger          (16686) ← distributed tracing UI
├── card-fraud-prometheus      (9090)  ← metrics scraping
└── card-fraud-grafana        (3000)  ← metrics dashboards
│
│  Applications [platform profile]
├── card-fraud-rule-management   (8000)
├── card-fraud-rule-engine-auth    (8081)
├── card-fraud-rule-engine-monitoring (8082)
├── card-fraud-transaction-management (8002)
├── card-fraud-ops-analyst-agent    (8003)
└── card-fraud-intelligence-portal  (5173)
│
│  Testing [load-testing profile]
└── card-fraud-locust            (8089)
```

All containers share the `card-fraud-network` bridge network. Within Docker,
services reference each other by container service name (e.g., `postgres`, `redis`, `minio`).
From the host, use `localhost` with the mapped ports.

## Connection Strings (for individual projects)

```
PostgreSQL : postgresql://postgres:<POSTGRES_ADMIN_PASSWORD>@localhost:5432/fraud_gov
Redis      : redis://localhost:6379
MinIO API  : http://localhost:9000
MinIO UI   : http://localhost:9001
Kafka      : localhost:9092
```

## Database

Single PostgreSQL instance with single database (`fraud_gov`) and single schema.
All services query the same tables, enabling cross-service joins for fraud operations.

**Users created on first start:**
- `fraud_gov_app_user` (read/write) - rule-management, transaction-management
- `fraud_gov_analytics_user` (read-only) - intelligence-portal, analytics

Schema migrations are managed by each application service (Alembic, etc.).

### Reset Scope Policy

- `db-reset-schema` is reserved for `rule-management` only (high-risk shared-schema action).
- `db-reset-schema` requires `--yes`, exact `--confirm`, and `--schema-reset-ack RESET_SHARED_SCHEMA`.
- Other services use `db-reset-tables` and/or `db-reset-data` only.
- `db-reset-tables` must never alias to `db-reset-schema`.

## What is MinIO / MinIO-init?

**MinIO** is an S3-compatible object storage server. It stores compiled ruleset artifacts
in the `fraud-gov-artifacts` bucket. The rule-management service publishes compiled
rulesets here; the rule-engine reads them at runtime.

**MinIO-init** is a one-shot init container that runs `mc` (MinIO Client) to create the
`fraud-gov-artifacts` bucket on first startup. It exits with code 0 after setup completes.
This is normal -- the container will show "Exited (0)" in `docker ps -a`. It only needs to
run once; on subsequent starts, `--ignore-existing` skips bucket creation.

## What is Redpanda?

**Redpanda** is a Kafka-compatible event streaming platform. The rule-engine publishes
fraud decision events to the `fraud.card.decisions.v1` topic. The transaction-management
service consumes these events for persistence and analyst workflows.

**Redpanda Console** (port 8083) provides a browser UI for viewing topics, messages, and
consumer groups.

## Adding a New Service

Step-by-step guide for adding a new application service to the platform:

1. **Create a Dockerfile** in the new service's repo following these best practices:
   - Use multi-stage builds (builder + runtime stages)
   - Use slim/alpine base images (e.g., `python:3.14-slim`, `eclipse-temurin:25-jre-alpine`)
   - Create a non-root user (`appuser`) and switch to it before `CMD`
   - Include a `HEALTHCHECK` instruction (curl or wget to a health endpoint)
   - Install only `curl` (or `wget`) in runtime stage for health checks
   - Set `PYTHONUNBUFFERED=1` and `PYTHONDONTWRITEBYTECODE=1` for Python services

2. **Create a `.dockerignore`** in the service repo to exclude:
   - Tests, docs, IDE files, git history
   - Build artifacts, virtual environments
   - Scripts and CLI tools not needed at runtime

3. **Add a service block** in `docker-compose.apps.yml`:
   - Set a unique host port (check the port table above for allocations)
   - Add environment variables for infrastructure connections (use Docker service names, not localhost)
   - Add `depends_on` with `condition: service_healthy` for required infrastructure
   - Add a `healthcheck` matching the Dockerfile
   - Include `profiles: [platform]`

4. **If new infrastructure is needed** (e.g., new DB user), update `init-db/01-create-users.sql`

5. **Update documentation**:
   - Update this AGENTS.md (port table, architecture diagram)
   - Update README.md (application table, health check URLs)
   - Add "Shared Infrastructure" section to the new service's AGENTS.md

### Docker Image Best Practices

All Dockerfiles in the platform follow these conventions:

| Practice | Why |
|----------|-----|
| Multi-stage builds | Smaller images (no build tools in runtime) |
| Slim/alpine base | Minimal attack surface, smaller download |
| Non-root user | Security: containers don't run as root |
| Health checks | Docker and compose can monitor service health |
| `.dockerignore` | Faster builds, no secrets leaked into images |
| Frozen lock files | Reproducible builds (`uv sync --frozen`, `pnpm install --frozen-lockfile`) |

**Note on container users:**
- **Infrastructure services** (PostgreSQL, MinIO, Redis, Redpanda, Jaeger, Prometheus, Grafana) run as root by design, following official image conventions.
- **Application services** (rule-management, rule-engine, transaction-management, ops-analyst-agent, intelligence-portal) should use non-root users in their Dockerfiles.

### Port Allocation Convention

| Range | Usage |
|-------|-------|
| 3000 | Grafana (Metrics dashboards) |
| 5432 | PostgreSQL |
| 6379 | Redis |
| 8000-8003 | Backend APIs (FastAPI, Quarkus) |
| 5173 | Frontend (Intelligence Portal) |
| 8083 | Redpanda Console |
| 8089 | Load testing (Locust) |
| 9090 | Prometheus (Metrics) |
| 9000-9001 | MinIO (API, Console) |
| 9092 | Kafka (Redpanda) |
| 16686 | Jaeger (Tracing UI) |
| 4317-4318 | Jaeger (OTLP gRPC/HTTP) |
| 5173 | Frontend (Intelligence Portal) |
| 8083 | Redpanda Console |
| 8089 | Load testing (Locust) |
| 9000-9001 | MinIO (API, Console) |
| 9092 | Kafka (Redpanda) |

## Repository Layout

```
github/
├── card-fraud-platform/                  # THIS REPO - infrastructure orchestrator
├── card-fraud-rule-management/           # FastAPI - rule CRUD
├── card-fraud-rule-engine-auth/          # Quarkus - AUTH evaluation engine
  |-- card-fraud-rule-engine-monitoring/    # Quarkus - MONITORING evaluation engine
├── card-fraud-transaction-management/    # FastAPI - transaction processing
├── card-fraud-intelligence-portal/       # React - fraud ops UI
├── card-fraud-ops-analyst-agent/         # FastAPI - autonomous fraud analyst assistant
└── card-fraud-analytics/                 # (future)
```

## Windows Notes

- Use `uv` (installed via `winget install --id Astral-sh.uv`)
- Docker commands use `docker compose` (not `docker-compose`)
- All scripts use forward slashes in paths

---

**Last Updated:** 2026-03-08
