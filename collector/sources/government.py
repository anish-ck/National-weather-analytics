from .base import SourceAdapter

class GovernmentSource(SourceAdapter):
    """Reserved for permitted IMD/government bulletin integrations."""
    def collect(self) -> list[dict]: return []
