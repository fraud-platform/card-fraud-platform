"""JSON presenter for machine-readable output."""

import json
from typing import Any


def format_json(data: Any, indent: int = 2) -> str:
    """Format data as JSON."""
    return json.dumps(data, indent=indent, default=str)


def format_action_json(result) -> str:
    """Format action result as JSON."""
    return format_json(result.to_dict())


def format_inventory_json(results: list) -> str:
    """Format inventory results as JSON."""
    data = {
        "results": [
            {
                "collector": r.collector,
                "success": r.success,
                "data": r.data,
                "error": r.error,
            }
            for r in results
        ]
    }
    return format_json(data)


def format_health_json(results: list) -> str:
    """Format health results as JSON."""
    data = {"services": [r.to_dict() for r in results]}
    return format_json(data)
