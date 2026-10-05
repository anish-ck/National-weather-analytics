from .base import SourceAdapter

class CitizenSource(SourceAdapter):
    """HTTP reports arrive through the backend, which publishes this adapter's raw schema."""
    def collect(self) -> list[dict]: return []
