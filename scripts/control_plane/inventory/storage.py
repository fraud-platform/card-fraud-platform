"""Storage (MinIO/S3) inventory collector."""

import subprocess
from pathlib import Path
from typing import Any

import yaml

from ..models import CollectorResult
from .base import BaseCollector


class StorageCollector(BaseCollector):
    """Collect MinIO/S3 storage inventory."""

    def __init__(self, ownership_path: Path | None = None):
        if ownership_path is None:
            ownership_path = (
                Path(__file__).parent.parent.parent.parent
                / "control-plane"
                / "ownership"
                / "storage.yaml"
            )
        self.ownership_path = ownership_path

    def name(self) -> str:
        return "storage"

    def collect(self, context: dict[str, Any] | None = None) -> CollectorResult:
        """Collect storage inventory."""
        try:
            ownership = self._load_ownership()
            runtime_buckets = self._list_runtime_buckets()
            buckets = self._merge_bucket_ownership(
                ownership.get("buckets", {}), runtime_buckets
            )

            return CollectorResult(
                collector=self.name(),
                success=True,
                data={
                    "buckets": buckets,
                    "artifact_paths": ownership.get("artifact_paths", {}),
                    "minio_reachable": self._is_minio_reachable(),
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

    def _is_minio_reachable(self) -> bool:
        """Check if MinIO is reachable."""
        try:
            result = subprocess.run(
                [
                    "curl",
                    "-sf",
                    "--max-time",
                    "4",
                    "http://localhost:9000/minio/health/ready",
                ],
                capture_output=True,
                timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _list_runtime_buckets(self) -> list[str]:
        """List runtime buckets from MinIO if the CLI alias is available."""
        try:
            result = subprocess.run(
                ["docker", "exec", "card-fraud-minio", "mc", "ls", "local/"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                return []

            buckets: list[str] = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split()
                if not parts:
                    continue
                name = parts[-1].strip().strip("/")
                if name:
                    buckets.append(name)
            return buckets

        except Exception:
            return []

    def _merge_bucket_ownership(
        self, owned_buckets: dict[str, dict[str, Any]], runtime_buckets: list[str]
    ) -> list[dict[str, Any]]:
        runtime_set = set(runtime_buckets)
        merged: list[dict[str, Any]] = []

        for bucket_name, spec in owned_buckets.items():
            merged.append(
                {
                    "name": bucket_name,
                    "owner": spec.get("owner"),
                    "description": spec.get("description", ""),
                    "access": spec.get("access", {}),
                    "declared": True,
                    "present_in_runtime": bucket_name in runtime_set,
                }
            )

        for bucket_name in runtime_buckets:
            if bucket_name not in owned_buckets:
                merged.append(
                    {
                        "name": bucket_name,
                        "declared": False,
                        "present_in_runtime": True,
                    }
                )

        return merged
