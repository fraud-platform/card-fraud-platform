"""Messaging (Kafka) inventory collector."""

import subprocess
from pathlib import Path
from typing import Any

import yaml

from ..models import CollectorResult
from .base import BaseCollector


class MessagingCollector(BaseCollector):
    """Collect Kafka/Redpanda messaging inventory."""

    def __init__(self, ownership_path: Path | None = None):
        if ownership_path is None:
            ownership_path = (
                Path(__file__).parent.parent.parent.parent
                / "control-plane"
                / "ownership"
                / "messaging.yaml"
            )
        self.ownership_path = ownership_path

    def name(self) -> str:
        return "messaging"

    def collect(self, context: dict[str, Any] | None = None) -> CollectorResult:
        """Collect messaging inventory."""
        try:
            ownership = self._load_ownership()
            runtime_topics = self._list_topics()
            runtime_groups = self._list_consumer_groups()

            topics = self._merge_topic_ownership(ownership.get("topics", {}), runtime_topics)
            consumer_groups = self._merge_consumer_group_ownership(
                ownership.get("consumer_groups", {}), runtime_groups
            )

            return CollectorResult(
                collector=self.name(),
                success=True,
                data={
                    "topics": topics,
                    "consumer_groups": consumer_groups,
                    "dlq_pattern": ownership.get("dlq_pattern", {}),
                    "redpanda_reachable": self._is_redpanda_reachable(),
                },
            )

        except Exception as e:
            return CollectorResult(
                collector=self.name(),
                success=False,
                error=str(e),
            )

    def _load_ownership(self) -> dict[str, Any]:
        if not self.ownership_path.exists():
            return {}
        with open(self.ownership_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _is_redpanda_reachable(self) -> bool:
        """Check if Redpanda is reachable."""
        try:
            result = subprocess.run(
                ["docker", "exec", "card-fraud-redpanda", "rpk", "cluster", "info"],
                capture_output=True,
                timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _list_topics(self) -> list[dict]:
        """List Kafka topics."""
        try:
            result = subprocess.run(
                ["docker", "exec", "card-fraud-redpanda", "rpk", "topic", "list"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                return []

            topics = []
            for line in result.stdout.strip().split("\n")[1:]:
                parts = line.split()
                if parts:
                    topics.append({"name": parts[0]})
            return topics

        except Exception:
            return []

    def _list_consumer_groups(self) -> list[dict]:
        """List Kafka consumer groups."""
        try:
            result = subprocess.run(
                ["docker", "exec", "card-fraud-redpanda", "rpk", "group", "list"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                return []

            groups = []
            for line in result.stdout.strip().split("\n")[1:]:
                parts = line.split()
                if parts:
                    groups.append({"name": parts[0]})
            return groups

        except Exception:
            return []

    def _merge_topic_ownership(
        self, owned_topics: dict[str, dict[str, Any]], runtime_topics: list[dict[str, str]]
    ) -> list[dict[str, Any]]:
        runtime_names = {t.get("name", "") for t in runtime_topics}
        merged: list[dict[str, Any]] = []

        for topic_name, spec in owned_topics.items():
            merged.append(
                {
                    "name": topic_name,
                    "owner": spec.get("owner"),
                    "producers": spec.get("producers", []),
                    "description": spec.get("description", ""),
                    "declared": True,
                    "present_in_runtime": topic_name in runtime_names,
                }
            )

        for topic in runtime_topics:
            name = topic.get("name", "")
            if name and name not in owned_topics:
                merged.append(
                    {
                        "name": name,
                        "declared": False,
                        "present_in_runtime": True,
                    }
                )

        return merged

    def _merge_consumer_group_ownership(
        self, owned_groups: dict[str, dict[str, Any]], runtime_groups: list[dict[str, str]]
    ) -> list[dict[str, Any]]:
        runtime_names = {g.get("name", "") for g in runtime_groups}
        merged: list[dict[str, Any]] = []

        for group_name, spec in owned_groups.items():
            merged.append(
                {
                    "name": group_name,
                    "owner": spec.get("owner"),
                    "topics": spec.get("topics", []),
                    "description": spec.get("description", ""),
                    "declared": True,
                    "present_in_runtime": group_name in runtime_names,
                }
            )

        for group in runtime_groups:
            name = group.get("name", "")
            if name and name not in owned_groups:
                merged.append(
                    {
                        "name": name,
                        "declared": False,
                        "present_in_runtime": True,
                    }
                )

        return merged
