# Card Fraud Ops Analyst Agent

> Status: approved

## Current Responsibilities

`card-fraud-ops-analyst-agent` is an application service with a special dependency profile.

It owns:

- agent runtime behavior
- LLM/provider integration
- ops-analyst workflow logic
- service-specific DB tables and migration semantics
- service-specific Auth0 setup and verification
- e2e scenario and agent behavior validation

It is also unusual because it depends on both shared suite infrastructure and service-only model/provider secrets.

## Current Duplication And Pain Points

This repo currently documents a dual-secrets model and explicit platform compose integration. That is correct in spirit, but it also means its local guidance can easily become one of the most complicated in the suite.

The main pain points are:

- split ownership across platform secrets and service-only LLM/provider secrets
- repeated shared infra guidance that belongs in platform
- operational complexity around preflight, platform integration, and observability

## Target Future-State Ownership

Ops-agent should continue to own:

- agent workflow logic
- LLM/provider runtime configuration semantics
- agent-specific DB tables and reset semantics
- service-specific Auth0 behavior
- service-specific e2e and observability needs

Platform should own:

- the shared infra and suite control plane around ops-agent
- the shared runtime visibility and action routing for ops-agent
- the canonical explanation of how dual ownership works in suite mode

## Special Secret Ownership Split

This service must retain a clearly documented two-layer ownership model.

Platform-owned shared runtime values:

- shared DB credentials and topology
- shared auth domain/topology where suite-wide
- shared MinIO/Kafka/Redis/OTEL/runtime values used by compose
- any suite-wide infra values consumed by the ops-agent container

Ops-agent-owned values:

- `LLM_API_KEY`
- provider/model selection
- planner/model runtime knobs
- service-only feature flags
- service-only external integration settings

This split is not a problem. It is the correct architecture. The important thing is to formalize it in the platform control-plane model.

## Admin Actions To Expose To Platform

Recommended platform-callable actions:

- `service status`
- `service health`
- `db-init`
- `db-verify`
- `db-reset-tables`
- `db-reset-data`
- `verify`
- `auth bootstrap`
- `auth verify`
- `seed`
- `logs`

Because ops-agent is operationally complex, it is also a strong candidate for richer preflight and readiness actions routed through platform.

## Inventory Data Platform Can Read

Platform should show for ops-agent:

- service runtime status and health endpoint
- DB ownership summary for ops-agent tables
- observability endpoints and links
- dependency status against transaction-management and other relevant services
- dual Doppler ownership model
- agent-specific readiness/preflight metadata

## Docs That Move To Platform

- shared platform integration flow
- shared infra topology and operator startup flow
- suite-level dual-ownership explanation where platform plus service secrets are merged
- platform-visible observability topology

## Docs That Remain Local

- agent workflow and orchestration
- model risk and prompt governance
- service-specific observability details
- agent-specific e2e and runtime semantics
- provider and model behavior guidance

## Implementation-Facing Repo Changes

Expected changes inside `card-fraud-ops-analyst-agent` during implementation:

- add `platform-adapter.yaml`
- declare `db`, `auth`, `service`, `seed`, and `verify` actions through stable wrappers
- publish concrete table/index ownership for ops-agent-owned DB objects
- publish dual secret ownership metadata so platform can show platform-owned versus agent-owned config cleanly
- reduce repeated shared infra docs and link back to platform-canonical control-plane docs

## Implementation Phases

### Phase 1 - Declare

- document the two-layer secret ownership model in platform docs and service metadata
- define ops-agent service registry and admin action capabilities
- define the inventory metadata platform needs for ops-agent oversight
- publish DB ownership boundaries for ops-agent tables

### Phase 2 - Operate

- allow platform to run ops-agent preflight and scoped service-owned actions
- keep implementation logic in ops-agent repo
- show ops-agent status, observability links, and readiness from platform admin

### Future Horizon

- richer operator views for agent readiness and scenario execution history

## Risks And Non-Goals

Risks:

- the dual-secrets model can become confusing if ownership is not explicit
- platform may overreach into agent-specific provider logic if boundaries are not enforced

Non-goals:

- moving LLM/provider logic into platform
- making platform the owner of agent behavior semantics


