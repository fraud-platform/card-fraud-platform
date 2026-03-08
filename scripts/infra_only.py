#!/usr/bin/env python3
"""
Platform Infrastructure Orchestrator

This script ONLY handles platform infrastructure (Redis, Redpanda, MinIO).
It checks if infrastructure is running, and starts it only if down.

This is used by the 10K TPS validation script in card-fraud-rule-engine-auth.

Usage:
    python scripts/infra_only.py [--down] [--status]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from typing import Literal

# Color codes for terminal output
Color = Literal["", "\033[92m", "\033[91m", "\033[93m", "\033[94m", "\033[0m"]
GREEN: Color = "\033[92m"
RED: Color = "\033[91m"
YELLOW: Color = "\033[93m"
BLUE: Color = "\033[94m"
NC: Color = "\033[0m"


def log(msg: str, color: Color = NC) -> None:
    """Print a message with optional color formatting."""
    print(f"{color}{msg}{NC}")


def run_command(
    cmd: list[str], *, check: bool = True, capture_output: bool = False
) -> subprocess.CompletedProcess[bytes]:
    """Run a shell command and print it."""
    log(f"Running: {' '.join(cmd)}", BLUE)
    return subprocess.run(cmd, shell=True, check=check, capture_output=capture_output)


def check_infra_status() -> bool:
    """Check status of all platform infrastructure. Returns True if all healthy."""
    log("Checking platform infrastructure status...", BLUE)

    services: dict[str, str] = {
        "card-fraud-redis": "Redis",
        "card-fraud-redpanda": "Redpanda",
        "card-fraud-minio": "MinIO",
    }

    all_running = True

    for container, name in services.items():
        result = run_command(
            ["docker", "inspect", "-f", "{{.State.Health}}", container],
            check=False,
            capture_output=True,
        )
        status = result.stdout.strip().decode() if result.stdout else "unknown"

        if status == "healthy":
            log(f"  {name}: {status}", GREEN)
        else:
            log(f"  {name}: {status}", RED)
            all_running = False

    if all_running:
        log("✓ All infrastructure services are healthy", GREEN)
    else:
        log("⚠ Some infrastructure services are down", YELLOW)

    return all_running


def start_infra() -> bool:
    """Start platform infrastructure. Returns True if all services healthy."""
    log("Starting platform infrastructure...", YELLOW)
    run_command(["doppler", "run", "--", "uv", "run", "platform-up"])
    log("✓ Platform infrastructure starting...", GREEN)
    log("Waiting 15 seconds for services to be healthy...", BLUE)

    for i in range(3):
        time.sleep(5)
        log(f"  {((i + 1) * 33)}%", BLUE)

    log("")
    return check_infra_status()


def stop_infra() -> None:
    """Stop platform infrastructure."""
    log("Stopping platform infrastructure...", YELLOW)
    run_command(["uv", "run", "platform-down"], check=False)
    log("✓ Platform infrastructure stopped", GREEN)


def reset_infra() -> None:
    """Reset platform infrastructure (stop and remove data)."""
    log("Resetting platform infrastructure...", YELLOW)
    run_command(["uv", "run", "platform-reset"], check=False)
    log("✓ Platform infrastructure reset", GREEN)


def main() -> int:
    """Main entry point for the infrastructure orchestrator."""
    parser = argparse.ArgumentParser(description="Platform Infrastructure Orchestrator")
    parser.add_argument("--status", action="store_true", help="Show infra status only")
    parser.add_argument("--down", action="store_true", help="Stop platform infrastructure")
    parser.add_argument("--reset", action="store_true", help="Stop and remove all data")
    args = parser.parse_args()

    log("=" * 60, BLUE)
    log("Platform Infrastructure Orchestrator", YELLOW)
    log("=" * 60 + "\n", NC)

    try:
        if args.reset:
            reset_infra()
        elif args.down:
            stop_infra()
        elif args.status:
            check_infra_status()
        else:
            # Default behavior: check and start if needed
            if not check_infra_status():
                start_infra()

        return 0

    except KeyboardInterrupt:
        log("\n⚠ Interrupted by user", YELLOW)
        return 1
    except Exception as e:
        log(f"\n❌ Error: {e}", RED)
        return 1


if __name__ == "__main__":
    sys.exit(main())
