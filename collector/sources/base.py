from abc import ABC, abstractmethod
from typing import Any

class SourceAdapter(ABC):
    @abstractmethod
    def collect(self) -> list[dict[str, Any]]: """Return reports in the shared raw schema."""
