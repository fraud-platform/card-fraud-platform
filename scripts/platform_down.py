"""
Stop platform infrastructure and optionally remove data.

Usage:
    uv run platform-down       # Stop all containers (keep data)
    uv run platform-reset      # Stop and remove all data
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

COMPOSE_FILE = str(Path(__file__).parent.parent / "docker-compose.yml")
APPS_COMPOSE_FILE = str(Path(__file__).parent.parent / "docker-compose.apps.yml")


def main() -> int:
    """Stop all platform containers (keep data)."""
    print("Card Fraud Platform - Stopping all containers...")
    print()

    # Stop apps first if they're running
    apps_cmd = [
        "docker", "compose",
        "-f", COMPOSE_FILE,
        "-f", APPS_COMPOSE_FILE,
        "-p", "card-fraud-platform",
        "--profile", "apps",
        "--profile", "load-testing",
        "down",
    ]
    print(f"  > {' '.join(apps_cmd)}")
    subprocess.run(apps_cmd)

    print()
    print("All containers stopped. Data volumes preserved.")
    print("Use 'uv run platform-reset' to also remove data.")
    return 0


def reset() -> int:
    """Stop all containers and remove all data volumes."""
    print("Card Fraud Platform - Stopping and removing ALL data...")
    print()

    cmd = [
        "docker", "compose",
        "-f", COMPOSE_FILE,
        "-f", APPS_COMPOSE_FILE,
        "-p", "card-fraud-platform",
        "--profile", "apps",
        "--profile", "load-testing",
        "down", "-v",
    ]
    print(f"  > {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print()
        print("All containers stopped and data removed.")
        print("Run 'uv run platform-up' to start fresh.")

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
