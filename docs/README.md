# Card Fraud Platform Documentation

Shared Docker Compose orchestrator for local multi-service development.

## Quick Start

```powershell
uv sync
doppler run -- uv run platform-up
uv run platform-status
```

## Documentation Standards

- Keep published docs inside `docs/01-setup` through `docs/07-reference`.
- Use lowercase kebab-case file names for topic docs.
- Exceptions: `README.md`, `codemap.md`, and generated contract artifacts (for example `openapi.json`).
- Do not keep TODO/archive/status/session planning docs in tracked documentation.

## Section Index

### `01-setup` - Setup

Prerequisites, first-run onboarding, and environment bootstrap.

- _No published topic file yet._

### `02-development` - Development

Day-to-day workflows, architecture notes, and contributor practices.

- _No published topic file yet._

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

- _No published topic file yet._

## Core Index Files

- `docs/README.md`
- `docs/codemap.md`
