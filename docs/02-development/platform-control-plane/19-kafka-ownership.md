# Kafka Topic and Consumer Group Ownership Artifact

> Status: approved

## Purpose

Define explicit ownership of Kafka topics and consumer groups across all services in the card-fraud suite.

All messaging uses Redpanda (Kafka-compatible) as the event streaming platform.

---

## Ownership Map

### Topics

| Topic | Owner | Producer | Description |
|-------|-------|----------|-------------|
| `fraud.card.decisions.v1` | shared | rule-engine-auth, rule-engine-monitoring | Fraud decision events from rule engines |

### Consumer Groups

| Consumer Group | Owner | Topics Consumed | Description |
|----------------|-------|-----------------|-------------|
| `card-fraud-transaction-management` | transaction-management | `fraud.card.decisions.v1` | Persists decision events to DB |
| `card-fraud-transaction-management.dlq` | transaction-management | `fraud.card.decisions.v1.dlq.*` | Dead letter queue consumer |

---

## Topic Design

### fraud.card.decisions.v1

**Purpose**: Primary topic for fraud decision events emitted by rule engines.

**Producers**:
- `card-fraud-rule-engine-auth` (AUTH evaluation results)
- `card-fraud-rule-engine-monitoring` (MONITORING evaluation results)

**Schema**: Avro/JSON decision event schema (see `decision-event-schema-v2.md` in rule-engine repos)

**Retention**: 7 days default (configurable via Redpanda)

**Partitions**: 6 (recommended for throughput)

---

## Dead Letter Queue Pattern

### Overview

transaction-management implements a DLQ pattern for failed message processing:

- **Main Topic**: `fraud.card.decisions.v1`
- **DLQ Topic**: `fraud.card.decisions.v1.dlq.{environment}`

### DLQ Behavior

1. On processing failure, message is forwarded to DLQ topic with error metadata
2. DLQ consumer group processes DLQ topic for retry or manual inspection
3. Platform adapter can clear DLQ via `clear-dlq` action

---

## Consumer Group Responsibilities

### card-fraud-transaction-management

- Consumes from `fraud.card.decisions.v1`
- Persists decision events to `transactions` and `transaction_rule_matches` tables
- Handles schema evolution gracefully
- Implements DLQ forwarding on processing failures

---

## Topic Configuration

### Local Development

```bash
# Create topics via Redpanda
rpk topic create fraud.card.decisions.v1 -p 6
rpk topic create fraud.card.decisions.v1.dlq.local -p 3
```

### Topic Metadata

| Property | Value |
|----------|-------|
| Protocol | Kafka (Redpanda) |
| Bootstrap Servers | `localhost:9092` (local) |
| Security | SASL/PLAIN (production) |
| Schema Registry | Yes (Confluent Schema Registry compatible) |

---

## Future Considerations

- Add separate topic for AUTH vs MONITORING decisions if needed
- Add replay capability via offset reset
- Consider partition strategy for high-volume scenarios
