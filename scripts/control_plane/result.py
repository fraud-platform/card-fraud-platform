"""Result serialization for control plane."""

import json
from typing import Any

from .models import ActionResult, InventorySnapshot


def serialize_action_result(result: ActionResult, json_mode: bool = False) -> str:
    """Serialize an action result for output."""
    if json_mode:
        return json.dumps(result.to_dict(), indent=2)

    lines = [
        f"Service:    {result.service}",
        f"Domain:     {result.domain}",
        f"Action:     {result.action}",
        f"Status:     {result.status.value}",
        f"Summary:    {result.summary}",
    ]

    if result.details:
        lines.append("Details:")
        for detail in result.details:
            lines.append(f"  - {detail}")

    if result.error:
        lines.append(f"Error:      {result.error}")

    if result.next_steps:
        lines.append("Next Steps:")
        for step in result.next_steps:
            lines.append(f"  - {step}")

    return "\n".join(lines)


def serialize_inventory_snapshot(
    snapshot: InventorySnapshot, json_mode: bool = False
) -> str:
    """Serialize an inventory snapshot for output."""
    if json_mode:
        data = {"records": []}
        for record in snapshot.records:
            data["records"].append(
                {
                    "collector": record.collector,
                    "scope": record.scope,
                    "data": record.data,
                    "timestamp": record.timestamp.isoformat(),
                }
            )
        return json.dumps(data, indent=2)

    lines = []
    for record in snapshot.records:
        lines.append(f"\n## {record.collector}: {record.scope}")
        lines.append(_format_dict(record.data))

    return "\n".join(lines)


def serialize_health(health_list: list, json_mode: bool = False) -> str:
    """Serialize health check results."""
    if json_mode:
        data = {"services": [h.to_dict() for h in health_list]}
        return json.dumps(data, indent=2)

    lines = ["Service Health Status", "=" * 50]
    for h in health_list:
        status_icon = "✓" if h.status.value == "healthy" else "✗"
        lines.append(f"{status_icon} {h.service:30} {h.status.value:15} {h.message}")

    return "\n".join(lines)


def _format_dict(d: dict[str, Any], indent: int = 0) -> str:
    """Format a dictionary for human output."""
    lines = []
    prefix = "  " * indent
    for key, value in d.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            lines.append(_format_dict(value, indent + 1))
        elif isinstance(value, list):
            lines.append(f"{prefix}{key}:")
            for item in value:
                lines.append(f"{prefix}  - {item}")
        else:
            lines.append(f"{prefix}{key}: {value}")
    return "\n".join(lines)
