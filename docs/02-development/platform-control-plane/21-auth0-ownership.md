# Auth0 Ownership Artifact

> Status: approved

## Purpose

Define explicit ownership of Auth0 resources across all services in the card-fraud suite.

This document distinguishes between:
- **Gateway Auth**: Services using Auth0 as API gateway (JWT validation via Quarkus SmallRye JWT)
- **In-Process Auth**: Services performing their own JWT validation (FastAPI with python-jose)

---

## Auth Model Classification

| Service | Auth Model | Validation Location | Description |
|---------|-----------|---------------------|-------------|
| rule-management | in-process | FastAPI (python-jose) | Validates JWT tokens internally |
| rule-engine-auth | gateway | Quarkus SmallRye JWT | Validates via Auth0 gateway |
| rule-engine-monitoring | gateway | Quarkus SmallRye JWT | Validates via Auth0 gateway |
| transaction-management | in-process | FastAPI (python-jose) | Validates JWT tokens internally |
| ops-analyst-agent | in-process | FastAPI (python-jose) | Validates JWT tokens internally |
| intelligence-portal | spa | Auth0 SPA SDK | React frontend with Auth0 |
| locust | gateway | Uses RULE_ENGINE auth | Load testing harness |

---

## Ownership Map

### Shared (Platform-Owned)

| Resource | Owner | Description |
|----------|-------|-------------|
| `AUTH0_DOMAIN` | platform | Auth0 tenant domain (e.g., `dev-xyz.us.auth0.com`) |
| `AUTH0_AUDIENCE` (shared) | platform | Shared audience values used across services |

### Service-Specific (Service-Owned)

| Service | Resource | Owner | Type |
|---------|----------|-------|------|
| rule-management | `RULE_MGMT_AUTH0_AUDIENCE` | rule-management | API audience |
| rule-engine-* | `RULE_ENGINE_AUTH0_AUDIENCE` | rule-engine | API audience |
| rule-engine-* | `RULE_ENGINE_AUTH0_CLIENT_ID` | rule-engine | M2M client ID |
| rule-engine-* | `RULE_ENGINE_AUTH0_CLIENT_SECRET` | rule-engine | M2M client secret |
| transaction-management | `TXN_MGMT_AUTH0_AUDIENCE` | transaction-management | API audience |
| ops-analyst-agent | `OPS_ANALYST_AUTH0_AUDIENCE` | ops-analyst-agent | API audience |
| ops-analyst-agent | `OPS_ANALYST_AUTH0_CLIENT_ID` | ops-analyst-agent | M2M client ID |
| ops-analyst-agent | `OPS_ANALYST_AUTH0_CLIENT_SECRET` | ops-analyst-agent | M2M client secret |
| intelligence-portal | `VITE_AUTH0_DOMAIN` | intelligence-portal | SPA domain (may differ) |
| intelligence-portal | `VITE_AUTH0_CLIENT_ID` | intelligence-portal | SPA client ID |
| intelligence-portal | `VITE_AUTH0_AUDIENCE` | intelligence-portal | SPA API audience |

---

## Auth0 Application Types

### M2M (Machine-to-Machine) Applications

Used for service-to-service communication:

| Application | Client ID | Owner |
|-------------|-----------|-------|
| card-fraud-rule-engine | `{uuid}` | rule-engine (shared) |
| card-fraud-ops-analyst-agent | `{uuid}` | ops-analyst-agent |

### SPA (Single Page Application)

Used for frontend:

| Application | Client ID | Owner |
|-------------|-----------|-------|
| card-fraud-intelligence-portal | `{uuid}` | intelligence-portal |

### API

Each backend service exposes an API:

| API | Audience | Owner |
|-----|----------|-------|
| fraud-governance-api | `https://fraud-governance-api` | rule-management |
| fraud-rule-engine-api | `https://fraud-rule-engine-api` | rule-engine |
| fraud-transaction-mgmt-api | `https://fraud-transaction-mgmt-api` | transaction-management |
| fraud-ops-analyst-api | `https://fraud-ops-analyst-api` | ops-analyst-agent |

---

## In-Process Auth Services

### rule-management, transaction-management, ops-analyst-agent

These FastAPI services validate JWT tokens in-process:

```python
# Example: FastAPI JWT validation
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            key=get_jwks(AUTH0_DOMAIN),
            audience=AUTH0_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/"
        )
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**Required Environment Variables**:
- `AUTH0_DOMAIN`
- `AUTH0_AUDIENCE` (service-specific)

---

## Gateway Auth Services

### rule-engine-auth, rule-engine-monitoring

These Quarkus services use Auth0 as the gateway:

```yaml
# application.yaml
quarkus.smallrye-jwt.enabled=true
mp.jwt.verify.publickey.location=https://${AUTH0_DOMAIN}/.well-known/jwks.json
mp.jwt.verify.issuer=https://${AUTH0_DOMAIN}/
mp.jwt.verify.audiences=${AUTH0_AUDIENCE}
```

**Required Environment Variables**:
- `AUTH0_DOMAIN`
- `AUTH0_AUDIENCE`
- `AUTH0_CLIENT_ID` (for M2M)
- `AUTH0_CLIENT_SECRET` (for M2M)

---

## SPA Auth Services

### intelligence-portal

React SPA using Auth0 SDK:

```typescript
// auth.ts
import { createAuth0Client } from "@auth0/auth0-spa-js";

const auth0 = await createAuth0Client({
  domain: import.meta.env.VITE_AUTH0_DOMAIN,
  clientId: import.meta.env.VITE_AUTH0_CLIENT_ID,
  authorizationParams: {
    audience: import.meta.env.VITE_AUTH0_AUDIENCE,
    redirect_uri: window.location.origin
  }
});
```

**Required Environment Variables**:
- `VITE_AUTH0_DOMAIN`
- `VITE_AUTH0_CLIENT_ID`
- `VITE_AUTH0_AUDIENCE`

---

## Verification

### Platform Adapter Actions

Each service with auth should declare `auth-verify` action:

```yaml
auth:
  verify:
    command: [uv, run, auth0-verify]
    destructive: false
    timeout_seconds: 60
    mode: [standalone, suite]
    description: Verify Auth0 configuration
```

---

## Future Considerations

- Add token refresh handling for long-running operations
- Consider centralized token introspection endpoint
- Document Auth0 tenant setup for new environments
