"""
Show suite-aware platform status.

Usage:
    uv run platform-status
    uv run platform-status --json
"""

from __future__ import annotations

import argparse
import sys

from scripts.control_plane.health import check_all_services_health
from scripts.control_plane.inventory.services import ServicesCollector
from scripts.control_plane.presenters.json_output import format_health_json
from scripts.control_plane.presenters.summary import format_summary
from scripts.control_plane.registry import get_registry


def _collect_status() -> tuple[dict, list]:
    """Collect service metadata and health aggregates."""
    registry = get_registry()
    services_result = ServicesCollector(registry).collect()
    services_data = services_result.data if services_result.success and services_result.data else {}
    health_results = check_all_services_health(registry)
    return services_data, health_results


def render_status(*, json_mode: bool) -> str:
    """Render the status output."""
    services_data, health_results = _collect_status()
    if json_mode:
        return format_health_json(health_results)
    return format_summary(services_data, health_results)


def main() -> int:
    parser = argparse.ArgumentParser(description="Card Fraud Platform status view")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()
    print(render_status(json_mode=args.json))
    return 0


if __name__ == "__main__":
    sys.exit(main())
