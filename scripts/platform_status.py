"""
Show status of all platform containers.

Usage:
    uv run platform-status
"""

from __future__ import annotations

import subprocess
import sys

# All containers managed by the platform
ALL_CONTAINERS = {
    "Infrastructure": [
        ("card-fraud-postgres", "PostgreSQL 18", "5432"),
        ("card-fraud-minio", "MinIO S3", "9000, 9001"),
        ("card-fraud-minio-init", "MinIO Init", "-"),
        ("card-fraud-redis", "Redis 8.4", "6379"),
        ("card-fraud-redpanda", "Redpanda/Kafka", "9092, 9644"),
        ("card-fraud-redpanda-console", "Redpanda Console", "8083"),
    ],
    "Applications": [
        ("card-fraud-rule-management", "Rule Management API", "8000"),
        ("card-fraud-rule-engine", "Rule Engine", "8081"),
        ("card-fraud-transaction-management", "Transaction Mgmt API", "8002"),
        ("card-fraud-intelligence-portal", "Intelligence Portal", "5173"),
    ],
    "Testing": [
        ("card-fraud-locust", "Locust Load Testing", "8089"),
    ],
}


def _get_container_status(name: str) -> tuple[str, str]:
    """Get container status and health."""
    # First get status
    result = subprocess.run(
        ["docker", "inspect", "--format", "{{.State.Status}}", name],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return "not created", ""

    status = result.stdout.strip()

    # Then try to get health (may not exist for all containers)
    health_result = subprocess.run(
        ["docker", "inspect", "--format", "{{if .State.Health}}{{.State.Health.Status}}{{end}}", name],
        capture_output=True,
        text=True,
    )
    health = health_result.stdout.strip() if health_result.returncode == 0 else ""
    return status, health


def main() -> int:
    """Show status of all platform containers."""
    print()
    print("Card Fraud Platform - Container Status")
    print("=" * 72)

    for group_name, containers in ALL_CONTAINERS.items():
        print()
        print(f"  {group_name}:")
        print(f"  {'-' * 68}")
        print(f"  {'Container':<38} {'Ports':<14} {'Status':<20}")
        print(f"  {'-' * 68}")

        for name, description, ports in containers:
            status, health = _get_container_status(name)

            if status == "running":
                if health == "healthy":
                    icon = "[OK]"
                    display = "running (healthy)"
                elif health == "unhealthy":
                    icon = "[!!]"
                    display = "running (unhealthy)"
                else:
                    icon = "[OK]"
                    display = "running"
            elif status == "exited":
                # Init containers exit with 0 on success
                if "init" in name.lower():
                    icon = "[OK]"
                    display = "completed"
                else:
                    icon = "[--]"
                    display = "exited"
            elif status == "not created":
                icon = "[  ]"
                display = "not created"
            else:
                icon = "[??]"
                display = status

            print(f"  {icon} {description:<34} {ports:<14} {display}")

    # Network check
    print()
    net_result = subprocess.run(
        ["docker", "network", "inspect", "card-fraud-network"],
        capture_output=True,
        text=True,
    )
    if net_result.returncode == 0:
        print("  Network: card-fraud-network [OK]")
    else:
        print("  Network: card-fraud-network [NOT CREATED]")

    print()
    print("=" * 72)
    print()
    print("Commands:")
    print("  uv run platform-up      Start infrastructure")
    print("  uv run platform-down    Stop all containers")
    print("  uv run platform-reset   Stop and remove all data")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
