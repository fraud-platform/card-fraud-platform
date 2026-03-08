"""Health aggregation for services."""

import subprocess
from datetime import datetime, timezone
from urllib.parse import urljoin

from .models import HealthAggregate, HealthStatus, ServiceRegistryEntry


HEALTH_HTTP_TIMEOUT = 5


class HealthChecker:
    """Check service health via HTTP endpoints."""

    def __init__(self, base_url: str = "http://localhost"):
        self.base_url = base_url

    def check_service(self, service: ServiceRegistryEntry) -> HealthAggregate:
        """Check health for a single service."""
        checked_at = datetime.now(timezone.utc)
        port = service.port

        container_running = self._is_container_running(service.container)

        if not container_running:
            return HealthAggregate(
                service=service.service_id,
                runtime=service.runtime,
                status=HealthStatus.NOT_RUNNING,
                checked_at=checked_at,
                source_path=service.health.path,
                message=f"Container {service.container} is not running",
            )

        health_url = urljoin(f"http://localhost:{port}", service.health.path)

        try:
            result = subprocess.run(
                ["curl", "-sf", "--max-time", str(HEALTH_HTTP_TIMEOUT), health_url],
                capture_output=True,
                text=True,
                timeout=HEALTH_HTTP_TIMEOUT + 2,
            )

            if result.returncode == 0:
                return HealthAggregate(
                    service=service.service_id,
                    runtime=service.runtime,
                    status=HealthStatus.HEALTHY,
                    checked_at=checked_at,
                    source_path=service.health.path,
                    message="Service is healthy",
                )
            else:
                return HealthAggregate(
                    service=service.service_id,
                    runtime=service.runtime,
                    status=HealthStatus.UNREACHABLE,
                    checked_at=checked_at,
                    source_path=service.health.path,
                    message=f"Health endpoint returned code {result.returncode}",
                )

        except subprocess.TimeoutExpired:
            return HealthAggregate(
                service=service.service_id,
                runtime=service.runtime,
                status=HealthStatus.UNREACHABLE,
                checked_at=checked_at,
                source_path=service.health.path,
                message="Health check timed out",
            )
        except Exception as e:
            return HealthAggregate(
                service=service.service_id,
                runtime=service.runtime,
                status=HealthStatus.UNREACHABLE,
                checked_at=checked_at,
                source_path=service.health.path,
                message=f"Health check failed: {str(e)}",
            )

    def _is_container_running(self, container_name: str) -> bool:
        """Check if a Docker container is running."""
        try:
            result = subprocess.run(
                ["docker", "inspect", "-f", "{{.State.Running}}", container_name],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0 and "true" in result.stdout.lower()
        except Exception:
            return False


def check_service_health(service: ServiceRegistryEntry) -> HealthAggregate:
    """Convenience function to check a service's health."""
    checker = HealthChecker()
    return checker.check_service(service)


def check_all_services_health(registry) -> list[HealthAggregate]:
    """Check health for all registered services."""
    checker = HealthChecker()
    results = []
    for service in registry.load().services.values():
        result = checker.check_service(service)
        results.append(result)
    return results
