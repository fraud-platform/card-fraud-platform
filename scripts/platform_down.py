"""
Stop platform containers and optionally remove data.

Usage:
    uv run platform-down       # Stop all containers (keep data)
    uv run platform-reset      # Stop all containers and remove data volumes
"""

from __future__ import annotations

import subprocess
import sys

from scripts.constants import APPS_COMPOSE_FILE, COMPOSE_FILE, COMPOSE_PROJECT, PLATFORM_PROFILE


def _compose_down_command(*, remove_volumes: bool) -> list[str]:
    """Build docker compose command for full platform stack shutdown."""
    cmd = [
        "docker",
        "compose",
        "-f",
        COMPOSE_FILE,
        "-f",
        APPS_COMPOSE_FILE,
        "-p",
        COMPOSE_PROJECT,
        "--profile",
        PLATFORM_PROFILE,
        "--profile",
        "load-testing",
        "down",
    ]

    if remove_volumes:
        cmd.append("-v")

    return cmd


def main() -> int:
    """Stop all platform containers while preserving volumes."""
    print("Card Fraud Platform - Stopping all containers...")
    print()

    cmd = _compose_down_command(remove_volumes=False)
    print(f"  > {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print()
        print("All containers stopped. Data volumes preserved.")
        print("Use 'uv run platform-reset' to also remove data.")

    return result.returncode


def reset() -> int:
    """Stop all platform containers and remove data volumes."""
    print("Card Fraud Platform - Stopping all containers and removing ALL data...")
    print()

    cmd = _compose_down_command(remove_volumes=True)
    print(f"  > {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print()
        print("All containers stopped and data removed.")
        print("Run 'doppler run -- uv run platform-up' to start fresh.")

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
