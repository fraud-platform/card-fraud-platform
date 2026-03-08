"""Table presenter for human-readable output."""

from typing import Any


def format_table(headers: list[str], rows: list[list[Any]]) -> str:
    """Format data as a table."""
    if not rows:
        return "No data"

    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    lines = []

    header_line = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
    lines.append(header_line)
    lines.append("-" * len(header_line))

    for row in rows:
        row_line = " | ".join(str(cell).ljust(w) for cell, w in zip(row, col_widths))
        lines.append(row_line)

    return "\n".join(lines)


def format_service_status(services: dict[str, Any]) -> str:
    """Format service status for display."""
    headers = ["Service", "Runtime", "Port", "Container", "Status"]
    rows = []

    for service_id, info in services.items():
        container_state = info.get("container_state", "unknown")
        rows.append(
            [
                service_id,
                info.get("runtime", ""),
                str(info.get("port", "")),
                info.get("container", ""),
                container_state,
            ]
        )

    return format_table(headers, rows)


def format_inventory(collector: str, data: dict[str, Any]) -> str:
    """Format inventory data for display."""
    lines = [f"\n## {collector}", "=" * len(collector)]

    def format_dict(d: dict, indent: int = 0):
        result = []
        prefix = "  " * indent
        for key, value in d.items():
            if isinstance(value, dict):
                result.append(f"{prefix}{key}:")
                result.append(format_dict(value, indent + 1))
            elif isinstance(value, list):
                result.append(f"{prefix}{key}:")
                for item in value:
                    result.append(f"{prefix}  - {item}")
            else:
                result.append(f"{prefix}{key}: {value}")
        return "\n".join(result)

    lines.append(format_dict(data))
    return "\n".join(lines)
