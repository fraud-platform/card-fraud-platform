# Code Map

## Repository Purpose

Shared Docker Compose orchestrator for local multi-service development and the authoritative control-plane design home for the Card Fraud suite.

## Documentation Layout

- `01-setup/`: Setup
- `02-development/`: Development
- `02-development/platform-control-plane/`: control-plane operating model, summary matrices, registry format, phased backlog, and Phase 2 platform internals
- `03-api/`: API
- `04-testing/`: Testing
- `05-deployment/`: Deployment
- `06-operations/`: Operations
- `07-reference/`: Reference

## Control-Plane Design Set

The control-plane design set defines how this repo evolves from an infra orchestrator into a suite control plane for:

- shared infra lifecycle
- cross-service inventory and observability
- governed admin actions
- shared secret and docs ownership
- platform admin UX boundaries

Key entrypoints:

- `docs/02-development/platform-control-plane/README.md`
- `docs/02-development/platform-control-plane/13-cross-repo-summary.md`
- `docs/02-development/platform-control-plane/14-service-registry-format.md`
- `docs/02-development/platform-control-plane/15-phase-1-implementation-backlog.md`
- `docs/02-development/platform-control-plane/16-phase-2-platform-internals-design.md`
- `docs/02-development/platform-control-plane/23-phase-implementation-validation.md`
- `docs/07-reference/secrets-ownership.md`

## Local Commands

- `uv sync`
- `doppler run -- uv run platform-up`
- `uv run platform-status`
- `uv run platformctl status`
- `uv run platform-check`
- `uv run platform-down`
- `uv run platform-reset`
- `uv run platformctl action db db-reset-schema rule-management --yes --confirm rule-management:db:db-reset-schema --schema-reset-ack RESET_SHARED_SCHEMA`

## Platform Modes

- Standalone mode: operate this repo for shared infra orchestration only.
- Suite mode: use this repo as the control plane for the full Card Fraud local service estate.
