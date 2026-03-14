"""
Shared constants for platform scripts.

This module defines common values used across multiple platform scripts
to avoid duplication and ensure consistency.
"""

from __future__ import annotations

from pathlib import Path

# Platform root directory
PLATFORM_ROOT = Path(__file__).parent.parent

# Docker Compose project name
COMPOSE_PROJECT = "card-fraud-platform"
PLATFORM_PROFILE = "platform"

# Docker Compose file paths
COMPOSE_FILE = str(PLATFORM_ROOT / "docker-compose.yml")
APPS_COMPOSE_FILE = str(PLATFORM_ROOT / "docker-compose.apps.yml")
JFR_OVERRIDE_COMPOSE_FILE = str(PLATFORM_ROOT / "docker-compose.override.jfr.yml")

# Infrastructure container names
INFRA_CONTAINERS = [
    "card-fraud-postgres",
    "card-fraud-minio",
    "card-fraud-redis",
    "card-fraud-redpanda",
    "card-fraud-redpanda-console",
    "card-fraud-jaeger",
    "card-fraud-prometheus",
    "card-fraud-grafana",
]

# All containers managed by the platform (for status display)
ALL_CONTAINERS = {
    "Infrastructure": [
        ("card-fraud-postgres", "PostgreSQL 18", "5432"),
        ("card-fraud-minio", "MinIO S3", "9000, 9001"),
        ("card-fraud-minio-init", "MinIO Init", "-"),
        ("card-fraud-redis", "Redis 8.4", "6379"),
        ("card-fraud-redpanda", "Redpanda/Kafka", "9092, 9644"),
        ("card-fraud-redpanda-console", "Redpanda Console", "8083"),
        ("card-fraud-jaeger", "Jaeger Tracing", "16686, 4317, 4318"),
        ("card-fraud-prometheus", "Prometheus", "9090"),
        ("card-fraud-grafana", "Grafana", "3000"),
    ],
    "Applications": [
        ("card-fraud-rule-management", "Rule Management API", "8000"),
        ("card-fraud-rule-engine-auth", "Rule Engine AUTH", "8081"),
        ("card-fraud-rule-engine-monitoring", "Rule Engine MONITORING", "8082"),
        ("card-fraud-transaction-management", "Transaction Mgmt API", "8002"),
        ("card-fraud-ops-analyst-agent", "Ops Analyst Agent", "8003"),
        ("card-fraud-mcp-gateway", "MCP Gateway", "8005"),
        ("card-fraud-intelligence-portal", "Intelligence Portal", "5173"),
    ],
    "Testing": [
        ("card-fraud-locust", "Locust Load Testing", "8089"),
    ],
}

# Containers that may have naming conflicts
CONFLICT_PRONE_CONTAINERS = [container for groups in ALL_CONTAINERS.values() for container, _, _ in groups]

# Network name
NETWORK_NAME = "card-fraud-network"
