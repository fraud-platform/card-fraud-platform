from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts import constants, platform_check, platform_down, platform_status, platform_up


class ConstantsTests(unittest.TestCase):
    def test_compose_files_exist(self) -> None:
        self.assertTrue(Path(constants.COMPOSE_FILE).exists())
        self.assertTrue(Path(constants.APPS_COMPOSE_FILE).exists())

    def test_all_container_names_are_unique(self) -> None:
        names = [name for group in constants.ALL_CONTAINERS.values() for name, _, _ in group]
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
        with patch("sys.argv", ["platform-up", "--load-testing", "--build", "--force-recreate", "--jfr"]):
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
        self.assertEqual(platform_down._compose_down_command(remove_volumes=True)[-1], "-v")


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
