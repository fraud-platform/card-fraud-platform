"""Services inventory collector."""

import subprocess
from typing import Any

from ..models import CollectorResult
from .base import BaseCollector


class ServicesCollector(BaseCollector):
    """Collect service metadata from registry."""

    def __init__(self, registry):
        self.registry = registry

    def name(self) -> str:
        return "services"

    def collect(self, context: dict[str, Any] | None = None) -> CollectorResult:
        """Collect service metadata."""
        try:
            registry_data = self.registry.load()
            services = {}

            for service_id, entry in registry_data.services.items():
                adapter_path = self.registry.get_service_adapter_path(service_id)
                adapter_exists = adapter_path.exists() if adapter_path else False

                container_state = self._get_container_state(entry.container)

                services[service_id] = {
                    "repo": entry.repo,
                    "runtime": entry.runtime,
                    "port": entry.port,
                    "container": entry.container,
                    "container_state": container_state,
                    "auth_model": entry.auth_model.value,
                    "engine_family": entry.engine_family,
                    "action_domains": entry.action_domains,
                    "destructive_actions": entry.destructive_actions,
                    "adapter_exists": adapter_exists,
                    "description": entry.description,
                }

            return CollectorResult(
                collector=self.name(),
                success=True,
                data={"services": services},
            )

        except Exception as e:
            return CollectorResult(
                collector=self.name(),
                success=False,
                error=str(e),
            )

    def _get_container_state(self, container_name: str) -> str:
        """Get Docker container state."""
        try:
            result = subprocess.run(
                ["docker", "inspect", "-f", "{{.State.Status}}", container_name],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return "not-found"
        except Exception:
            return "unknown"
