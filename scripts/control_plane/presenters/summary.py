"""Summary presenter for overview output."""

from .table import format_table


def format_summary(services_data: dict, health_data: list) -> str:
    """Format a summary view of the platform."""
    lines = [
        "Card Fraud Platform - Status Summary",
        "=" * 50,
    ]

    headers = ["Service", "Runtime", "Status", "Port"]
    rows = []

    for service_id, info in services_data.get("services", {}).items():
        health_status = "unknown"
        for h in health_data:
            if h.service == service_id:
                health_status = h.status.value
                break

        rows.append(
            [
                service_id,
                info.get("runtime", ""),
                health_status,
                str(info.get("port", "")),
            ]
        )

    lines.append(format_table(headers, rows))

    return "\n".join(lines)
