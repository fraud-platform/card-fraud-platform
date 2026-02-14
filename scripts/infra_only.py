#!/usr/bin/env python3
"""
Platform Infrastructure Orchestrator

This script ONLY handles platform infrastructure (Redis, Redpanda, MinIO).
It checks if infrastructure is running, and starts it only if down.

This is used by the 10K TPS validation script in card-fraud-rule-engine-auth.

Usage:
    python scripts/infra_only.py [--down] [--status]
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
NC = "\033[0m"


def log(msg, color=NC):
    print(f"{color}{msg}{NC}")


def run_command(cmd, check=True, capture_output=False):
    """Run a shell command."""
    log(f"Running: {' '.join(cmd)}", BLUE)
    return subprocess.run(cmd, shell=True, check=check, capture_output=capture_output)


def check_infra_status():
    """Check status of all platform infrastructure."""
    log("Checking platform infrastructure status...", BLUE)

    services = {
        "card-fraud-redis": "Redis",
        "card-fraud-redpanda": "Redpanda",
        "card-fraud-minio": "MinIO"
    }

    all_running = True

    for container, name in services.items():
        result = run_command(
            ["docker", "inspect", "-f", "{{.State.Health}}", container],
            check=False, capture_output=True
        )
        status = result.stdout.strip() if result.stdout else "unknown"

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


def start_infra():
    """Start platform infrastructure."""
    log("Starting platform infrastructure...", YELLOW)
    run_command(
        ["doppler", "run", "--", "uv", "run", "platform-up"]
    )
    log("✓ Platform infrastructure starting...", GREEN)
    log("Waiting 15 seconds for services to be healthy...", BLUE)

    import time
    for i in range(3):
        time.sleep(5)
        log(f"  {((i+1)*33}%)", BLUE)

    log("")
    return check_infra_status()


def stop_infra():
    """Stop platform infrastructure."""
    log("Stopping platform infrastructure...", YELLOW)
    run_command(
        ["uv", "run", "platform-down"],
        check=False
    )
    log("✓ Platform infrastructure stopped", GREEN)


def reset_infra():
    """Reset platform infrastructure (stop and remove data)."""
    log("Resetting platform infrastructure...", YELLOW)
    run_command(
        ["uv", "run", "platform-reset"],
        check=False
    )
    log("✓ Platform infrastructure reset", GREEN)


def main():
    parser = argparse.ArgumentParser(description="Platform Infrastructure Orchestrator")
    parser.add_argument("--status", action="store_true", help="Show infra status only")
    parser.add_argument("--down", action="store_true", help="Stop platform infrastructure")
    parser.add_argument("--reset", action="store_true", help="Stop and remove all data")
    args = parser.parse_args()

    log("="*60, BLUE)
    log("Platform Infrastructure Orchestrator", YELLOW)
    log("="*60 + "\n", NC)

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

