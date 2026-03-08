"""Platform control CLI entrypoint.

Usage:
    uv run platformctl status
    uv run platformctl inventory services
    uv run platformctl inventory infra
    uv run platformctl inventory redis
    uv run platformctl inventory db
    uv run platformctl inventory messaging
    uv run platformctl inventory storage
    uv run platformctl inventory auth
    uv run platformctl inventory secrets
    uv run platformctl action <domain> <action> <service>
    uv run platformctl registry validate
"""

import argparse
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))

from control_plane.adapter_manifest import load_adapter
from control_plane.audit import get_audit_logger
from control_plane.confirm import require_confirmation
from control_plane.health import check_all_services_health
from control_plane.inventory.services import ServicesCollector
from control_plane.inventory.docker_runtime import DockerRuntimeCollector
from control_plane.inventory.database import DatabaseCollector
from control_plane.inventory.messaging import MessagingCollector
from control_plane.inventory.storage import StorageCollector
from control_plane.inventory.auth import AuthCollector
from control_plane.inventory.secrets import SecretsCollector
from control_plane.inventory.redis_runtime import RedisRuntimeCollector
from control_plane.presenters.json_output import (
    format_action_json,
    format_health_json,
    format_inventory_json,
)
from control_plane.presenters.table import format_inventory
from control_plane.presenters.summary import format_summary
from control_plane.registry import get_registry
from control_plane.action_runner import run_action
from control_plane.models import ActionResult, ActionStatus, ExecutionMode

SCHEMA_RESET_ACK_TOKEN = "RESET_SHARED_SCHEMA"


def cmd_status(args) -> int:
    """Show platform status."""
    registry = get_registry()

    services_collector = ServicesCollector(registry)
    services_result = services_collector.collect()

    health_results = check_all_services_health(registry)

    if args.json:
        print(format_health_json(health_results))
    else:
        print(
            format_summary(
                services_result.data if services_result.data else {}, health_results
            )
        )
    return 0


def cmd_inventory(args) -> int:
    """Show platform inventory."""
    registry = get_registry()

    collectors = {
        "services": ServicesCollector(registry),
        "infra": DockerRuntimeCollector(),
        "redis": RedisRuntimeCollector(),
        "db": DatabaseCollector(),
        "messaging": MessagingCollector(),
        "storage": StorageCollector(),
        "auth": AuthCollector(registry=registry),
        "secrets": SecretsCollector(),
    }

    if args.scope == "all":
        selected = collectors
    elif args.scope == "infra":
        selected = {
            "infra": collectors["infra"],
            "redis": collectors["redis"],
        }
    else:
        selected = {args.scope: collectors.get(args.scope)}
        if not selected[args.scope]:
            print(f"Unknown inventory scope: {args.scope}")
            sys.exit(1)

    results = []
    for _, collector in selected.items():
        result = collector.collect()
        results.append(result)

    if args.json:
        print(format_inventory_json(results))
    else:
        for result in results:
            if result.success:
                print(format_inventory(result.collector, result.data or {}))
            else:
                print(f"Error in {result.collector}: {result.error}")
    return 0


def _is_container_running(container_name: str) -> bool:
    try:
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", container_name],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0 and "true" in result.stdout.lower()
    except Exception:
        return False


def _build_not_running_result(service_id: str, domain: str, action: str) -> ActionResult:
    return ActionResult(
        service=service_id,
        domain=domain,
        action=action,
        target="service",
        status=ActionStatus.FAILED,
        summary="Service container is not running",
        details=[
            "Platform precheck blocked adapter execution because the target container is not running."
        ],
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        next_steps=[
            "doppler run -- uv run platform-up",
            f"doppler run -- docker compose -f docker-compose.yml -f docker-compose.apps.yml --profile platform up -d --build {service_id}",
        ],
    )


