"""Action execution runner."""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .models import ActionResult, ActionSpec, ActionStatus


class ActionRunnerError(Exception):
    """Error executing an action."""

    pass


class ActionRunner:
    """Execute adapter commands with timeout and output parsing."""

    def __init__(self, working_dir: Path):
        self.working_dir = working_dir

    def run(
        self,
        service: str,
        domain: str,
        action: str,
        action_spec: ActionSpec,
        format_json: bool = True,
    ) -> ActionResult:
        """Execute an action and return the result."""
        started_at = datetime.now(timezone.utc)

        command = action_spec.command.copy()
        if format_json:
            if "uv" in command:
                command.append("--format")
                command.append("json")
            elif "--format" not in command:
                command.append("--format")
                command.append("json")

        try:
            result = subprocess.run(
                command,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=action_spec.timeout_seconds,
            )
            completed_at = datetime.now(timezone.utc)

            parsed_output: dict | None = None
            if result.stdout:
                try:
                    parsed_output = json.loads(result.stdout)
                except json.JSONDecodeError:
                    parsed_output = None

            if result.returncode != 0:
                if parsed_output is not None:
                    mapped_status = self._map_output_status(
                        str(parsed_output.get("status", "failed")),
                        default=ActionStatus.FAILED,
                    )
                    details = parsed_output.get("details", [])
                    if not isinstance(details, list):
                        details = [str(details)]
                    return ActionResult(
                        service=service,
                        domain=domain,
                        action=action,
                        target=domain,
                        status=mapped_status,
                        summary=str(
                            parsed_output.get(
                                "summary", f"Command exited with code {result.returncode}"
                            )
                        ),
                        details=[str(item) for item in details],
                        destructive=action_spec.destructive,
                        started_at=started_at,
                        completed_at=completed_at,
                        artifacts=[str(item) for item in parsed_output.get("artifacts", [])],
                        next_steps=[str(item) for item in parsed_output.get("next_steps", [])],
                        error=parsed_output.get("error") or result.stderr,
                    )
                return ActionResult(
                    service=service,
                    domain=domain,
                    action=action,
                    target=domain,
                    status=ActionStatus.FAILED,
                    summary=f"Command exited with code {result.returncode}",
                    details=[result.stderr] if result.stderr else [],
                    destructive=action_spec.destructive,
                    started_at=started_at,
                    completed_at=completed_at,
                    error=result.stderr,
                )

            output = parsed_output if parsed_output is not None else {}
            mapped_status = self._map_output_status(
                str(output.get("status", "ok")),
                default=ActionStatus.OK,
            )
            return ActionResult(
                service=service,
                domain=domain,
                action=action,
                target=domain,
                status=mapped_status,
                summary=output.get("summary", "Action completed"),
                details=output.get("details", []),
                destructive=action_spec.destructive,
                started_at=started_at,
                completed_at=completed_at,
                artifacts=output.get("artifacts", []),
                next_steps=output.get("next_steps", []),
            )

        except subprocess.TimeoutExpired:
            completed_at = datetime.now(timezone.utc)
            return ActionResult(
                service=service,
                domain=domain,
                action=action,
                target=domain,
                status=ActionStatus.TIMEOUT,
                summary=f"Action timed out after {action_spec.timeout_seconds} seconds",
                destructive=action_spec.destructive,
                started_at=started_at,
                completed_at=completed_at,
                error=f"Timeout after {action_spec.timeout_seconds}s",
            )

        except Exception as e:
            completed_at = datetime.now(timezone.utc)
            return ActionResult(
                service=service,
                domain=domain,
                action=action,
                target=domain,
                status=ActionStatus.RUNTIME_FAILED,
                summary=f"Action failed: {str(e)}",
                destructive=action_spec.destructive,
                started_at=started_at,
                completed_at=completed_at,
                error=str(e),
            )

    def _map_output_status(
        self, raw_status: str, *, default: ActionStatus
    ) -> ActionStatus:
        normalized = raw_status.strip().lower()
        if normalized in {"ok", "success"}:
            return ActionStatus.OK
        if normalized in {"timeout"}:
            return ActionStatus.TIMEOUT
        if normalized in {"invalid_output"}:
            return ActionStatus.INVALID_OUTPUT
        if normalized in {"runtime_failed"}:
            return ActionStatus.RUNTIME_FAILED
        if normalized in {"cancelled"}:
            return ActionStatus.CANCELLED
        if normalized in {"warn", "warning", "partial", "skipped"}:
            return ActionStatus.OK
        if normalized in {"failed", "error"}:
            return ActionStatus.FAILED
        return default


def run_action(
    service: str,
    domain: str,
    action: str,
    action_spec: ActionSpec,
    working_dir: Path,
    format_json: bool = True,
) -> ActionResult:
    """Convenience function to run an action."""
    runner = ActionRunner(working_dir)
    return runner.run(service, domain, action, action_spec, format_json=format_json)
