"""Adapter manifest loading and validation."""

from pathlib import Path

import yaml

from .models import ActionSpec, AdapterManifest, DomainActions, ExecutionMode


class AdapterManifestError(Exception):
    """Error loading or validating adapter manifest."""

    pass


class AdapterManifestLoader:
    """Load and validate adapter manifests."""

    def __init__(self, manifest_path: Path):
        self.manifest_path = manifest_path
        self._manifest: AdapterManifest | None = None

    def load(self) -> AdapterManifest:
        """Load and parse the adapter manifest."""
        if self._manifest is not None:
            return self._manifest

        if not self.manifest_path.exists():
            raise AdapterManifestError(
                f"Adapter manifest not found: {self.manifest_path}"
            )

        with open(self.manifest_path, "r") as f:
            data = yaml.safe_load(f)

        service = data.get("service", "")
        if not service:
            raise AdapterManifestError(
                f"Invalid adapter manifest {self.manifest_path}: missing 'service'"
            )
        version = data.get("version", "1.0")
        entrypoints_data = data.get("entrypoints", {})
        if not isinstance(entrypoints_data, dict) or not entrypoints_data:
            raise AdapterManifestError(
                f"Invalid adapter manifest {self.manifest_path}: missing 'entrypoints'"
            )

        entrypoints = {}
        for domain, actions in entrypoints_data.items():
            if not isinstance(actions, dict):
                raise AdapterManifestError(
                    f"Invalid adapter manifest {self.manifest_path}: "
                    f"domain '{domain}' must map to actions"
                )
            domain_actions = DomainActions(actions={})
            for action_name, action_data in actions.items():
                mode_list = action_data.get("mode", ["standalone", "suite"])
                modes = []
                for m in mode_list:
                    if m == "standalone":
                        modes.append(ExecutionMode.STANDALONE)
                    elif m == "suite":
                        modes.append(ExecutionMode.SUITE)
                if not modes:
                    modes = [ExecutionMode.STANDALONE, ExecutionMode.SUITE]

                command = action_data.get("command", [])
                if not isinstance(command, list) or not command:
                    raise AdapterManifestError(
                        f"Invalid adapter manifest {self.manifest_path}: "
                        f"{domain}.{action_name} must declare a non-empty command array"
                    )

                spec = ActionSpec(
                    command=command,
                    destructive=action_data.get("destructive", False),
                    timeout_seconds=action_data.get("timeout_seconds", 60),
                    requires_confirmation=action_data.get(
                        "requires_confirmation", False
                    ),
                    mode=modes,
                    description=action_data.get("description", ""),
                )
                domain_actions.actions[action_name] = spec
            entrypoints[domain] = domain_actions

        self._manifest = AdapterManifest(
            service=service, version=version, entrypoints=entrypoints
        )
        return self._manifest

    def get_action(self, domain: str, action: str) -> ActionSpec | None:
        """Get a specific action from the manifest."""
        return self.load().get_action(domain, action)

    def list_domains(self) -> list[str]:
        """List all action domains in the manifest."""
        return list(self.load().entrypoints.keys())

    def list_actions(self, domain: str) -> list[str]:
        """List all actions for a given domain."""
        manifest = self.load()
        if domain not in manifest.entrypoints:
            return []
        return list(manifest.entrypoints[domain].actions.keys())

    def is_destructive(self, domain: str, action: str) -> bool:
        """Check if an action is destructive."""
        act = self.get_action(domain, action)
        return act.destructive if act else False

    def requires_confirmation(self, domain: str, action: str) -> bool:
        """Check if an action requires confirmation."""
        act = self.get_action(domain, action)
        return act.requires_confirmation if act else False


def load_adapter(service_id: str, registry) -> AdapterManifestLoader | None:
    """Load adapter manifest for a service."""
    adapter_path = registry.get_service_adapter_path(service_id)
    if adapter_path is None or not adapter_path.exists():
        return None
    return AdapterManifestLoader(adapter_path)
