"""
Smart platform startup - only starts containers that aren't already running.

Usage:
    doppler run -- uv run platform-up              # Start all shared infrastructure
    doppler run -- uv run platform-up -- --apps    # Start infra + application containers

All environment variables (secrets, config) are injected by Doppler.
Run `doppler setup` once in the platform directory to configure.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# Expected infrastructure containers
INFRA_CONTAINERS = [
    "card-fraud-postgres",
    "card-fraud-minio",
    "card-fraud-redis",
    "card-fraud-redpanda",
    "card-fraud-redpanda-console",
]
CONFLICT_PRONE_CONTAINERS = INFRA_CONTAINERS + ["card-fraud-minio-init"]

COMPOSE_FILE = str(Path(__file__).parent.parent / "docker-compose.yml")
APPS_COMPOSE_FILE = str(Path(__file__).parent.parent / "docker-compose.apps.yml")
COMPOSE_PROJECT = "card-fraud-platform"


def _is_container_running(name: str) -> bool:
    """Check if a container is running and healthy."""
    result = subprocess.run(
        ["docker", "inspect", "--format", "{{.State.Status}}", name],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == "running"


def _container_exists(name: str) -> bool:
    """Check whether a container exists."""
    result = subprocess.run(
        ["docker", "inspect", name],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _container_compose_project(name: str) -> str:
    """Get docker compose project label for a container (if any)."""
    result = subprocess.run(
        [
            "docker",
            "inspect",
            "--format",
            "{{ index .Config.Labels \"com.docker.compose.project\" }}",
            name,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return ""
    return (result.stdout or "").strip()


def _cleanup_conflicting_containers() -> None:
    """
    Remove stale containers with expected names but from another compose project.

    This prevents "container name already in use" errors when local dev has stale
    containers created outside this compose project.
    """
    for name in CONFLICT_PRONE_CONTAINERS:
        if not _container_exists(name):
            continue
        project = _container_compose_project(name)
        if project and project == COMPOSE_PROJECT:
            continue

        print(
            f"[WARN] Found conflicting container '{name}' "
            f"(compose project: '{project or 'unknown'}'). Removing..."
        )
        subprocess.run(["docker", "rm", "-f", name], check=False)


def _get_running_containers() -> dict[str, bool]:
    """Check which infrastructure containers are already running."""
    status = {}
    for name in INFRA_CONTAINERS:
        status[name] = _is_container_running(name)
    return status


def _print_status(status: dict[str, bool]) -> None:
    """Print container status table."""
    print()
    print("=" * 60)
    print(f"  {'Container':<35} {'Status':<15}")
    print("-" * 60)
    for name, running in status.items():
        icon = "[OK]" if running else "[--]"
        state = "running" if running else "stopped"
        print(f"  {icon} {name:<31} {state}")
    print("=" * 60)


def _check_doppler_env() -> bool:
    """Check if required Doppler env vars are present."""
    required = [
        "POSTGRES_ADMIN_PASSWORD",
        "FRAUD_GOV_APP_PASSWORD",
        "MINIO_ROOT_USER",
        "MINIO_ROOT_PASSWORD",
        "S3_BUCKET_NAME",
    ]
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        print("[ERROR] Missing required environment variables:")
        for v in missing:
            print(f"  - {v}")
        print()
        print("Run with Doppler to inject secrets:")
        print("  doppler run -- uv run platform-up")
        print()
        print("Or run `doppler setup` first if not configured.")
        return False
    return True


def _start_apps() -> int:
    """Start application containers when --apps is requested."""
    print()
    print("Starting application containers...")
    apps_cmd = [
        "docker", "compose",
        "-f", COMPOSE_FILE,
        "-f", APPS_COMPOSE_FILE,
        "-p", "card-fraud-platform",
        "--profile", "apps",
        "up", "-d",
    ]
    print(f"  > {' '.join(apps_cmd)}")
    result = subprocess.run(apps_cmd)
    if result.returncode != 0:
        print()
        print("[ERROR] Failed to start application containers.")
        return result.returncode
    return 0


def main() -> int:
    """Start shared infrastructure (smart - skips running containers)."""
    print("Card Fraud Platform - Starting shared infrastructure...")
    print()

    if not _check_doppler_env():
        return 1

    _cleanup_conflicting_containers()

    # Check current state
    status = _get_running_containers()
    running_count = sum(1 for v in status.values() if v)
    total = len(INFRA_CONTAINERS)

    if running_count == total:
        print(f"All {total} infrastructure containers already running.")
        _print_status(status)
        if "--apps" in sys.argv:
            apps_rc = _start_apps()
            if apps_rc != 0:
                return apps_rc
            print()
            print("Infrastructure already running; apps were (re)started.")
            print("Use 'uv run platform-status' for details.")
            return 0
        print()
        print("Nothing to start. Use 'uv run platform-status' for details.")
        return 0

    if running_count > 0:
        print(f"{running_count}/{total} containers already running.")
        print("Starting remaining containers...")
    else:
        print(f"Starting all {total} infrastructure containers...")

    # Start infrastructure
    print()
    cmd = [
        "docker", "compose",
        "-f", COMPOSE_FILE,
        "-p", COMPOSE_PROJECT,
        "up", "-d",
    ]
    print(f"  > {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print()
        print("[ERROR] Failed to start infrastructure.")
        return 1

    # Check if --apps flag was passed
    if "--apps" in sys.argv:
        apps_rc = _start_apps()
        if apps_rc != 0:
            return apps_rc

    # Show final status
    print()
    final_status = _get_running_containers()
    _print_status(final_status)

    print()
    print("Infrastructure endpoints:")
    print("  PostgreSQL : localhost:5432 (fraud_gov)")
    print("  Redis      : localhost:6379")
    print("  MinIO API  : http://localhost:9000")
    print("  MinIO UI   : http://localhost:9001")
    print("  Kafka      : localhost:9092")
    print("  Redpanda UI: http://localhost:8083")
    print()
    print("Credentials are managed by Doppler (card-fraud-platform project).")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
