# Code Map

## Repository Purpose

Shared Docker Compose orchestrator for local multi-service development.

## Key Paths

- `scripts/`: Local orchestration commands (`platform-up`, `platform-down`, secret/config sync).
- `docker-compose.yml`: Shared infrastructure stack (PostgreSQL, MinIO, Redis, Redpanda).
- `docker-compose.apps.yml`: Application services profile for cross-repo local runs.
- `init-db/`: PostgreSQL bootstrap SQL for users and grants.
- `docs/`: Curated onboarding and operational documentation.

## Local Commands

- `uv sync`
- `uv run platform-up`
- `uv run platform-up -- --apps`
- `uv run platform-status`

## Local Test Commands

- `uv run platform-status`

## API Note

This repository does not expose a business API. It orchestrates local infrastructure and app containers.

## Platform Integration

- Standalone mode: run this repository using its own local commands and Doppler project config.
- Consolidated mode: run this repository through `card-fraud-platform` compose stack for cross-service validation.
