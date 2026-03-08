# Database Ownership Artifact

> Status: approved

## Purpose

Define explicit table and index ownership across all DB-owning services in the card-fraud suite.

All tables reside in the `fraud_gov` schema in the shared PostgreSQL instance.

---

## Ownership Map

### rule-management

| Table | Type | Owner | Description |
|-------|------|-------|-------------|
| `rule_fields` | table | rule-management | Field definitions for rule conditions |
| `rule_field_versions` | table | rule-management | Version history for rule fields |
| `rule_field_metadata` | table | rule-management | Metadata for rule fields |
| `rules` | table | rule-management | Core fraud rule definitions |
| `rule_versions` | table | rule-management | Version history for rules |
| `ruleset_manifests` | table | rule-management | Compiled ruleset metadata |
| `field_registry_manifests` | table | rule-management | Field registry snapshots |
| `rulesets` | table | rule-management | Ruleset containers |
| `ruleset_versions` | table | rule-management | Version history for rulesets |
| `ruleset_version_rules` | table | rule-management | Many-to-many: rulesets ↔ rules |
| `approvals` | table | rule-management | Rule/ruleset approval workflow |
| `audit_logs` | table | rule-management | Audit trail for all changes |

### Indices

- `idx_rule_fields_field_id` on `rule_fields(field_id)`
- `idx_rule_fields_field_key` on `rule_fields(field_key)`
- `idx_rule_versions_rule_id` on `rule_versions(rule_id)`
- `idx_rules_ruleset_id` on `rules(ruleset_id)`
- `idx_rules_status` on `rules(status)`
- `idx_ruleset_versions_ruleset_id` on `ruleset_versions(ruleset_id)`
- `idx_audit_logs_entity` on `audit_logs(entity_type, entity_id)`

---

### transaction-management

| Table | Type | Owner | Description |
|-------|------|-------|-------------|
| `transactions` | table | transaction-management | Core transaction records |
| `transaction_rule_matches` | table | transaction-management | Rule evaluation results per transaction |
| `transaction_reviews` | table | transaction-management | Analyst review records |
| `analyst_notes` | table | transaction-management | Notes added by analysts |
| `transaction_cases` | table | transaction-management | Case containers for related transactions |
| `case_activity_log` | table | transaction-management | Activity audit for cases |

### Indices

- `idx_transactions_card_id` on `transactions(card_id)`
- `idx_transactions_merchant_id` on `transactions(merchant_id)`
- `idx_transactions_timestamp` on `transactions(timestamp)`
- `idx_transactions_status` on `transactions(status)`
- `idx_transactions_idempotency_key` on `transactions(idempotency_key)` UNIQUE
- `idx_transaction_rule_matches_transaction_id` on `transaction_rule_matches(transaction_id)`
- `idx_transaction_reviews_transaction_id` on `transaction_reviews(transaction_id)`
- `idx_transaction_reviews_analyst_id` on `transaction_reviews(analyst_id)`
- `idx_analyst_notes_case_id` on `analyst_notes(case_id)`
- `idx_transaction_cases_status` on `transaction_cases(status)`

---

### ops-analyst-agent

| Table | Type | Owner | Description |
|-------|------|-------|-------------|
| `ops_agent_investigations` | table | ops-analyst-agent | Investigation records |
| `ops_agent_investigation_state` | table | ops-analyst-agent | LangGraph state snapshots |
| `ops_agent_tool_execution_log` | table | ops-analyst-agent | Tool execution history |
| `ops_agent_transaction_embeddings` | table | ops-analyst-agent | Vector embeddings for transactions |
| `ops_agent_insights` | table | ops-analyst-agent | AI-generated insights |
| `ops_agent_evidence` | table | ops-analyst-agent | Evidence items linked to investigations |
| `ops_agent_recommendations` | table | ops-analyst-agent | AI recommendations |
| `ops_agent_rule_drafts` | table | ops-analyst-agent | Draft rules created by agent |
| `ops_agent_audit_log` | table | ops-analyst-agent | Agent action audit trail |

### Indices

- `idx_investigations_status` on `ops_agent_investigations(status)`
- `idx_investigations_transaction_id` on `ops_agent_investigations(transaction_id)`
- `idx_investigation_state_investigation_id` on `ops_agent_investigation_state(investigation_id)`
- `idx_tool_execution_investigation_id` on `ops_agent_tool_execution_log(investigation_id)`
- `idx_tool_execution_timestamp` on `ops_agent_tool_execution_log(started_at)`
- `idx_transaction_embeddings_transaction_id` on `ops_agent_transaction_embeddings(transaction_id)`
- `idx_insights_investigation_id` on `ops_agent_insights(investigation_id)`

---

## Ownership Boundaries

### Shared Tables

No tables are shared between services. Each service owns its dedicated tables.

### Cross-Service Queries

The following cross-service joins are expected and supported:

- `transactions` + `transaction_rule_matches` + `rules` (via transaction-management)
- `transactions` + `transaction_reviews` + `analyst_notes` (via transaction-management)
- `ops_agent_investigations` + `transactions` (via ops-analyst-agent read-only)
- `ops_agent_rule_drafts` + `rules` (via ops-analyst-agent write, rule-management read)

### Migration Responsibility

| Service | Migration Tool | Location |
|---------|-----------------|----------|
| rule-management | Alembic | `card-fraud-rule-management/alembic/` |
| transaction-management | SQL scripts | `card-fraud-transaction-management/db/` |
| ops-analyst-agent | SQL scripts | `card-fraud-ops-analyst-agent/db/migrations/` |

---

## Reset Scope Definitions

- **db-reset-schema**: Drop and recreate all owned tables and indices, then re-run migrations
- **db-reset-data**: TRUNCATE all owned tables, preserving schema and indices
- **db-reset-tables**: DROP and CREATE owned tables only (no indices or constraints)

Each service must declare which reset scopes it supports in its `platform-adapter.yaml`.

---

## Future Considerations

- Consider adding foreign key constraints between services for data integrity
- Consider adding shared `alerts` table if needed across services
- Vector similarity search on `ops_agent_transaction_embeddings` requires pgvector extension
