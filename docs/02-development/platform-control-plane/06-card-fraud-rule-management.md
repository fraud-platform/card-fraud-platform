# Card Fraud Rule Management

> Status: approved

## Current Responsibilities

`card-fraud-rule-management` owns the control-plane side of the fraud rules domain:

- rule CRUD and lifecycle management
- deterministic compiler and ruleset packaging semantics
- artifact publication to MinIO/S3
- maker-checker and governance behavior
- service-specific DB migrations and schema semantics
- service-specific Auth0 bootstrap and verification flows
- service-owned testing, seeding, and validation logic

## Current Duplication And Pain Points

The repo still carries local wrappers for concerns that are already platform-owned in suite mode:

- PostgreSQL local lifecycle
- MinIO local lifecycle
- combined infra-up/down flows
- repeated setup documentation for shared infra and shared secrets

This duplication makes the repo usable standalone, but it also creates ambiguity about who owns shared infrastructure operations when the full suite is in play.

## Target Future-State Ownership

Rule management should remain the owner of the rule domain and artifact publication pipeline.

It should continue to own:

- rule authoring model
- compiler behavior
- publication semantics
- service-specific DB init/verify/reset logic
- Auth0 scopes, roles, audience, and bootstrap semantics for the rule-management API
- rule-management-specific seed/demo workflows

It should stop acting as an alternative owner of shared infra orchestration in suite mode.

## Admin Actions To Expose To Platform

Recommended platform-callable actions:

- `service status`
- `service health`
- `db-init`
- `db-verify`
- `db-reset-schema`
- `db-reset-data`
- `verify` for service-level setup and dependencies
- `auth bootstrap`
- `auth verify`
- `seed`
- `logs`

Important boundary:

Platform should call these actions; rule management should still implement them.

## Inventory Data Platform Can Read

Rule management should make it possible for platform to inventory:

- API port and health endpoint
- DB ownership summary for rule-related tables
- compiler artifact publish capability
- MinIO bucket and manifest usage at a summary level
- Auth0 audience and role ownership for this service
- seed/demo capability metadata

## Docs That Move To Platform

These topics should become platform-canonical:

- shared Doppler model
- shared DB topology
- shared MinIO setup
- suite-level Auth0 architecture overview
- shared local startup flow

## Docs That Remain Local

These topics remain rule-management-owned:

- compiler design
- rule governance model
- ruleset publisher specifics
- domain model
- pagination/API semantics
- service-specific auth model details
- service-specific DB and seed semantics

## Implementation-Facing Repo Changes

Expected changes inside `card-fraud-rule-management` during implementation:

- add `platform-adapter.yaml`
- declare supported `db`, `auth`, `service`, `seed`, and `storage` actions through stable repo wrappers
- publish the concrete table/index ownership map for rule-management-owned objects
- publish MinIO artifact ownership metadata for platform inventory
- shrink duplicated shared setup docs and link back to platform-canonical suite docs
- de-emphasize shared infra wrappers in suite mode while preserving standalone support

## Secret Ownership Split

Platform-owned shared secrets:

- shared DB credentials
- shared MinIO credentials
- shared bucket names
- shared local topology values
- shared Auth0 domain metadata where used across the suite

Rule-management-owned secrets:

- service-specific Auth0 settings that are unique to this service
- standalone-only duplicates needed for isolated repo use
- any feature flags or service-only integration values

## Implementation Phases

### Phase 1 - Declare

- map rule-management-owned DB objects and indexes
- map rule-management-owned auth resources
- add adapter manifest metadata
- link service docs to platform-canonical shared setup docs

### Phase 2 - Operate

- route rule-management admin actions through platform
- surface rule-management inventory in platform status and inventory views
- reduce duplicate shared infra workflows in suite mode

### Future Horizon

- richer artifact inventory and publication visibility in platform admin

## Risks And Non-Goals

Risks:

- if platform reimplements compiler or DB reset logic, ownership will blur
- if rule-management keeps documenting shared infra independently, docs drift will return

Non-goals:

- moving compiler logic to platform
- moving rule-management domain docs into platform

