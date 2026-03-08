"""Audit logging for control plane actions."""

import json
from datetime import datetime, timezone
from pathlib import Path

from .models import ActionStatus, AuditRecord


class AuditLogger:
    """Log actions to the audit trail."""

    def __init__(self, log_path: Path | None = None):
        if log_path is None:
            log_path = (
                Path(__file__).parent.parent.parent
                / "control-plane"
                / "logs"
                / "action-history.jsonl"
            )
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, record: AuditRecord) -> None:
        """Write an audit record to the log."""
        with open(self.log_path, "a") as f:
            f.write(json.dumps(record.to_dict()) + "\n")

    def log_start(
        self,
        service: str,
        domain: str,
        action: str,
        scope: str,
        destructive: bool,
        actor: str | None = None,
    ) -> AuditRecord:
        """Log the start of an action."""
        record = AuditRecord(
            timestamp=datetime.now(timezone.utc),
            service=service,
            domain=domain,
            action=action,
            scope=scope,
            destructive=destructive,
            actor=actor,
            outcome=ActionStatus.OK,
            summary=f"Started {domain}:{action} on {service}",
            started_at=datetime.now(timezone.utc),
        )
        self.log(record)
        return record

    def log_complete(
        self,
        record: AuditRecord,
        outcome: ActionStatus,
        summary: str,
    ) -> None:
        """Log the completion of an action."""
        record.completed_at = datetime.now(timezone.utc)
        record.outcome = outcome
        record.summary = summary
        self.log(record)

    def get_recent(self, limit: int = 10) -> list[AuditRecord]:
        """Get recent audit records."""
        if not self.log_path.exists():
            return []

        records = []
        with open(self.log_path, "r") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    records.append(
                        AuditRecord(
                            timestamp=datetime.fromisoformat(data["timestamp"]),
                            service=data["service"],
                            domain=data["domain"],
                            action=data["action"],
                            scope=data["scope"],
                            destructive=data["destructive"],
                            actor=data.get("actor"),
                            outcome=ActionStatus(data["outcome"]),
                            summary=data["summary"],
                            started_at=datetime.fromisoformat(data["started_at"])
                            if data.get("started_at")
                            else None,
                            completed_at=datetime.fromisoformat(data["completed_at"])
                            if data.get("completed_at")
                            else None,
                        )
                    )
        return records[-limit:]


_audit_logger: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
