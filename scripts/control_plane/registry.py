"""Service registry loading and validation."""

from pathlib import Path

import yaml

from .models import (
    AuthModel,
    HealthSpec,
    InfrastructureEntry,
    ServiceRegistry,
    ServiceRegistryEntry,
)


class Registry:
    """Load and manage the service registry."""

    def __init__(self, registry_path: Path | None = None):
        if registry_path is None:
            registry_path = (
                Path(__file__).parent.parent.parent / "control-plane" / "services.yaml"
            )
        self._registry_path = registry_path
        self._registry: ServiceRegistry | None = None

    def load(self) -> ServiceRegistry:
        """Load and parse the services.yaml registry."""
        if self._registry is not None:
            return self._registry

        with open(self._registry_path, "r") as f:
            data = yaml.safe_load(f)

        services = {}
        for service_id, service_data in data.get("services", {}).items():
            health_data = service_data.get("health", {})
            health = HealthSpec(
                kind=health_data.get("kind", "http"),
                path=health_data.get("path", "/health"),
                readiness_path=health_data.get("readiness_path", "/health"),
                container_port=health_data.get("container_port", 8000),
            )

            auth_model_str = service_data.get("auth_model", "in-process")
            auth_model = AuthModel.IN_PROCESS
            if auth_model_str == "gateway":
                auth_model = AuthModel.GATEWAY
            elif auth_model_str == "spa":
                auth_model = AuthModel.SPA
            elif auth_model_str == "none":
                auth_model = AuthModel.NONE

            entry = ServiceRegistryEntry(
                service_id=service_id,
                repo=service_data.get("repo", ""),
                runtime=service_data.get("runtime", ""),
                port=service_data.get("port", 8000),
                container=service_data.get("container", ""),
                health=health,
                auth_model=auth_model,
                engine_family=service_data.get("engine_family"),
                adapter_manifest=service_data.get(
                    "adapter_manifest", "platform-adapter.yaml"
                ),
                action_domains=service_data.get("action_domains", []),
                destructive_actions=service_data.get("destructive_actions", []),
                description=service_data.get("description", ""),
            )
            services[service_id] = entry

        infrastructure = {}
        for infra_id, infra_data in data.get("infrastructure", {}).items():
            entry = InfrastructureEntry(
                service=infra_data.get("service", ""),
                port=infra_data.get("port", 0),
                container=infra_data.get("container", ""),
                managed_by=infra_data.get("managed_by", "platform"),
                console_port=infra_data.get("console_port"),
                otlp_grpc=infra_data.get("otlp_grpc"),
                otlp_http=infra_data.get("otlp_http"),
            )
            infrastructure[infra_id] = entry

        self._registry = ServiceRegistry(
            services=services, infrastructure=infrastructure
        )
        return self._registry

    def get(self, service_id: str) -> ServiceRegistryEntry | None:
        """Get a service by ID."""
        return self.load().services.get(service_id)

    def get_service_repo_path(self, service_id: str) -> Path | None:
        """Get the absolute path to a service's repo."""
        service = self.get(service_id)
        if service is None:
            return None
        platform_root = Path(__file__).parent.parent.parent
        repo_path = platform_root / service.repo
        return repo_path.resolve()

    def get_service_adapter_path(self, service_id: str) -> Path | None:
        """Get the path to a service's adapter manifest."""
        service = self.get(service_id)
        if service is None:
            return None
        repo_path = self.get_service_repo_path(service_id)
        if repo_path is None:
            return None
        adapter_path = repo_path / service.adapter_manifest
        return adapter_path

    def list_by_runtime(self, runtime: str) -> list[ServiceRegistryEntry]:
        """List all services by runtime."""
        return [s for s in self.load().services.values() if s.runtime == runtime]

    def list_by_engine_family(self, engine_family: str) -> list[ServiceRegistryEntry]:
        """List all services by engine family."""
        return [
            s for s in self.load().services.values() if s.engine_family == engine_family
        ]

    def list_by_action_domain(self, domain: str) -> list[ServiceRegistryEntry]:
        """List all services supporting a given action domain."""
        return [s for s in self.load().services.values() if domain in s.action_domains]

    def list_services(self) -> list[str]:
        """List all service IDs."""
        return list(self.load().services.keys())

    def list_infrastructure(self) -> list[str]:
        """List all infrastructure IDs."""
        return list(self.load().infrastructure.keys())


_registry: Registry | None = None


def get_registry() -> Registry:
    """Get the global registry instance."""
    global _registry
    if _registry is None:
        _registry = Registry()
    return _registry
