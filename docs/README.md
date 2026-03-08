# Card Fraud Platform Documentation

Shared Docker Compose orchestrator for local multi-service development and the future control plane for the Card Fraud suite.

## Quick Start

```powershell
uv sync
doppler run -- uv run platform-up
uv run platform-status
uv run platform-check
```

High-risk action note: `db-reset-schema` requires `--yes`, exact `--confirm`, and `--schema-reset-ack RESET_SHARED_SCHEMA`.

## Documentation Standards

- Keep published docs inside `docs/01-setup` through `docs/07-reference`.
- Use lowercase kebab-case file names for topic docs.
- Exceptions: `README.md`, `codemap.md`, and generated contract artifacts (for example `openapi.json`).
- Do not keep TODO/archive/status/session planning docs in tracked documentation.
- Architecture and design docs must be current-state aware and future-state explicit.

## Section Index

### `01-setup` - Setup

Prerequisites, first-run onboarding, and environment bootstrap.

- _No published topic file yet._

### `02-development` - Development

Day-to-day workflows, architecture notes, and contributor practices.

- `02-development/platform-control-plane/README.md`
- `02-development/platform-control-plane/00-operating-model.md`
- `02-development/platform-control-plane/01-admin-action-contract.md`
- `02-development/platform-control-plane/02-inventory-and-observability-model.md`
- `02-development/platform-control-plane/03-secrets-and-configuration-ownership.md`
- `02-development/platform-control-plane/04-docs-and-governance-model.md`
- `02-development/platform-control-plane/05-card-fraud-platform.md`
- `02-development/platform-control-plane/06-card-fraud-rule-management.md`
- `02-development/platform-control-plane/07-card-fraud-rule-engine-auth.md`
- `02-development/platform-control-plane/08-card-fraud-rule-engine-monitoring.md`
- `02-development/platform-control-plane/09-card-fraud-transaction-management.md`
- `02-development/platform-control-plane/10-card-fraud-intelligence-portal.md`
- `02-development/platform-control-plane/11-card-fraud-e2e-load-testing.md`
- `02-development/platform-control-plane/12-card-fraud-ops-analyst-agent.md`
- `02-development/platform-control-plane/13-cross-repo-summary.md`
- `02-development/platform-control-plane/14-service-registry-format.md`
- `02-development/platform-control-plane/15-phase-1-implementation-backlog.md`
- `02-development/platform-control-plane/16-phase-2-platform-internals-design.md`
- `02-development/platform-control-plane/17-platform-adapter-schema.md`
- `02-development/platform-control-plane/18-db-ownership.md`
- `02-development/platform-control-plane/19-kafka-ownership.md`
- `02-development/platform-control-plane/20-minio-ownership.md`
- `02-development/platform-control-plane/21-auth0-ownership.md`
- `02-development/platform-control-plane/22-doppler-ownership.md`
- `02-development/platform-control-plane/23-phase-implementation-validation.md`
- `02-development/platform-control-plane/platform-adapter-reference.yaml`

### `03-api` - API

Contracts, schemas, endpoint references, and integration notes.

- _No published topic file yet._

### `04-testing` - Testing

Test strategy, local commands, and validation playbooks.

- _No published topic file yet._

### `05-deployment` - Deployment

Local runtime/deployment patterns and release-readiness guidance.

- _No published topic file yet._

### `06-operations` - Operations

Runbooks, observability, troubleshooting, and security operations.

- _No published topic file yet._

### `07-reference` - Reference

ADRs, glossary, and cross-repo reference material.

- `07-reference/secrets-ownership.md`

## Core Index Files

- `docs/README.md`
- `docs/codemap.md`
