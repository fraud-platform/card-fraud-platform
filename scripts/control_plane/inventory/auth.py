"""Auth ownership inventory collector."""

from pathlib import Path
from typing import Any

import yaml

from ..models import CollectorResult
from .base import BaseCollector


class AuthCollector(BaseCollector):
    """Collect Auth0 ownership inventory."""

    def __init__(self, ownership_path: Path | None = None, registry=None):
        if ownership_path is None:
            ownership_path = (
                Path(__file__).parent.parent.parent.parent
                / "control-plane"
                / "ownership"
                / "auth.yaml"
            )
        self.ownership_path = ownership_path
        self.registry = registry

    def name(self) -> str:
        return "auth"

    def collect(self, context: dict[str, Any] | None = None) -> CollectorResult:
        """Collect auth ownership inventory."""
        try:
            ownership = self._load_ownership()
            models = ownership.get("auth_models", {})

            registry_models: dict[str, list[str]] = {}
            if self.registry is not None:
                for service in self.registry.load().services.values():
                    registry_models.setdefault(service.auth_model.value, []).append(
                        service.service_id
                    )

            return CollectorResult(
                collector=self.name(),
                success=True,
                data={
                    "note": "Auth ownership is manifest-driven via control-plane/ownership/auth.yaml",
                    "auth_models": models,
                    "shared": ownership.get("shared", {}),
                    "service_specific": ownership.get("service_specific", {}),
                    "registry_auth_models": registry_models,
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
