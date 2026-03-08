"""Docker runtime inventory collector."""

import subprocess
from typing import Any

from ..models import CollectorResult
from .base import BaseCollector


class DockerRuntimeCollector(BaseCollector):
    """Collect Docker container runtime information."""

    def name(self) -> str:
        return "docker-runtime"

    def collect(self, context: dict[str, Any] | None = None) -> CollectorResult:
        """Collect Docker runtime data."""
        try:
            result = subprocess.run(
                ["docker", "ps", "-a", "--format", "{{.Names}}|{{.Status}}|{{.Ports}}"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return CollectorResult(
                    collector=self.name(),
                    success=False,
                    error=result.stderr,
                )

            containers = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split("|")
                    containers.append(
                        {
                            "name": parts[0] if len(parts) > 0 else "",
                            "status": parts[1] if len(parts) > 1 else "",
                            "ports": parts[2] if len(parts) > 2 else "",
                        }
                    )

            return CollectorResult(
                collector=self.name(),
                success=True,
                data={"containers": containers},
            )

        except Exception as e:
            return CollectorResult(
                collector=self.name(),
                success=False,
                error=str(e),
            )

    def supports(self, scope: str) -> bool:
        return scope in ("all", "infra", "docker")
