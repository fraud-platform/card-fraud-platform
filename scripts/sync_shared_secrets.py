"""
Sync shared local-development secrets across Card Fraud projects.

This keeps the platform infra credentials and service DATABASE_URL values aligned,
which prevents local auth mismatches against PostgreSQL.
"""

from __future__ import annotations

import argparse
import secrets
import subprocess
import sys

DB_KEYS = [
    "POSTGRES_ADMIN_PASSWORD",
    "FRAUD_GOV_APP_PASSWORD",
]

INFRA_KEYS = [
    "MINIO_ROOT_USER",
    "MINIO_ROOT_PASSWORD",
    "S3_ACCESS_KEY_ID",
    "S3_SECRET_ACCESS_KEY",
    "S3_BUCKET_NAME",
    "S3_REGION",
]

TARGET_PROJECTS = [
    "card-fraud-platform",
    "card-fraud-rule-management",
    "card-fraud-transaction-management",
]
METRICS_TARGET_PROJECTS = [
    *TARGET_PROJECTS,
    "card-fraud-ops-analyst-agent",
]
PLATFORM_PROJECT = "card-fraud-platform"
MCP_GATEWAY_PROJECT = "card-fraud-mcp-gateway"
MCP_READER_KEYS = [
    "FRAUD_GOV_MCP_READER_PASSWORD",
    "FRAUD_GOV_MCP_S3_ACCESS_KEY",
    "FRAUD_GOV_MCP_S3_SECRET_KEY",
]
AUTH0_MANAGEMENT_KEYS = [
    "AUTH0_MGMT_DOMAIN",
    "AUTH0_MGMT_CLIENT_ID",
    "AUTH0_MGMT_CLIENT_SECRET",
]


def _run(cmd: list[str], *, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=True,
        text=True,
        capture_output=capture_output,
    )


def _get_secret(project: str, config: str, name: str) -> str:
    result = _run(
        [
            "doppler",
            "secrets",
            "get",
            name,
            "--project",
            project,
            "--config",
            config,
            "--plain",
        ],
        capture_output=True,
    )
    return result.stdout.strip()


def _try_get_secret(project: str, config: str, name: str) -> str | None:
    try:
        value = _get_secret(project, config, name)
    except subprocess.CalledProcessError:
        return None
    return value or None


def _set_secrets(project: str, config: str, secrets: dict[str, str]) -> None:
    args = [
        "doppler",
        "secrets",
        "set",
        "--project",
        project,
        "--config",
        config,
        "--silent",
    ]
    args.extend([f"{k}={v}" for k, v in secrets.items()])
    _run(args)


def _ensure_mcp_reader_secrets(config: str) -> dict[str, str]:
    """Return platform-owned MCP reader credentials, creating missing local values."""
    values = {
        key: _try_get_secret(PLATFORM_PROJECT, config, key) or "" for key in MCP_READER_KEYS
    }
    if not values["FRAUD_GOV_MCP_READER_PASSWORD"]:
        values["FRAUD_GOV_MCP_READER_PASSWORD"] = secrets.token_urlsafe(32)
    if not values["FRAUD_GOV_MCP_S3_ACCESS_KEY"]:
        values["FRAUD_GOV_MCP_S3_ACCESS_KEY"] = "mcp-reader-local"
    if not values["FRAUD_GOV_MCP_S3_SECRET_KEY"]:
        values["FRAUD_GOV_MCP_S3_SECRET_KEY"] = secrets.token_urlsafe(32)
    _set_secrets(PLATFORM_PROJECT, config, values)
    return values


