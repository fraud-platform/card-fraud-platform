# Card Fraud Platform

Shared infrastructure orchestrator for the Card Fraud suite of services.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (running)
- [uv](https://docs.astral.sh/uv/) (`winget install --id Astral-sh.uv`)
- [Git](https://git-scm.com/)
- [Doppler CLI](https://docs.doppler.com/docs/install-cli) (secrets management)

## Repository Layout

All repos should be cloned as siblings in the same parent directory:

```
github/
├── card-fraud-platform/                  # THIS REPO - infrastructure orchestrator
├── card-fraud-rule-management/           # FastAPI - rule CRUD & compilation
├── card-fraud-rule-engine/               # Quarkus - real-time evaluation engine
├── card-fraud-transaction-management/    # FastAPI - transaction processing
├── card-fraud-intelligence-portal/       # React - fraud operations UI
└── card-fraud-analytics/                 # (future)
```

Clone all repos:

```powershell
cd C:\Users\kanna\github
# Clone each repo (replace with your org URL)
git clone <url>/card-fraud-platform
git clone <url>/card-fraud-rule-management
git clone <url>/card-fraud-rule-engine
git clone <url>/card-fraud-transaction-management
git clone <url>/card-fraud-intelligence-portal

# Or use the helper script
cd card-fraud-platform
.\clone-all.ps1
```

## Secrets Management (Doppler)

All environment variables are managed centrally via the **card-fraud-platform**
Doppler project. No secrets are hardcoded in compose files or scripts.

### One-Time Setup

```powershell
cd card-fraud-platform

# 1. Login to Doppler (if not already)
doppler login

# 2. Configure this directory (select config: local, test, or prod)
doppler setup
# Project: card-fraud-platform
# Config:  local
```

### Required Secrets

Add these to the **card-fraud-platform** Doppler project (`local` config):

| Variable | Description | Used By |
|----------|-------------|---------|
| **Infrastructure** | | |
| `POSTGRES_ADMIN_PASSWORD` | PostgreSQL superuser password | postgres, rule-mgmt, txn-mgmt |
| `FRAUD_GOV_APP_PASSWORD` | PostgreSQL app user password | rule-mgmt, txn-mgmt |
| `MINIO_ROOT_USER` | MinIO root username | minio, minio-init |
| `MINIO_ROOT_PASSWORD` | MinIO root password | minio, minio-init |
| `S3_ACCESS_KEY_ID` | S3/MinIO access key | rule-mgmt, rule-engine, txn-mgmt |
| `S3_SECRET_ACCESS_KEY` | S3/MinIO secret key | rule-mgmt, rule-engine, txn-mgmt |
| `S3_BUCKET_NAME` | S3 bucket name | minio-init, rule-mgmt, rule-engine, txn-mgmt |
| `S3_REGION` | S3 region | rule-mgmt, rule-engine, txn-mgmt |
| **Auth0** | | |
| `AUTH0_DOMAIN` | Auth0 tenant domain | all services |
| `RULE_MGMT_AUTH0_AUDIENCE` | Rule Management API audience | rule-mgmt |
| `RULE_ENGINE_AUTH0_AUDIENCE` | Rule Engine API audience | rule-engine, locust |
| `TXN_MGMT_AUTH0_AUDIENCE` | Transaction Management API audience | txn-mgmt |
| `RULE_ENGINE_AUTH0_CLIENT_ID` | Rule Engine M2M client ID | rule-engine, locust |
| `RULE_ENGINE_AUTH0_CLIENT_SECRET` | Rule Engine M2M client secret | rule-engine, locust |
| **Portal (build args)** | | |
| `VITE_API_URL` | Backend API URL for portal | portal |
| `VITE_AUTH0_DOMAIN` | Auth0 domain for SPA | portal |
| `VITE_AUTH0_CLIENT_ID` | Auth0 SPA client ID | portal |
| `VITE_AUTH0_AUDIENCE` | Auth0 API audience for SPA | portal |

### Per-Environment Configs

| Config | Usage |
|--------|-------|
| `local` | Local development with Docker |
| `test` | Test/staging environment |
| `prod` | Production deployment |

Switch configs:

```powershell
doppler setup --config local   # or test, prod
```

Keep `test`/`prod` aligned with `local` during local-only development:

```powershell
uv run platform-sync-configs
```

This syncs compose-required keys from `local` to `test` and `prod`, and enforces:
- `APP_ENV=local|test|prod` by config
- `VITE_SENTRY_ENVIRONMENT=local|test|prod` by config

### Individual Project Doppler

Each service also has its own Doppler project for standalone development
(running outside Docker). The platform project is only for docker-compose
orchestration.

| Doppler Project | Used By |
|-----------------|---------|
| `card-fraud-platform` | docker-compose (this repo) |
| `card-fraud-rule-management` | standalone `uvicorn` dev |
| `card-fraud-rule-engine` | standalone `mvn quarkus:dev` |
| `card-fraud-transaction-management` | standalone `uvicorn` dev |
| `card-fraud-intelligence-portal` | standalone `pnpm dev` |

Individual projects only need secrets for their own service. Shared infra
secrets (DB passwords, MinIO credentials, Auth0) live in the platform project.
See `SECRETS_OWNERSHIP.md` for the full ownership matrix.

## Quick Start

```powershell
cd card-fraud-platform

# 1. Install Python dependencies for platform CLI
uv sync

# 2. Configure Doppler (one-time)
doppler setup    # select: card-fraud-platform / local

# 3. Start all shared infrastructure
doppler run -- uv run platform-up

# 4. Verify all services are healthy
uv run platform-status

# 5. (Optional) Start all application containers
doppler run -- uv run platform-up -- --apps
```

## Architecture

```
card-fraud-network (Docker bridge)
│
│  Shared Infrastructure (always running)
├── card-fraud-postgres          (5432)  ← rule-mgmt, txn-mgmt, portal
├── card-fraud-minio             (9000)  ← rule-mgmt (write), rule-engine (read)
├── card-fraud-minio-init        (exit)  ← one-shot bucket creation
├── card-fraud-redis             (6379)  ← rule-engine (velocity counters)
├── card-fraud-redpanda          (9092)  ← rule-engine (pub), txn-mgmt (sub)
├── card-fraud-redpanda-console  (8083)  ← browser topic management
│
│  Application Containers (--apps profile)
├── card-fraud-rule-management   (8000)  ← FastAPI
├── card-fraud-rule-engine       (8081)  ← Quarkus/Java 21
├── card-fraud-transaction-management (8002)  ← FastAPI
├── card-fraud-intelligence-portal (5173)  ← React/Nginx
└── card-fraud-locust            (8089)  ← load testing profile
```

All containers share the `card-fraud-network` bridge network. Within Docker, services
reference each other by service name (e.g., `postgres`, `redis`, `minio`). From the host,
use `localhost` with the mapped ports.

## Shared Infrastructure

| Service | Container | Host Port(s) | Purpose |
|---------|-----------|--------------|---------|
| PostgreSQL 18 | `card-fraud-postgres` | 5432 | Shared `fraud_gov` database |
| MinIO (S3) | `card-fraud-minio` | 9000 (API), 9001 (Console) | Compiled ruleset artifacts |
| MinIO Init | `card-fraud-minio-init` | - | One-shot bucket creation (exits after setup) |
| Redis 8.4 | `card-fraud-redis` | 6379 | Velocity counters, hot reload |
| Redpanda (Kafka) | `card-fraud-redpanda` | 9092 | Decision event streaming |
| Redpanda Console | `card-fraud-redpanda-console` | 8083 | Web UI for topic management |

### What is MinIO / MinIO-init?

**MinIO** is an S3-compatible object storage server. It stores compiled ruleset artifacts
in the `fraud-gov-artifacts` bucket. The rule-management service publishes compiled
rulesets here; the rule-engine reads them at runtime.

**MinIO-init** is a one-shot init container that runs `mc` (MinIO Client) to create the
`fraud-gov-artifacts` bucket on first startup. It exits with code 0 after setup completes.
This is normal -- the container will show "Exited (0)" in `docker ps -a`. It only needs to
run once; on subsequent starts, `--ignore-existing` skips bucket creation.

### What is Redpanda?

**Redpanda** is a Kafka-compatible event streaming platform. The rule-engine publishes
fraud decision events to the `fraud.card.decisions.v1` topic. The transaction-management
service consumes these events for persistence and analyst workflows.

**Redpanda Console** (port 8083) provides a browser UI for viewing topics, messages, and
consumer groups.

## Application Services

| Application | Host Port | Container Port | Health Check |
|-------------|-----------|----------------|--------------|
| Rule Management API (FastAPI) | 8000 | 8000 | http://localhost:8000/api/v1/health |
| Rule Engine (Quarkus) | 8081 | 8081 | http://localhost:8081/health |
| Transaction Management API (FastAPI) | 8002 | 8002 | http://localhost:8002/api/v1/health |
| Intelligence Portal (React/Nginx) | 5173 | 5173 | http://localhost:5173/health |

### Running Applications

```powershell
# Start infra + all application containers
doppler run -- uv run platform-up -- --apps

# Or start apps via docker compose directly
doppler run -- docker compose -f docker-compose.yml -f docker-compose.apps.yml --profile apps up -d

# Build and start (force rebuild)
doppler run -- docker compose -f docker-compose.yml -f docker-compose.apps.yml --profile apps up -d --build
```

## Platform Commands

All `up` commands require `doppler run --` prefix. Stop/status commands do not
(they don't need secrets).

| Command | Description |
|---------|-------------|
| `doppler run -- uv run platform-up` | Start shared infrastructure |
| `doppler run -- uv run platform-up -- --apps` | Start infrastructure + all application containers |
| `uv run platform-down` | Stop all containers (keep data) |
| `uv run platform-status` | Show status of all containers |
| `uv run platform-reset` | Stop and remove all data (fresh start) |
| `uv run platform-sync-configs` | Sync platform Doppler configs (`local` -> `test`,`prod`) |

## Database

Single PostgreSQL instance with the `fraud_gov` database. All services query the same
schema, enabling cross-service data access.

**Users created on first start:**
- `fraud_gov_app_user` (read/write) - rule-management, transaction-management
- `fraud_gov_analytics_user` (read-only) - intelligence-portal, analytics

Schema migrations are managed by each application service.

## Verifying Services

After `doppler run -- uv run platform-up`:

```powershell
# Check all container status
uv run platform-status

# Test PostgreSQL
docker exec card-fraud-postgres pg_isready -U postgres -d fraud_gov

# Test Redis
docker exec card-fraud-redis redis-cli ping

# Test MinIO
curl -s http://localhost:9000/minio/health/ready

# Test Redpanda
docker exec card-fraud-redpanda rpk cluster health

# Open browser UIs
# MinIO Console: http://localhost:9001
# Redpanda Console: http://localhost:8083
```

After `doppler run -- uv run platform-up -- --apps`:

```powershell
# Test application health endpoints
curl http://localhost:8000/api/v1/health     # Rule Management
curl http://localhost:8081/health             # Rule Engine
curl http://localhost:8002/api/v1/health     # Transaction Management
curl http://localhost:5173/health             # Intelligence Portal
```

## Common Workflows

### Fresh Start (Reset Everything)

```powershell
uv run platform-reset                       # Stop all + remove volumes
doppler run -- uv run platform-up           # Start fresh
```

### Check Logs

```powershell
# All containers
docker compose logs -f

# Specific service
docker compose logs -f postgres
docker compose -f docker-compose.yml -f docker-compose.apps.yml logs -f rule-management
```

### Rebuild a Single App

```powershell
doppler run -- docker compose -f docker-compose.yml -f docker-compose.apps.yml \
    --profile apps up -d --build rule-management
```

## Troubleshooting

### "Missing required environment variables"

You forgot `doppler run --` prefix:
```powershell
# Wrong:
uv run platform-up

# Correct:
doppler run -- uv run platform-up
```

### Port already in use

Stop the conflicting container or process, then restart:
```powershell
# Find what's using the port
netstat -ano | findstr :5432
# Kill the process or stop the container
docker stop <container-name>
```

### Container won't start

Check logs for the specific container:
```powershell
docker compose logs <service-name>
```

### MinIO-init shows "Exited (0)"

This is **normal**. The init container runs once to create the bucket and exits. It does
not need to keep running.

### Database tables missing

Each application service manages its own schema. Start the service or run its DB init:
```powershell
# For rule-management
cd ../card-fraud-rule-management && doppler run -- uv run db-init

# For transaction-management
cd ../card-fraud-transaction-management && doppler run -- uv run db-init
```

### Network not found

If you see "network card-fraud-network not found", start infrastructure first:
```powershell
doppler run -- uv run platform-up
```

## GitHub Organization Strategy

**Recommended: GitHub Organization** (e.g., `card-fraud` or `card-fraud-platform`)

```
GitHub Organization: card-fraud
├── card-fraud-platform                 # Infra orchestrator
├── card-fraud-rule-management          # FastAPI backend
├── card-fraud-rule-engine              # Quarkus engine
├── card-fraud-transaction-management   # FastAPI backend
├── card-fraud-intelligence-portal      # React frontend
└── card-fraud-analytics                # (future)
```

**Why org, not monorepo:**
- Each service has different tech stacks (Java, Python, React)
- Independent CI/CD pipelines per service
- Independent versioning and release cycles
- Teams can own individual repos
- Docker builds reference each repo independently

See [AGENTS.md](AGENTS.md) for full agent documentation.
