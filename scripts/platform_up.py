"""
Start the full Card Fraud platform stack as a single compose project.

Usage:
    doppler run -- uv run platform-up
    doppler run -- uv run platform-up -- --load-testing
    doppler run -- uv run platform-up -- --build
    doppler run -- uv run platform-up -- --force-recreate

All environment variables (secrets, config) are injected by Doppler.
Run `doppler setup` once in this directory to configure.
"""

from __future__ import annotations

import os
import subprocess
import sys

from scripts.constants import (
    APPS_COMPOSE_FILE,
    COMPOSE_FILE,
    COMPOSE_PROJECT,
    CONFLICT_PRONE_CONTAINERS,
    JFR_OVERRIDE_COMPOSE_FILE,
    PLATFORM_PROFILE,
)


def _check_docker_version() -> bool:
    """Verify Docker Compose v2 is available."""
    try:
        result = subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print("[ERROR] Docker Compose v2 is required but not found.")
            print()
            print("This platform uses 'docker compose' (v2 syntax), not 'docker-compose'.")
            print("Update Docker Desktop to the latest version or install Docker Compose v2.")
            return False

        if "Docker Compose version" not in result.stdout:
            print("[WARN] Unable to verify Docker Compose version format.")
            print(f"  Output: {result.stdout.strip()}")

        return True
    except FileNotFoundError:
        print("[ERROR] Docker is not installed or not in PATH.")
        print()
        print("Please install Docker Desktop:")
        print("  https://www.docker.com/products/docker-desktop")
        return False


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

    This prevents "container name already in use" errors when old local containers
    were created outside this compose project.
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
        result = subprocess.run(["docker", "rm", "-f", name], check=False)
        if result.returncode != 0:
            print(f"[WARN] Failed to remove container '{name}'")
        else:
            print(f"[OK] Removed conflicting container '{name}'")


def _check_doppler_env() -> bool:
    """Check if required Doppler env vars are present."""
    required = [
        "POSTGRES_ADMIN_PASSWORD",
        "FRAUD_GOV_APP_PASSWORD",
        "MINIO_ROOT_USER",
        "MINIO_ROOT_PASSWORD",
        "S3_BUCKET_NAME",
    ]
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        print("[ERROR] Missing required environment variables:")
        for name in missing:
            print(f"  - {name}")
        print()
        print("Run with Doppler to inject secrets:")
        print("  doppler run -- uv run platform-up")
        print()
        print("Or run `doppler setup` first if not configured.")
        return False
    return True


def _compose_up_command() -> list[str]:
    """Build docker compose command for full platform stack startup."""
    cmd = ["docker", "compose", "-f", COMPOSE_FILE, "-f", APPS_COMPOSE_FILE]

    if "--jfr" in sys.argv:
        cmd += ["-f", JFR_OVERRIDE_COMPOSE_FILE]

    cmd += ["-p", COMPOSE_PROJECT, "--profile", PLATFORM_PROFILE]

    if "--load-testing" in sys.argv:
        cmd += ["--profile", "load-testing"]

    cmd += ["up", "-d"]

    if "--build" in sys.argv:
        cmd.append("--build")
    if "--force-recreate" in sys.argv:
        cmd.append("--force-recreate")

    return cmd


def main() -> int:
    """Start the full platform stack (infra + apps) as one group."""
    print("Card Fraud Platform - Starting full platform stack (infra + apps)...")
    print()

    if "--apps" in sys.argv:
        print("[WARN] '--apps' is deprecated. Apps are started by default now.")
        print()

    if "--load-testing" in sys.argv:
        print("[INFO] '--load-testing' enabled; Locust profile will also be started.")
        print()

    if not _check_docker_version():
        return 1

    if not _check_doppler_env():
        return 1

    _cleanup_conflicting_containers()

    cmd = _compose_up_command()
    print(f"  > {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print()
        print("[ERROR] Failed to start platform stack.")
        return result.returncode

    print()
    print("Platform stack started.")
    print("Use 'uv run platform-status' to verify container health.")
    print("Use '--load-testing' when you want to include the Locust profile.")
    print()
    print("For targeted restarts (still same platform group):")
    print(
        "  doppler run -- docker compose -f docker-compose.yml -f docker-compose.apps.yml "
        "-p card-fraud-platform --profile platform up -d --build <service>"
    )
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
