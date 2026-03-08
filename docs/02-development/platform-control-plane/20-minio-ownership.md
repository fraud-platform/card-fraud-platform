# MinIO / S3 Bucket Ownership Artifact

> Status: approved

## Purpose

Define explicit ownership of MinIO (S3-compatible) buckets and artifact paths across all services in the card-fraud suite.

---

## Ownership Map

### Buckets

| Bucket | Owner | Description |
|--------|-------|-------------|
| `fraud-gov-artifacts` | shared (platform) | Stores compiled rulesets and field registry manifests |

### Artifact Paths

| Path Prefix | Owner | Description |
|-------------|-------|-------------|
| `rulesets/{environment}/CARD_AUTH/*` | rule-management (write), rule-engine-auth (read) | Compiled AUTH ruleset JSON files |
| `rulesets/{environment}/CARD_MONITORING/*` | rule-management (write), rule-engine-monitoring (read) | Compiled MONITORING ruleset JSON files |
| `fields/{environment}/*` | rule-management (write), rule-engine-* (read) | Field registry manifests |

---

## Bucket Details

### fraud-gov-artifacts

**Purpose**: Primary artifact storage for compiled fraud rules and field registries.

**Owner**: Platform-managed (bucket created by `minio-init` container)

**Access Model**:
- **Write**: rule-management (publishes compiled rulesets)
- **Read**: rule-engine-auth, rule-engine-monitoring (load rulesets at runtime)

**Configuration**:
- Default bucket name: `fraud-gov-artifacts`
- Configured via `S3_BUCKET_NAME` environment variable
- Endpoint: `http://minio:9000` (local) or cloud endpoint (production)

---

## Artifact Path Structure

### Ruleset Artifacts

```
s3://fraud-gov-artifacts/rulesets/{environment}/{ruleset_key}/v{version}/ruleset.json
s3://fraud-gov-artifacts/rulesets/{environment}/{ruleset_key}/manifest.json
```

**Example**:
```
s3://fraud-gov-artifacts/rulesets/local/CARD_AUTH/v1/ruleset.json
s3://fraud-gov-artifacts/rulesets/local/CARD_AUTH/manifest.json
```

### Field Registry Artifacts

```
s3://fraud-gov-artifacts/fields/{environment}/v{version}/registry.json
s3://fraud-gov-artifacts/fields/{environment}/manifest.json
```

**Example**:
```
s3://fraud-gov-artifacts/fields/local/v1/registry.json
s3://fraud-gov-artifacts/fields/local/manifest.json
```

---

## Service Responsibilities

### rule-management

- **Write**: Publishes compiled rulesets to `rulesets/{env}/*`
- **Write**: Publishes field registry to `fields/{env}/*`
- **Read**: None (producer-only)

### rule-engine-auth

- **Read**: Loads rulesets from `rulesets/{env}/CARD_AUTH/*`
- **Read**: Loads field registry from `fields/{env}/*`

### rule-engine-monitoring

- **Read**: Loads rulesets from `rulesets/{env}/CARD_MONITORING/*`
- **Read**: Loads field registry from `fields/{env}/*`

---

## Bucket Creation

### Local Development

The bucket is automatically created by the `minio-init` container on first platform startup:

```yaml
# docker-compose.yml
minio-init:
  image: minio/mc
  command: mc mb local/fraud-gov-artifacts --ignore-existing
```

### Manual Creation

```bash
mc mb local/fraud-gov-artifacts
# or
aws --endpoint-url http://localhost:9000 s3 mb s3://fraud-gov-artifacts
```

---

## Verification Commands

```bash
# List bucket contents
mc ls local/fraud-gov-artifacts

# Verify connectivity
mc alias set local http://localhost:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD
mc ls local
```

---

## Future Considerations

- Add versioning for ruleset artifacts
- Consider lifecycle policies for old versions
- Add cross-region replication for production
