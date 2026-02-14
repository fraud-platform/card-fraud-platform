# Secrets Ownership Matrix

This file defines Doppler ownership across all local Card Fraud repos.

## Policy (Current)

- Keep **platform-level** secrets for docker-compose orchestration.
- Keep **service-level** secrets for standalone repo development/tests.
- Avoid deleting service-level projects until platform + standalone flows are both stable.

## Doppler Projects

| Doppler Project | Primary Use | Owner |
|---|---|---|
| `card-fraud-platform` | Shared infra + app containers via compose | Platform repo |
| `card-fraud-rule-management` | Standalone RM API dev/tests | Rule Management repo |
| card-fraud-rule-engine-auth | Standalone AUTH Rule Engine dev/tests | Rule Engine AUTH repo |
| card-fraud-rule-engine-monitoring | Standalone MONITORING Rule Engine dev/tests | Rule Engine MONITORING repo |
| `card-fraud-transaction-management` | Standalone TM API dev/tests | Transaction Mgmt repo |
| `card-fraud-intelligence-portal` | Standalone portal dev | Portal repo |
| `card-fraud-e2e-load-testing` | Standalone e2e/load execution | E2E repo |

## Platform Required Keys (Compose)

Infrastructure and shared app keys that **must** exist in `card-fraud-platform`:

- `POSTGRES_ADMIN_PASSWORD`
- `FRAUD_GOV_APP_PASSWORD`
- `FRAUD_GOV_ANALYTICS_PASSWORD`
- `MINIO_ROOT_USER`
- `MINIO_ROOT_PASSWORD`
- `S3_ACCESS_KEY_ID`
- `S3_SECRET_ACCESS_KEY`
- `S3_BUCKET_NAME`
- `S3_REGION`
- `AUTH0_DOMAIN`
- `RULE_MGMT_AUTH0_AUDIENCE`
- `RULE_ENGINE_AUTH0_AUDIENCE`
- `RULE_ENGINE_AUTH0_CLIENT_ID`
- `RULE_ENGINE_AUTH0_CLIENT_SECRET`
- `TXN_MGMT_AUTH0_AUDIENCE`
- `VITE_API_URL`
- `VITE_AUTH0_DOMAIN`
- `VITE_AUTH0_CLIENT_ID`
- `VITE_AUTH0_AUDIENCE`
- `APP_ENV` (`local` / `test` / `prod`)

## Operational Commands

- Sync shared local DB/object-storage secrets across platform + RM + TM:
  - `uv run platform-sync-secrets -- --source-project card-fraud-rule-management --config local`
- Sync platform configs from `local` to `test`/`prod`:
  - `uv run platform-sync-configs`

## Notes

- `APP_ENV` values are standardized as lowercase: `local`, `test`, `prod`.
- Platform `test`/`prod` now mirror local compose-required keys for local-only workflows.
