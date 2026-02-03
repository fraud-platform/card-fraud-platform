# Code Map

## Repository Purpose

Shared Docker Compose orchestrator for local multi-service development.

## Primary Areas

- `app/` or `src/`: service or application implementation.
- `tests/` or `e2e/`: automated validation.
- `scripts/` or `cli/`: local developer tooling.
- `docs/`: curated documentation index and section guides.

## Local Commands

- `uv sync`
- `doppler run -- uv run platform-up`
- `doppler run -- uv run platform-up -- --apps`
- `uv run platform-status`

## Test Commands

- `uv run platform-status`

## API Note

This repo does not expose an application API; it manages infrastructure and app containers.

## Deployment Note

Local deployment is Docker Compose-based. CI/CD is intentionally deferred.
