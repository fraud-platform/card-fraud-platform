"""Typed models for the control plane."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNREACHABLE = "unreachable"
    NOT_RUNNING = "not-running"
    UNKNOWN = "unknown"


class ActionStatus(str, Enum):
    OK = "ok"
    FAILED = "failed"
    TIMEOUT = "timeout"
    INVALID_OUTPUT = "invalid_output"
    RUNTIME_FAILED = "runtime_failed"
    CANCELLED = "cancelled"


class AuthModel(str, Enum):
    IN_PROCESS = "in-process"
    GATEWAY = "gateway"
    SPA = "spa"
    NONE = "none"


class ExecutionMode(str, Enum):
    STANDALONE = "standalone"
    SUITE = "suite"


@dataclass
class HealthSpec:
    kind: str
    path: str
    readiness_path: str
    container_port: int


@dataclass
class ServiceRegistryEntry:
    service_id: str
    repo: str
    runtime: str
    port: int
    container: str
    health: HealthSpec
    auth_model: AuthModel
    engine_family: str | None
    adapter_manifest: str
    action_domains: list[str]
    destructive_actions: list[str]
    description: str


@dataclass
class InfrastructureEntry:
    service: str
    port: int
    container: str
    managed_by: str
    console_port: int | None = None
    otlp_grpc: int | None = None
    otlp_http: int | None = None


@dataclass
class ServiceRegistry:
    services: dict[str, ServiceRegistryEntry] = field(default_factory=dict)
    infrastructure: dict[str, InfrastructureEntry] = field(default_factory=dict)


@dataclass
class ActionSpec:
    command: list[str]
    destructive: bool
    timeout_seconds: int
    requires_confirmation: bool = False
    mode: list[ExecutionMode] = field(
        default_factory=lambda: [ExecutionMode.STANDALONE, ExecutionMode.SUITE]
    )
    description: str = ""


@dataclass
class DomainActions:
    actions: dict[str, ActionSpec] = field(default_factory=dict)


@dataclass
class AdapterManifest:
    service: str
    version: str
    entrypoints: dict[str, DomainActions] = field(default_factory=dict)

    def get_action(self, domain: str, action: str) -> ActionSpec | None:
        if domain not in self.entrypoints:
            return None
        domain_actions = self.entrypoints[domain]
        return domain_actions.actions.get(action)


@dataclass
class InventoryRecord:
    collector: str
    scope: str
    data: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class InventorySnapshot:
    records: list[InventoryRecord] = field(default_factory=list)

    def add(self, collector: str, scope: str, data: dict[str, Any]) -> None:
        self.records.append(
            InventoryRecord(collector=collector, scope=scope, data=data)
        )


@dataclass
class ActionResult:
    service: str
    domain: str
    action: str
    target: str
    status: ActionStatus
    summary: str
    details: list[str] = field(default_factory=list)
    destructive: bool = False
    started_at: datetime | None = None
    completed_at: datetime | None = None
    artifacts: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "service": self.service,
            "domain": self.domain,
            "action": self.action,
            "target": self.target,
            "status": self.status.value,
            "summary": self.summary,
            "details": self.details,
            "destructive": self.destructive,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "artifacts": self.artifacts,
            "next_steps": self.next_steps,
            "error": self.error,
        }


@dataclass
class AuditRecord:
    timestamp: datetime
    service: str
    domain: str
    action: str
    scope: str
    destructive: bool
    actor: str | None
    outcome: ActionStatus
    summary: str
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "service": self.service,
            "domain": self.domain,
            "action": self.action,
            "scope": self.scope,
            "destructive": self.destructive,
            "actor": self.actor,
            "outcome": self.outcome.value,
            "summary": self.summary,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
        }


@dataclass
class CollectorResult:
    collector: str
    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None


@dataclass
class HealthAggregate:
    service: str
    runtime: str
    status: HealthStatus
    checked_at: datetime
    dependencies: dict[str, HealthStatus] = field(default_factory=dict)
    source_path: str = ""
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "service": self.service,
            "runtime": self.runtime,
            "status": self.status.value,
            "checked_at": self.checked_at.isoformat(),
            "dependencies": {k: v.value for k, v in self.dependencies.items()},
            "source_path": self.source_path,
            "message": self.message,
        }