def cmd_action(args) -> int:
    """Execute a platform action."""
    registry = get_registry()

    service = registry.get(args.service)
    if not service:
        print(f"Unknown service: {args.service}")
        sys.exit(1)

    adapter_loader = load_adapter(args.service, registry)
    if not adapter_loader:
        print(f"No adapter manifest found for {args.service}")
        sys.exit(1)

    action_spec = adapter_loader.get_action(args.domain, args.action)
    if not action_spec:
        print(f"Action {args.domain}:{args.action} not found for {args.service}")
        available = adapter_loader.list_actions(args.domain)
        if available:
            print(f"Available actions in {args.domain}: {', '.join(available)}")
        sys.exit(1)
    if ExecutionMode.SUITE not in action_spec.mode:
        print(
            f"Action {args.domain}:{args.action} for {args.service} "
            "does not support suite mode"
        )
        sys.exit(1)

    audit = get_audit_logger()
    audit_record = audit.log_start(
        args.service,
        args.domain,
        args.action,
        "suite",
        action_spec.destructive,
    )

    if args.domain == "db" and args.action == "db-reset-schema":
        if args.service != "rule-management":
            summary = "db-reset-schema is reserved for rule-management only"
            print(summary)
            audit.log_complete(audit_record, ActionStatus.FAILED, summary)
            return 1
        if args.schema_reset_ack != SCHEMA_RESET_ACK_TOKEN:
            summary = (
                "High-risk schema reset requires --schema-reset-ack "
                f"{SCHEMA_RESET_ACK_TOKEN}"
            )
            print(summary)
            audit.log_complete(audit_record, ActionStatus.FAILED, summary)
            return 1
        print(
            "WARNING: db-reset-schema is a high-risk action that can impact all services using fraud_gov."
        )

    try:
        require_confirmation(
            args.service,
            args.domain,
            args.action,
            action_spec.destructive,
            yes_flag=args.yes,
            confirm_token=args.confirm,
        )
    except Exception as e:
        summary = f"Confirmation failed: {e}"
        print(summary)
        audit.log_complete(audit_record, ActionStatus.FAILED, summary)
        return 1

    repo_path = registry.get_service_repo_path(args.service)
    if not repo_path:
        summary = f"Could not resolve repo path for {args.service}"
        print(summary)
        audit.log_complete(audit_record, ActionStatus.FAILED, summary)
        return 1

    should_precheck_container = (
        (args.domain == "service" and args.action in {"status", "health"})
        or (args.domain == "runtime" and args.action == "verify")
    )
    if should_precheck_container and not _is_container_running(service.container):
        result = _build_not_running_result(args.service, args.domain, args.action)
    else:
        result = run_action(
            args.service,
            args.domain,
            args.action,
            action_spec,
            repo_path,
        )

    audit.log_complete(audit_record, result.status, result.summary)

    if args.json:
        print(format_action_json(result))
    else:
        print(f"Status: {result.status.value}")
        print(f"Summary: {result.summary}")
        if result.error:
            print(f"Error: {result.error}")
        if result.next_steps:
            print("Next Steps:")
            for step in result.next_steps:
                print(f"  - {step}")

    return 0 if result.status == ActionStatus.OK else 1


def cmd_registry_validate(args) -> int:
    """Validate the service registry."""
    registry = get_registry()
    reg = registry.load()

    print("Service Registry Validation")
    print("=" * 50)

    errors = []
    for service_id, service in reg.services.items():
        adapter_path = registry.get_service_adapter_path(service_id)
        if adapter_path and adapter_path.exists():
            print(f"[OK] {service_id}: adapter found")
        else:
            print(f"[FAIL] {service_id}: adapter NOT found")
            errors.append(service_id)

    if errors:
        print(f"\n{len(errors)} services missing adapters")
        return 1
    else:
        print(f"\nAll {len(reg.services)} services validated")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Card Fraud Platform Control Plane")
    subparsers = parser.add_subparsers(dest="command")

    status_parser = subparsers.add_parser("status", help="Show platform status")
    status_parser.add_argument("--json", action="store_true", help="JSON output")

    inv_parser = subparsers.add_parser("inventory", help="Show platform inventory")
    inv_parser.add_argument(
        "scope",
        nargs="?",
        default="all",
        choices=["all", "services", "infra", "redis", "db", "messaging", "storage", "auth", "secrets"],
        help="Scope: services, infra, redis, db, messaging, storage, auth, secrets, or all",
    )
    inv_parser.add_argument("--json", action="store_true", help="JSON output")

    action_parser = subparsers.add_parser("action", help="Execute a platform action")
    action_parser.add_argument("domain", help="Action domain (e.g., db, auth)")
    action_parser.add_argument("action", help="Action name (e.g., verify, reset-data)")
    action_parser.add_argument("service", help="Target service")
    action_parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation for destructive actions",
    )
    action_parser.add_argument("--confirm", help="Explicit confirmation token")
    action_parser.add_argument(
        "--schema-reset-ack",
        help=f"Required for db-reset-schema. Must be: {SCHEMA_RESET_ACK_TOKEN}",
    )
    action_parser.add_argument("--json", action="store_true", help="JSON output")

    reg_parser = subparsers.add_parser("registry", help="Registry commands")
    reg_subparsers = reg_parser.add_subparsers(dest="registry_command")
    validate_parser = reg_subparsers.add_parser("validate", help="Validate registry")

    args = parser.parse_args()

    if args.command == "status":
        return cmd_status(args)
    elif args.command == "inventory":
        return cmd_inventory(args)
    elif args.command == "action":
        return cmd_action(args)
    elif args.command == "registry":
        if args.registry_command == "validate":
            return cmd_registry_validate(args)
        else:
            reg_parser.print_help()
            return 1
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
