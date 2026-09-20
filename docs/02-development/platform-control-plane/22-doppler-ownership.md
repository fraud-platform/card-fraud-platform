# Doppler Ownership Artifact

> Status: approved

## Purpose

Define explicit ownership of Doppler secrets across all services in the card-fraud suite.

This artifact complements the `03-secrets-and-configuration-ownership.md` document with a more granular view of Doppler project structure.

---

## Doppler Project Structure

| Project | Owner | Purpose |
|---------|-------|---------|
| `card-fraud-platform` | platform | Shared runtime secrets for suite mode |
| `card-fraud-rule-management` | rule-management | Standalone config + service-specific values |
| `card-fraud-rule-engine-auth` | rule-engine | Standalone config + AUTH runtime values |
| `card-fraud-rule-engine-monitoring` | rule-engine | Standalone config + MONITORING runtime values |
| `card-fraud-transaction-management` | transaction-management | Standalone config + messaging values |
| `card-fraud-intelligence-portal` | intelligence-portal | Standalone config + SPA values |
| `card-fraud-ops-analyst-agent` | ops-analyst-agent | Service config + LLM/provider values |
| `card-fraud-e2e-load-testing` | platform | Load testing harness values |

---

## Ownership Map

### Platform-Owned (card-fraud-platform)

These secrets are owned by the platform and used across all services:

| Secret | Type | Description |
|--------|------|-------------|
| `POSTGRES_ADMIN_PASSWORD` | secret | PostgreSQL admin password |
| `FRAUD_GOV_APP_PASSWORD` | secret | Shared app user password (read/write) |
| `FRAUD_GOV_ANALYTICS_PASSWORD` | secret | Shared analytics user password (read-only) |
| `MINIO_ROOT_USER` | secret | MinIO root access key |
| `MINIO_ROOT_PASSWORD` | secret | MinIO root secret key |
| `S3_ACCESS_KEY_ID` | secret | Shared S3/MinIO access key |
| `S3_SECRET_ACCESS_KEY` | secret | Shared S3/MinIO secret key |
| `S3_BUCKET_NAME` | string | Shared bucket name (`fraud-gov-artifacts`) |
| `S3_REGION` | string | S3 region (default: `us-east-1`) |
| `AUTH0_DOMAIN` | string | Auth0 tenant domain |
| `AUTH0_USER_AUDIENCE` | string | Unified human-user audience for portal tokens |
| `REDIS_URL` | string | Redis connection URL |
| `KAFKA_BOOTSTRAP_SERVERS` | string | Kafka/Redpanda bootstrap servers |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | string | OpenTelemetry collector endpoint |
| `SECURITY_CORS_ALLOWED_ORIGINS` | string | CORS allowed origins |

### Service-Owned (Service Projects)

#### rule-management

| Secret | Type | Description |
|--------|------|-------------|
| `RULE_MGMT_AUTH0_AUDIENCE` | string | M2M audience for rule-management |
| `AUTH0_TEST_CLIENT_ID` | secret | Development-only Local Test Client ID for role-token helpers |
| `AUTH0_TEST_CLIENT_SECRET` | secret | Development-only Local Test Client secret; never exposed to the browser |
| `TEST_USER_*_PASSWORD` | secret | Canonical role-user passwords for local/password-realm tests |
| `APP_ENV` | string | Environment (local, dev, prod) |

#### rule-engine (shared for AUTH and MONITORING)

| Secret | Type | Description |
|--------|------|-------------|
| `RULE_ENGINE_AUTH0_AUDIENCE` | string | API audience for rule engines |
| `RULE_ENGINE_AUTH0_CLIENT_ID` | secret | M2M client ID for rule engines |
| `RULE_ENGINE_AUTH0_CLIENT_SECRET` | secret | M2M client secret for rule engines |
| `QUARKUS_PROFILE` | string | Quarkus profile (load-test, etc.) |

#### transaction-management

| Secret | Type | Description |
|--------|------|-------------|
| `TXN_MGMT_AUTH0_AUDIENCE` | string | M2M audience for transaction management |
| `KAFKA_CONSUMER_GROUP_ID` | string | Kafka consumer group ID |
| `KAFKA_DLQ_TOPIC` | string | Dead letter queue topic |

#### intelligence-portal

| Secret | Type | Description |
|--------|------|-------------|
| `VITE_AUTH0_DOMAIN` | string | Auth0 domain for SPA |
| `VITE_AUTH0_CLIENT_ID` | string | SPA client ID |
| `VITE_AUTH0_AUDIENCE` | string | SPA human-user audience; mirrors `AUTH0_USER_AUDIENCE` |
| `E2E_AUTH0_CLIENT_ID` | secret | Alias for the rule-management-owned Local Test Client ID |
| `E2E_AUTH0_CLIENT_SECRET` | secret | Alias for the rule-management-owned Local Test Client secret |
| `VITE_API_URL` | string | Backend API URL |

