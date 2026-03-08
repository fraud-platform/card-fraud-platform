# Card Fraud Intelligence Portal

> Status: approved

## Current Responsibilities

`card-fraud-intelligence-portal` is the suite business UI, not the platform control plane.

It owns:

- user-facing fraud operations UI flows
- frontend integration with backend service APIs
- SPA auth integration and access control behavior
- business workflow views and user journeys
- portal-specific testing, build, and frontend documentation

## Current Duplication And Pain Points

The portal still includes some setup and integration guidance that overlaps with shared platform concerns:

- shared Auth0 setup context
- shared runtime and API topology context
- cross-service integration assumptions that could be documented more centrally

There is also an architectural risk that a future platform admin UI could accidentally be conflated with the portal. That should not happen.

## Target Future-State Ownership

The portal remains the business/application UI.

It should not become the platform admin console.

The future control-plane UI should live under platform ownership, even if it reuses frontend patterns or assets from the portal ecosystem later.

Portal should continue to own:

- user-facing fraud operations UX
- SPA auth semantics and access control behavior
- frontend route/resource model
- backend API integration behavior
- portal-specific docs and tests

## Relationship To The Platform Admin

Platform admin and portal should be modeled as separate products:

- **Portal**: fraud analyst or business workflow interface
- **Platform Admin**: operator/developer control plane for suite runtime and oversight

They may share:

- auth provider infrastructure
- shared backend APIs
- shared visual primitives later if desired

They must not share ownership boundaries.

## Admin Actions To Expose To Platform

Recommended platform-callable actions:

- `service status`
- `service health`
- `verify`
- `auth bootstrap`
- `auth verify`
- `logs`

Portal is not a primary owner of destructive DB or messaging actions.

## Inventory Data Platform Can Read

Platform should show for the portal:

- app runtime status
- host port
- health endpoint
- backend dependency targets
- SPA auth ownership summary
- whether portal routes depend on specific backend availability

## Docs That Move To Platform

Platform should centralize:

- suite-level Auth0 topology
- suite API topology and canonical service map
- platform admin versus business UI separation
- shared runtime startup flow

## Docs That Remain Local

Portal should keep:

- frontend architecture and workflow docs
- UI patterns
- route and resource documentation
- portal-specific auth/access-control behavior
- frontend testing and CSP/security docs

## Implementation-Facing Repo Changes

Expected changes inside `card-fraud-intelligence-portal` during implementation:

- add `platform-adapter.yaml`
- declare `service` and `auth` actions through stable wrappers
- publish runtime dependency metadata for backend APIs used by the portal
- remove duplicated suite-level auth and topology explanations in favor of platform docs
- preserve portal as a business UI and avoid embedding platform-admin responsibilities here

## Secret Ownership Split

Platform-owned shared values:

- shared domain and API topology values used in suite mode
- shared Auth0 domain metadata where suite-wide
- shared CORS or suite runtime values where relevant

Portal-owned values:

- SPA-specific Auth0 client settings
- frontend-only runtime values
- standalone duplicates needed for direct portal execution

## Implementation Phases

### Phase 1 - Declare

- document portal runtime dependencies and auth ownership
- add adapter manifest metadata
- clarify shared versus portal-specific docs

### Phase 2 - Operate

- surface portal status and dependency context in platform
- route portal verify/auth actions through platform
- keep portal and platform-admin concerns separated in implementation

### Future Horizon

- optional shared visual primitives, but only after the product boundary is stable

## Risks And Non-Goals

Risks:

- conflating portal and platform admin will blur user personas and responsibilities
- moving operator concerns into the portal will complicate the business UI unnecessarily

Non-goals:

- turning the existing portal into the first platform admin by default
- moving frontend business workflows into the platform repo

