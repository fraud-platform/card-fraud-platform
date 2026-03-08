# Card Fraud E2E Load Testing

> Status: approved

## Current Responsibilities

`card-fraud-e2e-load-testing` is the suite validation client and load-testing harness.

It owns:

- end-to-end scenario execution
- load generation and load test orchestration
- latency/SLO validation for target services
- scenario-level validation of suite behavior
- performance assumptions and test-driver documentation

It does not own runtime infrastructure or business service logic.

## Current Duplication And Pain Points

This repo documents service endpoints and some dependency assumptions that overlap with shared platform topology.

Without a platform control-plane model, test harness setup can become too dependent on tribal knowledge about:

- which services should be up
- which ports are canonical
- which health endpoints should be checked
- which infra services must be available for specific scenarios

## Target Future-State Ownership

E2E/load testing should remain a consumer of the suite, not an owner of the runtime.

It should continue to own:

- scenario design
- load-generation logic
- performance target enforcement
- test-data generation and harness behavior
- validation methodology

Platform should provide the suite context it depends on.

## Existing Platform Integration To Preserve

Platform already owns the containerized execution path for load testing through the Locust service in `docker-compose.apps.yml` and the `load-testing` profile.

The target design should preserve that direction:

- platform remains the authoritative owner of the containerized Locust execution path
- the harness consumes platform topology instead of re-deriving it
- suite readiness and target service availability should come from platform inventory

## How It Should Consume Platform Inventory

The test harness should be designed to consume platform-owned metadata such as:

- canonical service URLs
- health endpoints
- suite readiness state
- platform dependency state
- environment ownership and config linkage

That keeps the test harness from becoming a second source of truth for platform topology.

## Admin Actions To Expose To Platform

Recommended platform-callable actions:

- `service status`
- `verify`
- `seed` where the harness owns pre-test assets or data setup
- `logs`

Optional later actions:

- `bootstrap` for test fixtures if a stable harness-level setup action is defined

The load-testing repo should not become the owner of infra setup or service resets.

## Inventory Data Platform Can Read

Platform should show for e2e/load testing:

- target service coverage
- scenario families
- required dependencies per scenario class
- performance target references by service family
- latest available local test harness mode or profile information
- whether the load-testing profile is available in platform runtime

## Docs That Move To Platform

- shared service topology and canonical endpoints
- shared suite readiness model
- shared infra dependency map
- suite-wide operator flow for end-to-end validation

## Docs That Remain Local

- load-test design
- scenario and generator logic
- SLO/assertion methodology
- performance test execution details
- harness-specific troubleshooting

## Implementation-Facing Repo Changes

Expected changes inside `card-fraud-e2e-load-testing` during implementation:

- add `platform-adapter.yaml`
- declare `verify`, `service`, and any harness-owned `seed` actions through stable wrappers
- publish scenario dependency metadata for platform inventory
- stop acting as a second topology source and instead consume the platform registry
- document the existing Locust/profile relationship to platform as the canonical container path

## Secret Ownership Split

Platform-owned shared values:

- canonical local endpoint topology in suite mode
- shared auth or suite runtime metadata needed by the harness
- shared MinIO or service URLs where suite mode is authoritative

E2E-owned values:

- harness-only settings
- scenario-specific runtime toggles
- standalone duplicates needed when the harness is run directly

## Implementation Phases

### Phase 1 - Declare

- document harness dependencies and target-service coverage
- add adapter manifest metadata
- map the Locust/profile integration to the platform registry model

### Phase 2 - Operate

- use platform readiness and inventory models to simplify test setup
- allow platform to show whether the suite is ready for given scenario classes
- keep harness logic local while surfacing validation coverage in platform

### Future Horizon

- richer validation coverage summaries and run-history views in platform admin

## Risks And Non-Goals

Risks:

- if the harness becomes a second source of truth for topology, drift will grow
- if platform begins to embed scenario logic, boundaries will blur

Non-goals:

- moving load generation into platform
- making e2e/load testing responsible for runtime ownership

