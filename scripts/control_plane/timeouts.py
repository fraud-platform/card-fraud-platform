"""Timeout constants and helpers for control plane actions."""

from typing import Final

DEFAULT_TIMEOUTS: Final[dict[str, int]] = {
    "status": 10,
    "health": 10,
    "verify": 60,
    "bootstrap": 180,
    "db-init": 180,
    "db-reset-schema": 300,
    "db-reset-data": 300,
    "db-reset-tables": 300,
    "seed": 180,
    "logs": 0,
}


def get_timeout(action_name: str, manifest_timeout: int | None = None) -> int:
    """Get timeout for an action.

    Args:
        action_name: Name of the action
        manifest_timeout: Timeout from manifest (if any)

    Returns:
        Timeout in seconds
    """
    if manifest_timeout is not None:
        return manifest_timeout

    for key, timeout in DEFAULT_TIMEOUTS.items():
        if key in action_name.lower():
            return timeout

    return 60
