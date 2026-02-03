"""
Sync shared local-development secrets across Card Fraud projects.

This keeps the platform infra credentials and service DATABASE_URL values aligned,
which prevents local auth mismatches against PostgreSQL.
"""

from __future__ import annotations

import argparse
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
PLATFORM_PROJECT = "card-fraud-platform"


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

    print()
    print("Done. Shared local secrets are now aligned across projects.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
