from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts import (
    constants,
    platform_check,
    platform_down,
    platform_status,
    platform_up,
)


class ConstantsTests(unittest.TestCase):
    def test_compose_files_exist(self) -> None:
        self.assertTrue(Path(constants.COMPOSE_FILE).exists())
        self.assertTrue(Path(constants.APPS_COMPOSE_FILE).exists())

    def test_all_container_names_are_unique(self) -> None:
        names = [
            name for group in constants.ALL_CONTAINERS.values() for name, _, _ in group
        ]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(sorted(names), sorted(constants.CONFLICT_PRONE_CONTAINERS))


class PlatformUpTests(unittest.TestCase):
    def test_compose_up_command_defaults(self) -> None:
        with patch("sys.argv", ["platform-up"]):
            cmd = platform_up._compose_up_command()
        self.assertEqual(
            cmd,
            [
                "docker",
                "compose",
                "-f",
                constants.COMPOSE_FILE,
                "-f",
                constants.APPS_COMPOSE_FILE,
                "-p",
                constants.COMPOSE_PROJECT,
                "--profile",
                constants.PLATFORM_PROFILE,
                "up",
                "-d",
            ],
        )

    def test_compose_up_command_with_optional_flags(self) -> None:
        with patch(
            "sys.argv",
            ["platform-up", "--load-testing", "--build", "--force-recreate", "--jfr"],
        ):
            cmd = platform_up._compose_up_command()
        self.assertEqual(
            cmd,
            [
                "docker",
                "compose",
                "-f",
                constants.COMPOSE_FILE,
                "-f",
                constants.APPS_COMPOSE_FILE,
                "-f",
                constants.JFR_OVERRIDE_COMPOSE_FILE,
                "-p",
                constants.COMPOSE_PROJECT,
                "--profile",
                constants.PLATFORM_PROFILE,
                "--profile",
                "load-testing",
                "up",
                "-d",
                "--build",
                "--force-recreate",
            ],
        )

    def test_compose_up_command_with_target_service(self) -> None:
        with patch(
            "sys.argv",
            ["platform-up", "--build", "--service", "ops-analyst-agent"],
        ):
            cmd = platform_up._compose_up_command()
        self.assertEqual(cmd[-2:], ["--build", "ops-analyst-agent"])

    def test_compose_up_command_requires_target_service_name(self) -> None:
        with patch("sys.argv", ["platform-up", "--service"]):
            with self.assertRaisesRegex(ValueError, "requires a Compose service name"):
                platform_up._compose_up_command()

    def test_check_doppler_env_requires_expected_keys(self) -> None:
        with patch("builtins.print"):
            with patch.dict("os.environ", {}, clear=True):
                self.assertFalse(platform_up._check_doppler_env())

            with patch.dict(
                "os.environ",
                {
                    "POSTGRES_ADMIN_PASSWORD": "x",
                    "FRAUD_GOV_APP_PASSWORD": "x",
                    "MINIO_ROOT_USER": "x",
                    "MINIO_ROOT_PASSWORD": "x",
                    "S3_BUCKET_NAME": "x",
                },
                clear=True,
            ):
                self.assertTrue(platform_up._check_doppler_env())

    @patch("scripts.platform_up.subprocess.run")
    def test_ops_agent_overlay_filters_unknown_keys(self, mock_run: MagicMock) -> None:
        values = {
            name: f"value-{name}" for name in platform_up.OPS_AGENT_REQUIRED_ENV_KEYS
        }
        values["LLM_MAX_RETRIES"] = "2"
        values["VECTOR_SEARCH_LIMIT"] = "20"
        values["UNRELATED_PLATFORM_SECRET"] = "must-not-be-forwarded"
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=json.dumps(values), stderr=""
        )

        overlay = platform_up._load_ops_agent_env_overlay()

        self.assertIsNotNone(overlay)
        assert overlay is not None
        self.assertEqual(
            set(overlay),
            platform_up.OPS_AGENT_REQUIRED_ENV_KEYS
            | {"LLM_MAX_RETRIES", "VECTOR_SEARCH_LIMIT"},
        )
        self.assertNotIn("UNRELATED_PLATFORM_SECRET", overlay)

    @patch("scripts.platform_up.subprocess.run")
    def test_ops_agent_overlay_reports_missing_keys_without_secret_values(
        self, mock_run: MagicMock
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps({"LLM_PROVIDER": "openai/gpt-5-mini"}),
            stderr="",
        )

        with patch("builtins.print") as mock_print:
            overlay = platform_up._load_ops_agent_env_overlay()

        self.assertIsNone(overlay)
        rendered = " ".join(str(call.args[0]) for call in mock_print.call_args_list)
        self.assertNotIn("secret-value", rendered)
        self.assertIn("LLM_API_KEY", rendered)

    @patch("scripts.platform_up._cleanup_conflicting_containers")
    @patch(
        "scripts.platform_up._compose_up_command", return_value=["docker", "compose"]
    )
    @patch("scripts.platform_up._load_ops_agent_env_overlay")
    @patch("scripts.platform_up._check_doppler_env", return_value=True)
    @patch("scripts.platform_up._check_docker_version", return_value=True)
    @patch("scripts.platform_up.subprocess.run")
    def test_main_passes_overlay_only_to_compose_subprocess(
        self,
        mock_run: MagicMock,
        _mock_docker: MagicMock,
        _mock_doppler: MagicMock,
        mock_overlay: MagicMock,
        _mock_command: MagicMock,
        _mock_cleanup: MagicMock,
    ) -> None:
        mock_overlay.return_value = {
            "LLM_PROVIDER": "openai/gpt-5-mini",
            "LLM_API_KEY": "secret-value",
        }
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )

        with patch.dict("os.environ", {"PLATFORM_ONLY": "platform-value"}, clear=True):
            self.assertEqual(platform_up.main(), 0)

        compose_env = mock_run.call_args.kwargs["env"]
        self.assertEqual(compose_env["PLATFORM_ONLY"], "platform-value")
        self.assertEqual(compose_env["LLM_PROVIDER"], "openai/gpt-5-mini")
        self.assertEqual(compose_env["LLM_API_KEY"], "secret-value")


