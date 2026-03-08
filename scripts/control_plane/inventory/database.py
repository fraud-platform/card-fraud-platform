"""Database inventory collector."""

import subprocess
from pathlib import Path
from typing import Any

import yaml

from ..models import CollectorResult
from .base import BaseCollector


class DatabaseCollector(BaseCollector):
    """Collect database ownership information."""

    def __init__(self, ownership_path: Path | None = None):
        if ownership_path is None:
            ownership_path = (
                Path(__file__).parent.parent.parent.parent
                / "control-plane"
                / "ownership"
                / "database.yaml"
            )
        self.ownership_path = ownership_path

    def name(self) -> str:
        return "database"

    def collect(self, context: dict[str, Any] | None = None) -> CollectorResult:
        """Collect database inventory."""
        try:
            ownership = self._load_ownership()
            services = ownership.get("services", {})
            reset_scopes = ownership.get("reset_scopes", {})
            reachable = self._is_db_reachable()

            table_ownership: dict[str, Any] = {}
            for service_name, spec in services.items():
                declared_tables = spec.get("tables", [])
                declared_indices = spec.get("indices", [])
                table_ownership[service_name] = {
                    "schema": spec.get("schema", "fraud_gov"),
                    "declared_tables": len(declared_tables),
                    "declared_indices": len(declared_indices),
                    "reachable": reachable,
                    "existing_tables": self._count_existing_tables(declared_tables)
                    if reachable
                    else None,
                    "existing_indices": self._count_existing_indices(declared_indices)
                    if reachable
                    else None,
                }

            return CollectorResult(
                collector=self.name(),
                success=True,
                data={
                    "services": table_ownership,
                    "reset_scopes": reset_scopes,
                    "postgres_reachable": reachable,
                },
            )

        except Exception as e:
            return CollectorResult(
                collector=self.name(),
                success=False,
                error=str(e),
            )

    def _is_db_reachable(self) -> bool:
        """Check if PostgreSQL is reachable."""
        try:
            result = subprocess.run(
                [
                    "docker",
                    "exec",
                    "card-fraud-postgres",
                    "psql",
                    "-U",
                    "postgres",
                    "-d",
                    "fraud_gov",
                    "-c",
                    "SELECT 1",
                ],
                capture_output=True,
                timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _load_ownership(self) -> dict[str, Any]:
        if not self.ownership_path.exists():
            return {}
        with open(self.ownership_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _count_existing_tables(self, table_names: list[str]) -> int | None:
        if not table_names:
            return 0
        quoted_tables = ", ".join(f"'{name}'" for name in table_names)
        sql = (
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema = 'fraud_gov' "
            f"AND table_name IN ({quoted_tables});"
        )
        return self._run_scalar_query(sql)

    def _count_existing_indices(self, index_names: list[str]) -> int | None:
        if not index_names:
            return 0
        quoted_indices = ", ".join(f"'{name}'" for name in index_names)
        sql = (
            "SELECT COUNT(*) FROM pg_indexes "
            "WHERE schemaname = 'fraud_gov' "
            f"AND indexname IN ({quoted_indices});"
        )
        return self._run_scalar_query(sql)

    def _run_scalar_query(self, sql: str) -> int | None:
        try:
            result = subprocess.run(
                [
                    "docker",
                    "exec",
                    "card-fraud-postgres",
                    "psql",
                    "-U",
                    "postgres",
                    "-d",
                    "fraud_gov",
                    "-t",
                    "-A",
                    "-c",
                    sql,
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode != 0:
                return None
            output = result.stdout.strip()
            return int(output) if output else 0
        except Exception:
            return None
