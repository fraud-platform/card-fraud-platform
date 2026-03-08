# Development

Day-to-day workflows, architecture notes, and contributor practices.

## Published Files

- `platform-control-plane/README.md` - index for the platform control-plane architecture and design set
- `platform-control-plane/00-operating-model.md` - enterprise operating model and ownership boundaries
- `platform-control-plane/01-admin-action-contract.md` - standard admin action contract and safeguards
- `platform-control-plane/02-inventory-and-observability-model.md` - suite inventory and read-only oversight model
- `platform-control-plane/03-secrets-and-configuration-ownership.md` - Doppler ownership and shared config rules
- `platform-control-plane/04-docs-and-governance-model.md` - docs consolidation and governance model
- `platform-control-plane/05-card-fraud-platform.md` - platform repo future-state plan
- `platform-control-plane/06-card-fraud-rule-management.md` - rule-management future-state plan
- `platform-control-plane/07-card-fraud-rule-engine-auth.md` - AUTH runtime future-state plan
- `platform-control-plane/08-card-fraud-rule-engine-monitoring.md` - MONITORING runtime future-state plan
- `platform-control-plane/09-card-fraud-transaction-management.md` - transaction-management future-state plan
- `platform-control-plane/10-card-fraud-intelligence-portal.md` - portal future-state plan
- `platform-control-plane/11-card-fraud-e2e-load-testing.md` - e2e/load future-state plan
- `platform-control-plane/12-card-fraud-ops-analyst-agent.md` - ops-agent future-state plan
- `platform-control-plane/13-cross-repo-summary.md` - suite summary matrix for runtime, ownership, and action domains
- `platform-control-plane/14-service-registry-format.md` - concrete service registry and adapter manifest format
- `platform-control-plane/15-phase-1-implementation-backlog.md` - phased execution backlog derived from the approved design pack
- `platform-control-plane/16-phase-2-platform-internals-design.md` - detailed technical design for Phase 2 implementation inside the platform repo
- `platform-control-plane/17-platform-adapter-schema.md` - canonical schema and validation rules for platform adapter manifests
- `platform-control-plane/18-db-ownership.md` - database ownership matrix for tables and indexes
- `platform-control-plane/19-kafka-ownership.md` - Kafka topic and consumer-group ownership matrix
- `platform-control-plane/20-minio-ownership.md` - MinIO bucket and artifact ownership matrix
- `platform-control-plane/21-auth0-ownership.md` - Auth0 ownership boundaries and integration model
- `platform-control-plane/22-doppler-ownership.md` - Doppler key ownership matrix and governance rules
- `platform-control-plane/23-phase-implementation-validation.md` - validation report for Phase 1 and Phase 2 implementation status

## Naming Rules

- Use lowercase kebab-case for new topic docs.
- Keep each section focused on the section purpose.
- Publish design docs only when they are current, authoritative, and implementation-ready.
