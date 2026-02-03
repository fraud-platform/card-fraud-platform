"""Shared subprocess runner for platform scripts."""

from __future__ import annotations

import subprocess
import sys


def run(cmd: list[str], check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    """Run a command, printing it first."""
    print(f"  > {' '.join(cmd)}")
    return subprocess.run(
        cmd,
        check=check,
        capture_output=capture,
        text=True if capture else None,
    )


def run_quiet(cmd: list[str]) -> subprocess.CompletedProcess:
    """Run a command silently, capturing output."""
    return subprocess.run(cmd, capture_output=True, text=True)


def get_platform_root() -> str:
    """Get the platform project root directory."""
    from pathlib import Path

    return str(Path(__file__).parent.parent)
