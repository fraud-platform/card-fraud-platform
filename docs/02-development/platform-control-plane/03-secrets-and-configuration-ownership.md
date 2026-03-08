# Secrets And Configuration Ownership

> Status: approved

## Objective

Define the canonical ownership model for Doppler-managed configuration across the suite.

The suite already depends on Doppler everywhere. The remaining problem is not whether to use Doppler; it is how to prevent duplication, confusion, and drift while preserving standalone usability.

## Design Principle

Use two layers of ownership:

- **platform-owned shared runtime secrets** for suite mode
- **service-owned secrets** for standalone mode and service-specific integrations

This is the correct enterprise split because it supports one local control plane without making each service repo dependent on platform for all of its private configuration semantics.

## Ownership Rules

### Platform-Owned Shared Secrets

The `card-fraud-platform` Doppler project should own secrets that represent shared local runtime topology or cross-service infrastructure contracts.

Examples:

- PostgreSQL admin password
- shared application DB user password
- shared analytics/read-only DB user password
- MinIO root credentials
- shared S3 access credentials for local suite runtime
- shared bucket names
- shared Redis/Kafka/OTEL/CORS topology values where centralized
- shared Auth0 domain metadata used across the suite
- shared audience or client metadata only when the same value is explicitly consumed by multiple services in suite mode
- shared observability routing values such as a suite-level `SENTRY_DSN` only when deliberately centralized

Platform ownership means:

- platform documents the canonical key names
- platform uses those values in compose-based suite runtime
- shared values should not be manually redefined differently across repos

### Service-Owned Secrets

Each service Doppler project should own secrets that represent service-specific behavior or secrets that should not be generalized into the platform project.

Examples:

- service-specific Auth0 client ids or secrets that are only meaningful for that service
- standalone-only service configuration
- LLM credentials and model settings for `card-fraud-ops-analyst-agent`
- service-specific third-party API keys
- service-only feature flags or runtime tuning knobs
- values required only when running the service directly outside the platform runtime
- service-specific `SENTRY_DSN` values when telemetry isolation per service is preferred

### Shared Value Duplication Policy

Some duplication is acceptable and necessary when a service must remain standalone-capable.

Allowed duplication:

- shared connection values duplicated in a service Doppler project for standalone execution
- shared host/port values when the service needs them locally outside compose
- Auth0 metadata duplicated where a service must validate or configure itself independently

Disallowed duplication:

- ungoverned divergence of shared passwords, bucket names, or shared runtime credentials
- repo-local `.env` replacements for Doppler-managed values
- copy-paste of shared config names without ownership documentation

## Ownership Table

| Category | Platform Owns | Service Owns |
|---|---|---|
| Shared DB credentials | Yes | Only duplicate for standalone use |
| Shared MinIO/S3 local runtime creds | Yes | Only duplicate for standalone use |
| Shared Kafka/Redis local topology | Yes | Only duplicate for standalone use |
| Shared Auth0 domain metadata | Yes | May duplicate if needed locally |
| Service-specific Auth0 client secrets | No | Yes |
| LLM/runtime provider secrets | No | Yes |
| Service-only feature flags | No | Yes |
| Compose-wide OTEL/CORS/shared runtime values | Yes | Only duplicate if standalone requires them |
| `SENTRY_DSN` | central only if intentionally shared | otherwise per-service |

## Doppler Project Model

Recommended steady state:

- `card-fraud-platform`: suite-mode shared runtime secrets
- `card-fraud-rule-management`: standalone rule-management + service-only values
- `card-fraud-rule-engine-auth`: standalone AUTH runtime + service-only values
- `card-fraud-rule-engine-monitoring`: standalone MONITORING runtime + service-only values
- `card-fraud-transaction-management`: standalone transaction management + service-only values
- `card-fraud-intelligence-portal`: standalone portal + service-only values
- `card-fraud-e2e-load-testing`: standalone test harness values
- `card-fraud-ops-analyst-agent`: service-only values plus LLM/provider configuration

## Naming Conventions

### Canonical Shared Key Naming

Shared runtime keys should use consistent names across the suite. Platform docs must define the canonical names and services should consume those names rather than invent aliases where avoidable.

Examples:

- `POSTGRES_ADMIN_PASSWORD`
- `FRAUD_GOV_APP_PASSWORD`
- `FRAUD_GOV_ANALYTICS_PASSWORD`
- `MINIO_ROOT_USER`
- `MINIO_ROOT_PASSWORD`
- `S3_ACCESS_KEY_ID`
- `S3_SECRET_ACCESS_KEY`
- `S3_BUCKET_NAME`
- `AUTH0_DOMAIN`

### Service-Specific Names

Service-specific keys should be clearly scoped by service or capability.

Examples:

- `RULE_ENGINE_AUTH0_CLIENT_ID`
- `RULE_ENGINE_AUTH0_CLIENT_SECRET`
- `OPS_ANALYST_AUTH0_CLIENT_ID`
- `OPS_ANALYST_AUTH0_CLIENT_SECRET`
- `LLM_API_KEY`
- `PLANNER_MODEL_NAME`

The naming goal is to make ownership obvious from the key name itself.

## Drift Detection And Sync

The platform should define a future drift-check capability for shared keys.

Drift detection should answer:

- are platform-owned shared keys present where required?
- do standalone service projects define the required duplicates for standalone execution?
- are duplicated shared keys aligned where alignment is required?
- are unexpected extra keys carrying shared values under inconsistent names?

Drift checks should compare presence and ownership, not display secret values.

### Role Of `platform-sync-secrets`

`platform-sync-secrets` is a **sync helper**, not the full ownership model.

Design intent:

- it can copy or align approved shared keys into the platform-owned shared runtime project or other approved targets
- it should never become the only source of truth for what ownership means
- drift detection remains a separate control-plane responsibility even if the sync helper is reused in implementation

## Configuration Publication Rules

- `README.md` and `AGENTS.md` should reference the ownership model, not re-explain all secrets in every repo.
- Suite-level configuration docs live in `card-fraud-platform`.
- Service repos should document only their service-specific delta and any required standalone duplication.
- `.env` workflows remain disallowed.

## Special Case: Ops Analyst Agent

`card-fraud-ops-analyst-agent` is a special case because it depends on shared suite runtime values and also on service-only LLM/provider secrets.

The target model should keep:

- shared infra and platform runtime values under platform ownership
- LLM and model/provider secrets under ops-agent ownership

That split should remain explicit because it is materially different from the rest of the suite.

## Success Criteria

This ownership model is successful when:

- shared runtime secrets are defined once authoritatively
- standalone repos still work without platform lock-in
- secret drift is visible and governable
- service-specific secrets remain clearly owned
- documentation stops duplicating the same shared secret setup instructions across repos

