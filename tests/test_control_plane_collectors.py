from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.control_plane.confirm import ConfirmationError, confirm_destructive
from scripts.control_plane.inventory.auth import AuthCollector
from scripts.control_plane.inventory.database import DatabaseCollector
from scripts.control_plane.inventory.messaging import MessagingCollector
from scripts.control_plane.inventory.secrets import SecretsCollector
from scripts.control_plane.inventory.storage import StorageCollector


class CollectorOwnershipTests(unittest.TestCase):
    def _write_temp_yaml(self, content: str) -> Path:
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
        with tmp:
            tmp.write(content)
        return Path(tmp.name)

    def test_database_collector_uses_declared_ownership(self) -> None:
        ownership = self._write_temp_yaml(
            """
services:
  rule-management:
    schema: fraud_gov
    tables: [rules, rule_versions]
    indices: [idx_rules_status]
reset_scopes:
  db-reset-data:
    supported_by: [rule-management]
"""
        )
        collector = DatabaseCollector(ownership_path=ownership)
        with patch.object(collector, "_is_db_reachable", return_value=False):
            result = collector.collect()
        self.assertTrue(result.success)
        self.assertEqual(result.data["services"]["rule-management"]["declared_tables"], 2)
        self.assertFalse(result.data["postgres_reachable"])

    def test_messaging_collector_merges_ownership_and_runtime(self) -> None:
        ownership = self._write_temp_yaml(
            """
topics:
  fraud.card.decisions.v1:
    owner: shared
consumer_groups:
  txn-group:
    owner: transaction-management
"""
        )
        collector = MessagingCollector(ownership_path=ownership)
        with patch.object(collector, "_list_topics", return_value=[{"name": "fraud.card.decisions.v1"}]):
            with patch.object(collector, "_list_consumer_groups", return_value=[{"name": "txn-group"}]):
                with patch.object(collector, "_is_redpanda_reachable", return_value=True):
                    result = collector.collect()
        self.assertTrue(result.success)
        self.assertTrue(result.data["topics"][0]["present_in_runtime"])
        self.assertEqual(result.data["consumer_groups"][0]["owner"], "transaction-management")

    def test_storage_collector_merges_ownership_and_runtime(self) -> None:
        ownership = self._write_temp_yaml(
            """
buckets:
  fraud-gov-artifacts:
    owner: platform
artifact_paths:
  rulesets:
    pattern: rulesets/{environment}
"""
        )
        collector = StorageCollector(ownership_path=ownership)
        with patch.object(collector, "_list_runtime_buckets", return_value=["fraud-gov-artifacts"]):
            with patch.object(collector, "_is_minio_reachable", return_value=True):
                result = collector.collect()
        self.assertTrue(result.success)
        self.assertEqual(result.data["buckets"][0]["name"], "fraud-gov-artifacts")
        self.assertTrue(result.data["buckets"][0]["present_in_runtime"])

    def test_auth_collector_loads_models_from_yaml(self) -> None:
        ownership = self._write_temp_yaml(
            """
auth_models:
  in-process:
    services: [rule-management]
shared:
  owner: platform
"""
        )
        result = AuthCollector(ownership_path=ownership).collect()
        self.assertTrue(result.success)
        self.assertIn("in-process", result.data["auth_models"])

    def test_secrets_collector_reports_missing_declared_projects(self) -> None:
        ownership = self._write_temp_yaml(
            """
projects:
  card-fraud-platform:
    owner: platform
    type: platform
    secrets: [POSTGRES_ADMIN_PASSWORD]
configs: [local]
"""
        )
        collector = SecretsCollector(ownership_path=ownership)
        with patch.object(collector, "_list_doppler_projects", return_value=[]):
            result = collector.collect()
        self.assertTrue(result.success)
        self.assertEqual(result.data["missing_runtime_projects"], ["card-fraud-platform"])


class ConfirmationTests(unittest.TestCase):
    def test_confirm_destructive_requires_yes_and_token(self) -> None:
        with self.assertRaises(ConfirmationError):
            confirm_destructive("rule-management", "db", "reset-data", yes_flag=True)

    def test_confirm_destructive_accepts_yes_and_matching_token(self) -> None:
        self.assertTrue(
            confirm_destructive(
                "rule-management",
                "db",
                "reset-data",
                yes_flag=True,
                confirm_token="rule-management:db:reset-data",
            )
        )


if __name__ == "__main__":
    unittest.main()
