# Platform Adapter Manifest Schema

> Status: approved

## Purpose

Define the JSON Schema for `platform-adapter.yaml` - the manifest file that each service repo must provide to declare the actions the platform can invoke.

## Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["service", "version", "entrypoints"],
  "properties": {
    "service": {
      "type": "string",
      "description": "Canonical service identifier matching services.yaml"
    },
    "version": {
      "type": "string",
      "description": "Manifest version for compatibility tracking"
    },
    "entrypoints": {
      "type": "object",
      "description": "Map of action domains to supported actions",
      "additionalProperties": {
        "type": "object",
        "additionalProperties": {
          "type": "object",
          "required": ["command", "destructive", "timeout_seconds"],
          "properties": {
            "command": {
              "type": "array",
              "items": { "type": "string" },
              "description": "Command to execute as array of strings"
            },
            "destructive": {
              "type": "boolean",
              "description": "Whether this action modifies state irreversibly"
            },
            "timeout_seconds": {
              "type": "integer",
              "minimum": 1,
              "description": "Maximum execution time before termination"
            },
            "requires_confirmation": {
              "type": "boolean",
              "description": "Whether platform must confirm before execution"
            },
            "mode": {
              "type": "array",
              "items": { "type": "string", "enum": ["standalone", "suite"] },
              "description": "Supported execution modes"
            },
            "description": {
              "type": "string",
              "description": "Human-readable action description"
            }
          }
        }
      }
    }
  }
}
```

## Example: rule-management

```yaml
service: rule-management
version: "1.0"
entrypoints:
  service:
    status:
      command: [uv, run, service-status]
      destructive: false
      timeout_seconds: 10
      mode: [standalone, suite]
      description: Get service runtime status
    health:
      command: [uv, run, service-health]
      destructive: false
      timeout_seconds: 10
      mode: [standalone, suite]
      description: Check service health endpoint
  db:
    verify:
      command: [uv, run, db-verify]
      destructive: false
      timeout_seconds: 60
      mode: [standalone, suite]
      description: Verify database connectivity and schema
    reset-schema:
      command: [uv, run, db-reset-schema]
      destructive: true
      timeout_seconds: 300
      requires_confirmation: true
      mode: [standalone, suite]
      description: Drop and recreate all schema objects
    reset-data:
      command: [uv, run, db-reset-data]
      destructive: true
      timeout_seconds: 300
      requires_confirmation: true
      mode: [standalone, suite]
      description: Truncate all data, preserve schema
  auth:
    verify:
      command: [uv, run, auth0-verify]
      destructive: false
      timeout_seconds: 60
      mode: [standalone, suite]
      description: Verify Auth0 configuration
  seed:
    rules:
      command: [uv, run, seed-rules]
      destructive: false
      timeout_seconds: 180
      mode: [standalone, suite]
      description: Seed default fraud rules
  storage:
    verify:
      command: [uv, run, storage-verify]
      destructive: false
      timeout_seconds: 60
      mode: [standalone, suite]
      description: Verify MinIO connectivity and bucket
```

## Example: transaction-management

```yaml
service: transaction-management
version: "1.0"
entrypoints:
  service:
    status:
      command: [uv, run, service-status]
      destructive: false
      timeout_seconds: 10
      mode: [standalone, suite]
    health:
      command: [uv, run, service-health]
      destructive: false
      timeout_seconds: 10
      mode: [standalone, suite]
  db:
    verify:
      command: [uv, run, db-verify]
      destructive: false
      timeout_seconds: 60
      mode: [standalone, suite]
    reset-schema:
      command: [uv, run, db-reset-schema]
      destructive: true
      timeout_seconds: 300
      requires_confirmation: true
      mode: [standalone, suite]
    reset-data:
      command: [uv, run, db-reset-data]
      destructive: true
      timeout_seconds: 300
      requires_confirmation: true
      mode: [standalone, suite]
  auth:
    verify:
      command: [uv, run, auth0-verify]
      destructive: false
      timeout_seconds: 60
      mode: [standalone, suite]
  messaging:
    verify:
      command: [uv, run, kafka-verify]
      destructive: false
      timeout_seconds: 60
      mode: [standalone, suite]
    replay-events:
      command: [uv, run, replay-events]
      destructive: true
      timeout_seconds: 600
      requires_confirmation: true
      mode: [suite]
      description: Replay events from topic offset
    clear-dlq:
      command: [uv, run, clear-dlq]
      destructive: true
      timeout_seconds: 300
      requires_confirmation: true
      mode: [suite]
      description: Clear dead letter queue
  seed:
    transactions:
      command: [uv, run, seed-transactions]
      destructive: false
      timeout_seconds: 180
      mode: [standalone, suite]
```

## Action Domain Conventions

| Domain | Typical Actions | Destructive? |
|--------|-----------------|--------------|
| `service` | status, health, logs | No |
| `db` | verify, reset-schema, reset-data, reset-tables | Yes (selective) |
| `auth` | verify | No |
| `messaging` | verify, replay-events, clear-dlq | Yes (selective) |
| `storage` | verify | No |
| `runtime` | verify, restart | No |
| `seed` | * (service-specific) | No |
| `verify` | * (service-specific) | No |

## Output Format

All adapter commands should output JSON to stdout:

```json
{
  "success": true,
  "action": "db-verify",
  "duration_ms": 150,
  "data": {
    "connected": true,
    "schema_version": "20240315",
    "tables_count": 12
  }
}
```

On failure:

```json
{
  "success": false,
  "action": "db-reset-schema",
  "error": "connection refused",
  "details": "postgres://..."
}
```

## Versioning

- Manifest version follows semver (1.0, 1.1, etc.)
- Platform should warn when service manifest version is older than expected
- Backward compatibility: platform must accept older manifest versions that contain a subset of current fields
