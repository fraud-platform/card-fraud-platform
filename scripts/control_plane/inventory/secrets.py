"""Secrets (Doppler) inventory collector."""

import json
import subprocess
from pathlib import Path
from typing import Any

import yaml

from ..models import CollectorResult
from .base import BaseCollector


class SecretsCollector(BaseCollector):
    """Collect Doppler secrets inventory."""

    def __init__(self, ownership_path: Path | None = None):
        if ownership_path is None:
            ownership_path = (
                Path(__file__).parent.parent.parent.parent
                / "control-plane"
                / "ownership"
                / "secrets.yaml"
            )
        self.ownership_path = ownership_path

    def name(self) -> str:
        return "secrets"

    def collect(self, context: dict[str, Any] | None = None) -> CollectorResult:
        """Collect secrets inventory."""
        try:
            ownership = self._load_ownership()
            declared_projects = ownership.get("projects", {})
            runtime_projects = self._list_doppler_projects()
            runtime_names = {p.get("name", "") for p in runtime_projects}

            return CollectorResult(
                collector=self.name(),
                success=True,
                data={
                    "declared_projects": [
                        {
                            "name": name,
                            "owner": spec.get("owner"),
                            "type": spec.get("type"),
                            "secret_count": len(spec.get("secrets", [])),
                        }
                        for name, spec in declared_projects.items()
                    ],
                    "runtime_projects": runtime_projects,
                    "missing_runtime_projects": [
                        name for name in declared_projects if name not in runtime_names
                    ],
                    "configs": ownership.get("configs", []),
                    "note": "Secret values are not fetched. Ownership is sourced from control-plane/ownership/secrets.yaml.",
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

    def _list_doppler_projects(self) -> list[dict]:
        """List Doppler projects (name-only, no values)."""
        try:
            result = subprocess.run(
                ["doppler", "projects", "list", "--json"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                return []

            projects_data = json.loads(result.stdout)
            return [{"name": p.get("name", "")} for p in projects_data]

        except Exception:
            return []
