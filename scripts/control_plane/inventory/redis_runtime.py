"""Redis runtime inventory collector."""

import subprocess
from typing import Any

from ..models import CollectorResult
from .base import BaseCollector


class RedisRuntimeCollector(BaseCollector):
    """Collect Redis runtime inventory."""

    def name(self) -> str:
        return "redis-runtime"

    def collect(self, context: dict[str, Any] | None = None) -> CollectorResult:
        """Collect Redis health and summary runtime details."""
        try:
            reachable = self._ping()
            info = self._info_summary() if reachable else {}
            return CollectorResult(
                collector=self.name(),
                success=True,
                data={
                    "reachable": reachable,
                    "summary": info,
                },
            )
        except Exception as exc:
            return CollectorResult(
                collector=self.name(),
                success=False,
                error=str(exc),
            )

    def _ping(self) -> bool:
        try:
            result = subprocess.run(
                ["docker", "exec", "card-fraud-redis", "redis-cli", "ping"],
                capture_output=True,
                text=True,
                timeout=8,
            )
            return result.returncode == 0 and "PONG" in result.stdout
        except Exception:
            return False

    def _info_summary(self) -> dict[str, str]:
        try:
            result = subprocess.run(
                [
                    "docker",
                    "exec",
                    "card-fraud-redis",
                    "redis-cli",
                    "INFO",
                    "server",
                    "memory",
                    "keyspace",
                ],
                capture_output=True,
                text=True,
                timeout=8,
            )
            if result.returncode != 0:
                return {}

            summary: dict[str, str] = {}
            for line in result.stdout.splitlines():
                if not line or line.startswith("#") or ":" not in line:
                    continue
                key, value = line.split(":", 1)
                if key in ("redis_version", "uptime_in_seconds", "used_memory_human"):
                    summary[key] = value.strip()
                if key.startswith("db"):
                    summary[key] = value.strip()
            return summary
        except Exception:
            return {}
