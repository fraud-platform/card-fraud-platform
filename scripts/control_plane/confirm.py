"""Confirmation dialogs for destructive actions."""

import sys


class ConfirmationError(Exception):
    """Error during confirmation."""

    pass


def confirm_destructive(
    service: str,
    domain: str,
    action: str,
    yes_flag: bool = False,
    confirm_token: str | None = None,
) -> bool:
    """Confirm a destructive action.

    Args:
        service: Service name
        domain: Action domain
        action: Action name
        yes_flag: Whether --yes flag was passed
        confirm_token: Explicit confirmation token

    Returns:
        True if confirmed

    Raises:
        ConfirmationError: If confirmation is required but not given
    """
    expected_token = f"{service}:{domain}:{action}"
    has_token = bool(confirm_token)

    if yes_flag and confirm_token == expected_token:
        return True

    if yes_flag or has_token:
        raise ConfirmationError(
            "Destructive actions require both --yes and "
            f"--confirm {expected_token}"
        )

    if not sys.stdin.isatty():
        raise ConfirmationError(
            f"Destructive action {domain}:{action} on {service} requires "
            f"explicit confirmation. Use --yes --confirm {expected_token}"
        )

    print(f"\nWARNING: This is a DESTRUCTIVE action: {service} {domain}:{action}")
    response = input("Do you want to continue? [y/N]: ").strip().lower()

    if response in ("y", "yes"):
        return True

    raise ConfirmationError("Action cancelled by user")


def require_confirmation(
    service: str,
    domain: str,
    action: str,
    is_destructive: bool,
    yes_flag: bool = False,
    confirm_token: str | None = None,
) -> None:
    """Require confirmation for destructive actions.

    Args:
        service: Service name
        domain: Action domain
        action: Action name
        is_destructive: Whether the action is destructive
        yes_flag: Whether --yes flag was passed
        confirm_token: Explicit confirmation token

    Raises:
        ConfirmationError: If confirmation is required but not given
    """
    if not is_destructive:
        return

    if not confirm_destructive(service, domain, action, yes_flag, confirm_token):
        raise ConfirmationError("Action cancelled")
