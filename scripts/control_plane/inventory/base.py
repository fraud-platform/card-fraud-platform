"""Base collector interface for inventory."""

from abc import ABC, abstractmethod
from typing import Any

from ..models import CollectorResult


class BaseCollector(ABC):
    """Base class for inventory collectors."""

    @abstractmethod
    def name(self) -> str:
        """Return the collector name."""
        pass

    @abstractmethod
    def collect(self, context: dict[str, Any] | None = None) -> CollectorResult:
        """Collect inventory data."""
        pass

    def supports(self, scope: str) -> bool:
        """Check if this collector supports the given scope."""
        return True
