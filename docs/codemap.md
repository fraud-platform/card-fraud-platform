# Code Map

## Repo

- `docker-compose.yml`: shared infrastructure stack (PostgreSQL, Redis, MinIO, Redpanda).
- `docker-compose.apps.yml`: optional app containers profile.
- `scripts/`: orchestration CLIs (`platform-up`, `platform-down`, `platform-status`, secret sync).
- `init-db/`: database bootstrap SQL.

## Key Commands

- `doppler run -- uv run platform-up`
- `doppler run -- uv run platform-up -- --apps`
- `uv run platform-status`
- `uv run platform-down`
- `uv run platform-sync-secrets`
- `uv run platform-sync-configs`

## Notes

This repo is the shared local orchestrator. Service runtime code lives in sibling repos.
