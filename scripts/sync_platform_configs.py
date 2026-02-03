"""
Sync card-fraud-platform Doppler configs from a source config.

This is a local-development helper to keep compose-required secrets aligned
across Doppler configs (for example local -> test/prod) while setting APP_ENV
per target config.
"""

from __future__ import annotations

import argparse
import subprocess
import sys

SYNC_KEYS = [
    "POSTGRES_ADMIN_PASSWORD",
    "FRAUD_GOV_APP_PASSWORD",
    "FRAUD_GOV_ANALYTICS_PASSWORD",
    "MINIO_ROOT_USER",
    "MINIO_ROOT_PASSWORD",
    "S3_ACCESS_KEY_ID",
    "S3_SECRET_ACCESS_KEY",
    "S3_BUCKET_NAME",
    "S3_REGION",
    "AUTH0_DOMAIN",
    "RULE_ENGINE_AUTH0_AUDIENCE",
    "RULE_ENGINE_AUTH0_CLIENT_ID",
    "RULE_ENGINE_AUTH0_CLIENT_SECRET",
    "RULE_MGMT_AUTH0_AUDIENCE",
    "TXN_MGMT_AUTH0_AUDIENCE",
    "VITE_API_URL",
    "VITE_AUTH0_DOMAIN",
    "VITE_AUTH0_CLIENT_ID",
    "VITE_AUTH0_AUDIENCE",
    "VITE_DISABLE_MOCKS",
    "VITE_E2E_MODE",
    "VITE_SENTRY_ENVIRONMENT",
    "VITE_SENTRY_RELEASE",
]


def _run(cmd: list[str], *, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=True,
        text=True,
        capture_output=capture_output,
    )


def _get_secret(project: str, config: str, key: str) -> str:
    result = _run(
        [
            "doppler",
            "secrets",
            "get",
            key,
            "--project",
            project,
            "--config",
            config,
            "--plain",
        ],
        capture_output=True,
    )
    return result.stdout.strip()


def _try_get_secret(project: str, config: str, key: str) -> str | None:
    try:
        value = _get_secret(project, config, key)
    except subprocess.CalledProcessError:
        return None
    return value or None


def _set_secrets(project: str, config: str, secrets: dict[str, str]) -> None:
    cmd = [
        "doppler",
        "secrets",
        "set",
        "--project",
        project,
        "--config",
        config,
        "--silent",
    ]
    cmd.extend([f"{k}={v}" for k, v in secrets.items()])
    _run(cmd)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync card-fraud-platform Doppler configs from source config values."
    )
    parser.add_argument(
        "--project",
        default="card-fraud-platform",
        help="Doppler project name (default: card-fraud-platform).",
    )
    parser.add_argument(
        "--source-config",
        default="local",
        help="Source config to copy values from (default: local).",
    )
    parser.add_argument(
        "--target-configs",
        nargs="+",
        default=["test", "prod"],
        help="Target configs to sync (default: test prod).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show intended updates without changing Doppler.",
    )
    args = parser.parse_args()

    source_values: dict[str, str] = {}
    missing: list[str] = []
    for key in SYNC_KEYS:
        value = _try_get_secret(args.project, args.source_config, key)
        if value is None:
            missing.append(key)
            continue
        source_values[key] = value

    if missing:
        print("[WARN] Missing keys in source config (skipping):")
        for key in missing:
            print(f"  - {key}")

    if not source_values:
        print("[ERROR] No source secrets found to sync.")
        return 1

    print(
        f"Syncing {len(source_values)} keys from "
        f"{args.project}/{args.source_config} -> {', '.join(args.target_configs)}"
    )
    if args.dry_run:
        print("[DRY RUN] No Doppler changes were applied.")
        return 0

    for target in args.target_configs:
        payload = dict(source_values)
        payload["APP_ENV"] = target
        payload["VITE_SENTRY_ENVIRONMENT"] = target
        _set_secrets(args.project, target, payload)
        print(f"  [OK] Synced {len(payload)} keys to {args.project}/{target}")

    local_payload = {"APP_ENV": "local", "VITE_SENTRY_ENVIRONMENT": "local"}
    _set_secrets(args.project, "local", local_payload)
    print(f"  [OK] Ensured APP_ENV/VITE_SENTRY_ENVIRONMENT in {args.project}/local")
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
