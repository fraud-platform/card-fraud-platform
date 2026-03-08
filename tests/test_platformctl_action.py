from __future__ import annotations

import types
import unittest
from unittest.mock import MagicMock, patch

from scripts import platformctl
from scripts.control_plane.models import ActionResult, ActionSpec, ActionStatus, ExecutionMode


def _args(domain: str, action: str, service: str) -> types.SimpleNamespace:
    return types.SimpleNamespace(
        domain=domain,
        action=action,
        service=service,
        yes=True,
        confirm=f"{service}:{domain}:{action}",
        schema_reset_ack=None,
        json=True,
    )


class PlatformCtlActionTests(unittest.TestCase):
    def test_cmd_action_returns_zero_on_ok(self) -> None:
        service_entry = types.SimpleNamespace(container="card-fraud-rule-management")
        registry = MagicMock()
        registry.get.return_value = service_entry
        registry.get_service_repo_path.return_value = "."

        loader = MagicMock()
        loader.get_action.return_value = ActionSpec(
            command=["uv", "run", "platform-adapter", "service", "logs"],
            destructive=False,
            timeout_seconds=60,
            mode=[ExecutionMode.SUITE],
        )

        action_result = ActionResult(
            service="rule-management",
            domain="service",
            action="logs",
            target="service",
            status=ActionStatus.OK,
            summary="ok",
        )

        audit = MagicMock()
        audit.log_start.return_value = MagicMock()

        with patch("scripts.platformctl.get_registry", return_value=registry):
            with patch("scripts.platformctl.load_adapter", return_value=loader):
                with patch("scripts.platformctl.require_confirmation"):
                    with patch("scripts.platformctl._is_container_running", return_value=True):
                        with patch("scripts.platformctl.run_action", return_value=action_result):
                            with patch("scripts.platformctl.get_audit_logger", return_value=audit):
                                with patch("builtins.print"):
                                    code = platformctl.cmd_action(_args("service", "logs", "rule-management"))
        self.assertEqual(code, 0)

    def test_cmd_action_returns_non_zero_on_failed(self) -> None:
        service_entry = types.SimpleNamespace(container="card-fraud-rule-management")
        registry = MagicMock()
        registry.get.return_value = service_entry
        registry.get_service_repo_path.return_value = "."

        loader = MagicMock()
        loader.get_action.return_value = ActionSpec(
            command=["uv", "run", "platform-adapter", "runtime", "verify"],
            destructive=False,
            timeout_seconds=60,
            mode=[ExecutionMode.SUITE],
        )

        action_result = ActionResult(
            service="rule-management",
            domain="runtime",
            action="verify",
            target="service",
            status=ActionStatus.FAILED,
            summary="failed",
        )

        audit = MagicMock()
        audit.log_start.return_value = MagicMock()

        with patch("scripts.platformctl.get_registry", return_value=registry):
            with patch("scripts.platformctl.load_adapter", return_value=loader):
                with patch("scripts.platformctl.require_confirmation"):
                    with patch("scripts.platformctl._is_container_running", return_value=True):
                        with patch("scripts.platformctl.run_action", return_value=action_result):
                            with patch("scripts.platformctl.get_audit_logger", return_value=audit):
                                with patch("builtins.print"):
                                    code = platformctl.cmd_action(_args("runtime", "verify", "rule-management"))
        self.assertEqual(code, 1)

    def test_cmd_action_precheck_blocks_when_container_not_running(self) -> None:
        service_entry = types.SimpleNamespace(container="card-fraud-rule-management")
        registry = MagicMock()
        registry.get.return_value = service_entry
        registry.get_service_repo_path.return_value = "."

        loader = MagicMock()
        loader.get_action.return_value = ActionSpec(
            command=["uv", "run", "platform-adapter", "service", "health"],
            destructive=False,
            timeout_seconds=60,
            mode=[ExecutionMode.SUITE],
        )

        audit = MagicMock()
        audit.log_start.return_value = MagicMock()

        with patch("scripts.platformctl.get_registry", return_value=registry):
            with patch("scripts.platformctl.load_adapter", return_value=loader):
                with patch("scripts.platformctl.require_confirmation"):
                    with patch("scripts.platformctl._is_container_running", return_value=False):
                        with patch("scripts.platformctl.run_action") as run_action_mock:
                            with patch("scripts.platformctl.get_audit_logger", return_value=audit):
                                with patch("builtins.print"):
                                    code = platformctl.cmd_action(_args("service", "health", "rule-management"))
        self.assertEqual(code, 1)
        run_action_mock.assert_not_called()

    def test_cmd_action_schema_reset_requires_second_ack(self) -> None:
        service_entry = types.SimpleNamespace(container="card-fraud-rule-management")
        registry = MagicMock()
        registry.get.return_value = service_entry
        registry.get_service_repo_path.return_value = "."

        loader = MagicMock()
        loader.get_action.return_value = ActionSpec(
            command=["uv", "run", "platform-adapter", "db", "db-reset-schema"],
            destructive=True,
            timeout_seconds=60,
            mode=[ExecutionMode.SUITE],
        )

        audit = MagicMock()
        audit.log_start.return_value = MagicMock()

        args = _args("db", "db-reset-schema", "rule-management")
        args.schema_reset_ack = None

        with patch("scripts.platformctl.get_registry", return_value=registry):
            with patch("scripts.platformctl.load_adapter", return_value=loader):
                with patch("scripts.platformctl.require_confirmation"):
                    with patch("scripts.platformctl.get_audit_logger", return_value=audit):
                        with patch("scripts.platformctl.run_action") as run_action_mock:
                            with patch("builtins.print"):
                                code = platformctl.cmd_action(args)
        self.assertEqual(code, 1)
        run_action_mock.assert_not_called()
        audit.log_complete.assert_called_once()
        denied_outcome = audit.log_complete.call_args.args[1]
        self.assertEqual(denied_outcome, ActionStatus.FAILED)

    def test_cmd_action_confirmation_denial_is_audited(self) -> None:
        service_entry = types.SimpleNamespace(container="card-fraud-rule-management")
        registry = MagicMock()
        registry.get.return_value = service_entry
        registry.get_service_repo_path.return_value = "."

        loader = MagicMock()
        loader.get_action.return_value = ActionSpec(
            command=["uv", "run", "platform-adapter", "db", "db-reset-data"],
            destructive=True,
            timeout_seconds=60,
            mode=[ExecutionMode.SUITE],
        )

        audit = MagicMock()
        audit.log_start.return_value = MagicMock()

        args = _args("db", "db-reset-data", "rule-management")

        with patch("scripts.platformctl.get_registry", return_value=registry):
            with patch("scripts.platformctl.load_adapter", return_value=loader):
                with patch(
                    "scripts.platformctl.require_confirmation",
                    side_effect=RuntimeError("confirmation token mismatch"),
                ):
                    with patch("scripts.platformctl.get_audit_logger", return_value=audit):
                        with patch("builtins.print"):
                            code = platformctl.cmd_action(args)

        self.assertEqual(code, 1)
        audit.log_complete.assert_called_once()
        denied_outcome = audit.log_complete.call_args.args[1]
        self.assertEqual(denied_outcome, ActionStatus.FAILED)


if __name__ == "__main__":
    unittest.main()