#### ops-analyst-agent

| Secret | Type | Description |
|--------|------|-------------|
| `OPS_ANALYST_AUTH0_AUDIENCE` | string | M2M audience for ops agent |
| `OPS_ANALYST_AUTH0_CLIENT_ID` | secret | M2M client ID |
| `OPS_ANALYST_AUTH0_CLIENT_SECRET` | secret | M2M client secret |
| `LLM_PROVIDER` | string | LLM provider (openai, anthropic, etc.) |
| `LLM_API_KEY` | secret | LLM API key |
| `LLM_BASE_URL` | string | LLM base URL (for local models) |
| `PLANNER_MODEL_NAME` | string | Planner model name |
| `PLANNER_EVIDENCE_SELECTION_ENABLED` | boolean | Enable optional planner evidence selection |
| `VECTOR_ENABLED` | boolean | Enable vector search |
| `VECTOR_API_BASE` | string | Vector DB API base URL |
| `VECTOR_MODEL_NAME` | string | Embedding model name |
| `VECTOR_DIMENSION` | int | Embedding dimension |

The suite overlay also forwards the active non-secret tuning keys for these
same groups: LLM retry/prompt/reasoning settings, planner temperature/token/
timeout settings, LangGraph step/timeouts, and vector search/retry/timeout
settings. `VECTOR_API_KEY` is allowlisted as an optional service-owned secret;
the ops-agent normally inherits the cloud key from `LLM_API_KEY`.

### Suite-mode ops-agent overlay

`uv run platform-up` remains invoked under the platform project's Doppler
context, then reads `card-fraud-ops-analyst-agent/local` with
`doppler secrets download --no-file --format json`. The startup script captures
that response in memory and overlays only the ops-owned LLM, planner, vector,
and reasoning allowlist into the Compose subprocess. It never prints values or
passes unrelated ops-agent secrets through the platform environment. Missing
required allowlist keys fail startup with names-only diagnostics. This keeps
the service-owned model/provider source of truth in the ops-agent project while
the platform project remains authoritative for shared runtime secrets.

#### e2e-load-testing

| Secret | Type | Description |
|--------|------|-------------|
| (inherits from platform) | | Uses platform secrets |

---

## Shared Value Duplication Policy

### Allowed Duplication

Services may duplicate platform-owned secrets for standalone execution:

```
# In card-fraud-rule-management Doppler project
FRAUD_GOV_APP_PASSWORD = <same as platform>
AUTH0_DOMAIN = <same as platform>
AUTH0_USER_AUDIENCE = <same as platform>
```

This allows services to run standalone without platform orchestration.

Audience rule:

- `AUTH0_USER_AUDIENCE` is platform-owned and shared.
- Service M2M audience values remain service-owned.
- `VITE_AUTH0_AUDIENCE` is a portal build arg derived from the platform-owned human-user audience.

Local test-auth rule:

- `AUTH0_TEST_CLIENT_ID` and `AUTH0_TEST_CLIENT_SECRET` are owned by rule-management and are local/test only.
- The portal may consume them through its `E2E_AUTH0_CLIENT_ID` and `E2E_AUTH0_CLIENT_SECRET` aliases.
- No runtime service container or platform compose service should receive these credentials.

### Disallowed Duplication

- Creating new secrets with different names for the same value
- Committing `.env` files to repos

---

## Sync Mechanism

### platform-sync-secrets

The `platform-sync-secrets` command synchronizes shared secrets:

```bash
doppler run -- uv run platform-sync-secrets
```

This copies platform-owned secrets to service projects for standalone use.

### Verification

Each service should verify secret alignment:

```yaml
# platform-adapter.yaml example
auth:
  verify:
    command: [uv, run, auth0-verify]
    destructive: false
    timeout_seconds: 60
```

---

## Drift Detection

Platform should detect drift between:

1. Platform-owned secrets in `card-fraud-platform` project
2. Duplicated secrets in service projects
3. Missing required secrets in service projects

### Expected Drift Report

```json
{
  "card-fraud-platform": {
    "owned": ["POSTGRES_ADMIN_PASSWORD", "AUTH0_DOMAIN", ...],
    "complete": true
  },
  "card-fraud-rule-management": {
    "platform_duplicates": ["AUTH0_DOMAIN"],
    "service_owned": ["RULE_MGMT_AUTH0_AUDIENCE"],
    "complete": true
  }
}
```

---

## Environment-Specific Config

Each Doppler project supports multiple configs:

| Config | Purpose |
|--------|---------|
| `local` | Local development with Docker Compose |
| `test` | Test environment |
| `prod` | Production environment |

---

## Future Considerations

- Automate drift detection on platform startup
- Add secret rotation support
- Document new secret onboarding process
