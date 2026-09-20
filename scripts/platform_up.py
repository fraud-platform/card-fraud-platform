"""
Start the full Card Fraud platform stack as a single compose project.

Usage:
    doppler run -- uv run platform-up
    doppler run -- uv run platform-up -- --load-testing
    doppler run -- uv run platform-up -- --build
    doppler run -- uv run platform-up -- --force-recreate
    doppler run -- uv run platform-up -- --build --service ops-analyst-agent

All environment variables (secrets, config) are injected by Doppler.
Run `doppler setup` once in this directory to configure.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

from scripts.constants import (
    APPS_COMPOSE_FILE,
    COMPOSE_FILE,
    COMPOSE_PROJECT,
    CONFLICT_PRONE_CONTAINERS,
    JFR_OVERRIDE_COMPOSE_FILE,
    PLATFORM_PROFILE,
)

OPS_AGENT_DOPPLER_PROJECT = "card-fraud-ops-analyst-agent"
OPS_AGENT_DOPPLER_CONFIG = "local"

# Keep this list deliberately narrow.  Platform-owned runtime/auth/database
# values continue to come from the outer `doppler run` invocation.
OPS_AGENT_ENV_ALLOWLIST = frozenset(
    {
        "OPS_AGENT_ENABLE_LLM_REASONING",
        "LLM_PROVIDER",
        "LLM_BASE_URL",
        "LLM_API_KEY",
        "LLM_TIMEOUT",
        "LLM_MAX_RETRIES",
        "LLM_PROMPT_GUARD_ENABLED",
        "LLM_MAX_PROMPT_TOKENS",
        "LLM_MAX_COMPLETION_TOKENS",
        "LLM_CONSISTENCY_THRESHOLD",
        "LLM_STAGE_TIMEOUT_SECONDS",
        "LLM_ROUTINE_MODEL",
        "LLM_ESCALATION_MODEL",
        "LLM_REASONING_EFFORT",
        "PLANNER_MODEL_NAME",
        "PLANNER_LLM_ENABLED",
        "PLANNER_TEMPERATURE",
        "PLANNER_MAX_TOKENS",
        "PLANNER_TIMEOUT_SECONDS",
        "PLANNER_EVIDENCE_SELECTION_ENABLED",
        "LANGGRAPH_INVESTIGATION_TIMEOUT_SECONDS",
        "LANGGRAPH_TOOL_TIMEOUT_SECONDS",
        "LANGGRAPH_PLANNER_TIMEOUT_SECONDS",
        "VECTOR_ENABLED",
        "VECTOR_API_BASE",
        "VECTOR_API_KEY",
        "VECTOR_MODEL_NAME",
        "VECTOR_DIMENSION",
        "VECTOR_SEARCH_LIMIT",
        "VECTOR_TIME_WINDOW_DAYS",
        "VECTOR_MIN_SIMILARITY",
        "VECTOR_REQUEST_TIMEOUT_S",
        "VECTOR_RETRY_ATTEMPTS",
        "VECTOR_RETRY_BACKOFF_SECONDS",
    }
)

OPS_AGENT_REQUIRED_ENV_KEYS = frozenset(
    {
        "OPS_AGENT_ENABLE_LLM_REASONING",
        "LLM_PROVIDER",
        "LLM_BASE_URL",
        "LLM_API_KEY",
        "PLANNER_MODEL_NAME",
        "PLANNER_LLM_ENABLED",
        "PLANNER_EVIDENCE_SELECTION_ENABLED",
        "VECTOR_ENABLED",
        "VECTOR_API_BASE",
        "VECTOR_MODEL_NAME",
        "VECTOR_DIMENSION",
    }
)


def _check_docker_version() -> bool:
    """Verify Docker Compose v2 is available."""
    try:
        result = subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            print("[ERROR] Docker Compose v2 is required but not found.")
            print()
            print(
                "This platform uses 'docker compose' (v2 syntax), not 'docker-compose'."
            )
            print(
                "Update Docker Desktop to the latest version or install Docker Compose v2."
            )
            return False

        if "Docker Compose version" not in result.stdout:
            print("[WARN] Unable to verify Docker Compose version format.")
            print(f"  Output: {result.stdout.strip()}")

        return True
    except FileNotFoundError:
        print("[ERROR] Docker is not installed or not in PATH.")
        print()
        print("Please install Docker Desktop:")
        print("  https://www.docker.com/products/docker-desktop")
        return False


def _container_exists(name: str) -> bool:
    """Check whether a container exists."""
    result = subprocess.run(
        ["docker", "inspect", name],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def _container_compose_project(name: str) -> str:
    """Get docker compose project label for a container (if any)."""
    result = subprocess.run(
        [
            "docker",
            "inspect",
            "--format",
            '{{ index .Config.Labels "com.docker.compose.project" }}',
            name,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return (result.stdout or "").strip()


def _cleanup_conflicting_containers() -> None:
    """
    Remove stale containers with expected names but from another compose project.

    This prevents "container name already in use" errors when old local containers
    were created outside this compose project.
    """
    for name in CONFLICT_PRONE_CONTAINERS:
        if not _container_exists(name):
            continue

        project = _container_compose_project(name)
        if project and project == COMPOSE_PROJECT:
            continue

        print(
            f"[WARN] Found conflicting container '{name}' "
            f"(compose project: '{project or 'unknown'}'). Removing..."
        )
        result = subprocess.run(["docker", "rm", "-f", name], check=False)
        if result.returncode != 0:
            print(f"[WARN] Failed to remove container '{name}'")
        else:
            print(f"[OK] Removed conflicting container '{name}'")


def _check_doppler_env() -> bool:
    """Check if required Doppler env vars are present."""
    required = [
        "POSTGRES_ADMIN_PASSWORD",
        "FRAUD_GOV_APP_PASSWORD",
        "MINIO_ROOT_USER",
        "MINIO_ROOT_PASSWORD",
        "S3_BUCKET_NAME",
    ]
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        print("[ERROR] Missing required environment variables:")
        for name in missing:
            print(f"  - {name}")
        print()
        print("Run with Doppler to inject secrets:")
        print("  doppler run -- uv run platform-up")
        print()
        print("Or run `doppler setup` first if not configured.")
        return False
    return True


def _load_ops_agent_env_overlay() -> dict[str, str] | None:
    """Load the ops-agent-owned runtime config without exposing secret values."""
    try:
        result = subprocess.run(
            [
                "doppler",
                "secrets",
                "download",
                "--project",
                OPS_AGENT_DOPPLER_PROJECT,
                "--config",
                OPS_AGENT_DOPPLER_CONFIG,
                "--no-file",
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        print("[ERROR] Doppler CLI is required to load the ops-agent config.")
        return None
    if result.returncode != 0:
        print(
            "[ERROR] Unable to load the ops-agent Doppler overlay "
            f"({OPS_AGENT_DOPPLER_PROJECT}/{OPS_AGENT_DOPPLER_CONFIG})."
        )
        print("  Ensure Doppler is installed and you can read the local config.")
        return None

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("[ERROR] Ops-agent Doppler overlay was not valid JSON.")
        return None

    if not isinstance(payload, dict):
        print("[ERROR] Ops-agent Doppler overlay must be a JSON object.")
        return None

    overlay = {
        name: value
        for name, value in payload.items()
        if name in OPS_AGENT_ENV_ALLOWLIST and isinstance(value, str) and value
    }
    missing = sorted(OPS_AGENT_REQUIRED_ENV_KEYS - overlay.keys())
    if missing:
        print("[ERROR] Ops-agent Doppler config is missing required keys:")
        for name in missing:
            print(f"  - {name}")
        print(
            f"  Project/config: {OPS_AGENT_DOPPLER_PROJECT}/{OPS_AGENT_DOPPLER_CONFIG}"
        )
        print("  Secret values are not displayed.")
        return None

    return overlay


def _compose_up_command() -> list[str]:
    """Build docker compose command for full platform stack startup."""
    cmd = ["docker", "compose", "-f", COMPOSE_FILE, "-f", APPS_COMPOSE_FILE]

    if "--jfr" in sys.argv:
        cmd += ["-f", JFR_OVERRIDE_COMPOSE_FILE]

    cmd += ["-p", COMPOSE_PROJECT, "--profile", PLATFORM_PROFILE]

    if "--load-testing" in sys.argv:
        cmd += ["--profile", "load-testing"]

    cmd += ["up", "-d"]

    if "--build" in sys.argv:
        cmd.append("--build")
    if "--force-recreate" in sys.argv:
        cmd.append("--force-recreate")

    if "--service" in sys.argv:
        service_index = sys.argv.index("--service") + 1
        if service_index >= len(sys.argv) or sys.argv[service_index].startswith("--"):
            raise ValueError("--service requires a Compose service name")
        cmd.append(sys.argv[service_index])

    return cmd


def main() -> int:
    """Start the full platform stack (infra + apps) as one group."""
    print("Card Fraud Platform - Starting full platform stack (infra + apps)...")
    print()

    if "--apps" in sys.argv:
        print("[WARN] '--apps' is deprecated. Apps are started by default now.")
        print()

    if "--load-testing" in sys.argv:
        print("[INFO] '--load-testing' enabled; Locust profile will also be started.")
        print()

    if not _check_docker_version():
        return 1

    if not _check_doppler_env():
        return 1

    ops_agent_env = _load_ops_agent_env_overlay()
    if ops_agent_env is None:
        return 1

    _cleanup_conflicting_containers()

    try:
        cmd = _compose_up_command()
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        return 1
    print(f"  > {' '.join(cmd)}")
    compose_env = os.environ.copy()
    compose_env.update(ops_agent_env)
    result = subprocess.run(cmd, env=compose_env, check=False)

    if result.returncode != 0:
        print()
        print("[ERROR] Failed to start platform stack.")
        return result.returncode

    print()
    print("Platform stack started.")
    print("Use 'uv run platform-status' to verify container health.")
    print("Use '--load-testing' when you want to include the Locust profile.")
    print()
    print("For targeted restarts (still same platform group):")
    print("  doppler run -- uv run platform-up -- --build --service <service>")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