def _ensure_metrics_token(config: str) -> str:
    """Return the platform-owned local scrape token, creating it if absent."""
    token = _try_get_secret(PLATFORM_PROJECT, config, "METRICS_TOKEN")
    if not token:
        token = secrets.token_urlsafe(32)
        _set_secrets(PLATFORM_PROJECT, config, {"METRICS_TOKEN": token})
    return token


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync shared local secrets across platform, rule-management, and transaction-management."
    )
    parser.add_argument(
        "--source-project",
        default="card-fraud-rule-management",
        help="Doppler project to use as the source of truth (default: card-fraud-rule-management).",
    )
    parser.add_argument(
        "--config",
        default="local",
        help="Doppler config to sync (default: local).",
    )
    args = parser.parse_args()

    if args.config != "local":
        print(
            "[ERROR] This sync command is intentionally restricted to --config local "
            "to avoid accidental non-local secret rewrites."
        )
        return 1

    print(f"Syncing shared secrets from '{args.source_project}' ({args.config})...")
    shared: dict[str, str] = {}

    # Always take DB passwords from the selected source project.
    for key in DB_KEYS:
        shared[key] = _get_secret(args.source_project, args.config, key)

    # FRAUD_GOV_ANALYTICS_PASSWORD may not exist in every service project.
    analytics_password = _try_get_secret(
        args.source_project, args.config, "FRAUD_GOV_ANALYTICS_PASSWORD"
    )
    if not analytics_password:
        analytics_password = _try_get_secret(
            PLATFORM_PROJECT, args.config, "FRAUD_GOV_ANALYTICS_PASSWORD"
        )
    if not analytics_password:
        analytics_password = shared["FRAUD_GOV_APP_PASSWORD"]
    shared["FRAUD_GOV_ANALYTICS_PASSWORD"] = analytics_password

    # Keep infra/object-storage keys sourced from platform project.
    for key in INFRA_KEYS:
        shared[key] = _get_secret(PLATFORM_PROJECT, args.config, key)

    mcp_reader = _ensure_mcp_reader_secrets(args.config)
    metrics_token = _ensure_metrics_token(args.config)

    for project in METRICS_TARGET_PROJECTS:
        _set_secrets(project, args.config, {"METRICS_TOKEN": metrics_token})
        print(f"  [OK] Synced metrics scrape token to {project}")

    for project in TARGET_PROJECTS:
        _set_secrets(project, args.config, shared)
        print(f"  [OK] Synced shared keys to {project}")

    app_pwd = shared["FRAUD_GOV_APP_PASSWORD"]
    admin_pwd = shared["POSTGRES_ADMIN_PASSWORD"]
    app_db_url = f"postgresql://fraud_gov_app_user:{app_pwd}@localhost:5432/fraud_gov"
    admin_db_url = f"postgresql://postgres:{admin_pwd}@localhost:5432/fraud_gov"

    for project in ("card-fraud-rule-management", "card-fraud-transaction-management"):
        _set_secrets(
            project,
            args.config,
            {
                "DATABASE_URL_APP": app_db_url,
                "DATABASE_URL_ADMIN": admin_db_url,
            },
        )
        print(f"  [OK] Updated DATABASE_URL_* in {project}")

    auth0_management = {
        key: _get_secret(args.source_project, args.config, key) for key in AUTH0_MANAGEMENT_KEYS
    }
    auth0_domain = _get_secret(args.source_project, args.config, "AUTH0_DOMAIN")
    bucket = shared["S3_BUCKET_NAME"]
    mcp_password = mcp_reader["FRAUD_GOV_MCP_READER_PASSWORD"]
    _set_secrets(
        MCP_GATEWAY_PROJECT,
        args.config,
        {
            **auth0_management,
            **mcp_reader,
            "APP_ENV": "local",
            "SECURITY_SKIP_JWT_VALIDATION": "true",
            "GATEWAY_AUTH0_DOMAIN": auth0_domain,
            "GATEWAY_AUTH0_AUDIENCE": "https://card-fraud-mcp-gateway",
            "GATEWAY_PG_DSN": (
                "postgresql://fraud_gov_mcp_reader:"
                f"{mcp_password}@localhost:5432/fraud_gov"
            ),
            "GATEWAY_PG_ALLOWED_SCHEMAS": "fraud_gov,public",
            "GATEWAY_PG_ALLOWED_TABLES": (
                "transactions,transaction_rule_matches,transaction_reviews,analyst_notes,"
                "transaction_cases,case_activity_log,rule_fields,rule_field_versions,"
                "rule_field_metadata,rules,rule_versions,ruleset_manifest,"
                "field_registry_manifest,rulesets,ruleset_versions,"
                "ruleset_version_rules,approvals"
            ),
            "GATEWAY_REDIS_URL": "redis://localhost:6379",
            "GATEWAY_REDIS_ALLOWED_PREFIXES": "fraud:,session:,rate:",
            "GATEWAY_KAFKA_BROKERS": "localhost:9092",
            "GATEWAY_KAFKA_ALLOWED_TOPICS": (
                "fraud.transactions,fraud.decisions,fraud.alerts,"
                "fraud.card.decisions.v1,test.fraud.decisions.v1"
            ),
            "GATEWAY_KAFKA_ALLOWED_GROUPS": "fraud-engine,card-fraud-engine",
            "GATEWAY_S3_ENDPOINT": "http://localhost:9000",
            "GATEWAY_S3_ACCESS_KEY": mcp_reader["FRAUD_GOV_MCP_S3_ACCESS_KEY"],
            "GATEWAY_S3_SECRET_KEY": mcp_reader["FRAUD_GOV_MCP_S3_SECRET_KEY"],
            "GATEWAY_S3_REGION": shared["S3_REGION"],
            "GATEWAY_S3_ALLOWED_BUCKETS": bucket,
            "GATEWAY_S3_ALLOWED_PREFIXES": f"{bucket}/",
            "GATEWAY_ENFORCE_ALLOWLISTS": "true",
        },
    )
    print(f"  [OK] Synced least-privilege runtime and Auth0 bootstrap keys to {MCP_GATEWAY_PROJECT}")

    print()
    print("Done. Shared local secrets are now aligned across projects.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