class PlatformDownTests(unittest.TestCase):
    def test_compose_down_command_defaults(self) -> None:
        self.assertEqual(
            platform_down._compose_down_command(remove_volumes=False),
            [
                "docker",
                "compose",
                "-f",
                constants.COMPOSE_FILE,
                "-f",
                constants.APPS_COMPOSE_FILE,
                "-p",
                constants.COMPOSE_PROJECT,
                "--profile",
                constants.PLATFORM_PROFILE,
                "--profile",
                "load-testing",
                "down",
            ],
        )

    def test_compose_down_command_with_volumes(self) -> None:
        self.assertEqual(
            platform_down._compose_down_command(remove_volumes=True)[-1], "-v"
        )


class PlatformStatusTests(unittest.TestCase):
    @patch("scripts.platform_status._collect_status")
    def test_render_status_text(self, mock_collect: MagicMock) -> None:
        health = MagicMock()
        health.service = "rule-management"
        health.status.value = "healthy"
        mock_collect.return_value = (
            {"services": {"rule-management": {"runtime": "fastapi", "port": 8000}}},
            [health],
        )
        output = platform_status.render_status(json_mode=False)
        self.assertIn("Card Fraud Platform - Status Summary", output)
        self.assertIn("rule-management", output)

    @patch("scripts.platform_status._collect_status")
    def test_render_status_json(self, mock_collect: MagicMock) -> None:
        health = MagicMock()
        health.to_dict.return_value = {
            "service": "rule-management",
            "status": "healthy",
        }
        mock_collect.return_value = ({}, [health])
        payload = platform_status.render_status(json_mode=True)
        parsed = json.loads(payload)
        self.assertIn("services", parsed)
        self.assertEqual(parsed["services"][0]["service"], "rule-management")


class PlatformCheckTests(unittest.TestCase):
    def test_discover_control_plane_modules_includes_core_modules(self) -> None:
        modules = platform_check._discover_control_plane_modules()
        self.assertIn("scripts.control_plane.registry", modules)
        self.assertIn("scripts.control_plane.inventory.redis_runtime", modules)


if __name__ == "__main__":
    unittest.main()
