# Phase Implementation Validation

> Validated: 2026-03-08
> Scope: `card-fraud-platform` implementation and control-plane artifacts in this repository

## Purpose

Validate whether Phase 1 and Phase 2 from the control-plane backlog are implemented cleanly, identify gaps, and document fixes applied in this repo.

## Validation Summary

### Phase 1 - Declare

Result: **complete**

Validated in-repo deliverables:

- `control-plane/services.yaml` exists and is loadable.
- Ownership artifacts exist:
  - `control-plane/ownership/database.yaml`
  - `control-plane/ownership/messaging.yaml`
  - `control-plane/ownership/storage.yaml`
  - `control-plane/ownership/auth.yaml`
  - `control-plane/ownership/secrets.yaml`
- Adapter schema/reference docs exist:
  - `17-platform-adapter-schema.md`
  - `platform-adapter-reference.yaml`

Cross-repo completion:

- `platform-adapter.yaml` now exists in all in-scope sibling repos.
- `platformctl registry validate` now passes for all services.

### Phase 2 - Operate

Result: **implemented and operational for adapter routing**

Completed/validated:

- Registry loading and lookup implemented via `scripts/control_plane/registry.py`.
- Adapter manifest loading/routing implemented via `scripts/control_plane/adapter_manifest.py` and `scripts/control_plane/action_runner.py`.
- Health aggregation exists via `scripts/control_plane/health.py`.
- `platformctl` command surface exists (`status`, `inventory`, `action`, `registry validate`).

Gaps fixed in this validation pass:

- `scripts/control_plane/inventory/redis_runtime.py` was incomplete; implemented collector logic.
- Ownership collectors now read ownership YAML artifacts instead of hardcoded/stub data:
  - database
  - messaging
  - storage
  - auth
  - secrets
- `scripts/platform_status.py` now acts as a thin wrapper over shared control-plane collectors/presenters.
- `scripts/platform_check.py` now validates `platformctl` and all `scripts/control_plane/*` modules in its type phase.
- Added control-plane collector unit tests in `tests/test_control_plane_collectors.py`.
- `platformctl action` now returns non-zero exit codes for non-OK action outcomes.
- Platform now performs container prechecks for `service status/health` and `runtime verify` before adapter execution.
- `db-reset-schema` is treated as a high-risk action with explicit warning, restricted ownership policy, and required `--schema-reset-ack RESET_SHARED_SCHEMA`.
- Cross-repo reset policy aligned:
  - only `rule-management` exposes `db-reset-schema`
  - non-owner services expose `db-reset-tables` and `db-reset-data`
  - no adapter aliases `db-reset-tables` to `db-reset-schema`
- Portal auth verification now fails when required Auth0 environment keys are missing.
- Rule-management now has a true table-only reset implementation behind `db-reset-tables`.

Remaining external dependency for full Phase 2 completion:

- Service-specific readiness/health actions still depend on those services being actively running in local Docker.

## Validation Commands

Commands executed during validation:

- `uv run platform-check` -> pass
- `uv run platformctl registry validate` -> pass
- `uv run platformctl status --json` -> pass
- `uv run platformctl inventory all --json` -> pass
- `uv run platformctl action service logs <service> --json` for all 7 services -> pass
