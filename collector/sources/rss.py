from .base import SourceAdapter

class RssSource(SourceAdapter):
    """Add only authorised RSS feed URLs and normalise their entries here."""
    def collect(self) -> list[dict]: return []
