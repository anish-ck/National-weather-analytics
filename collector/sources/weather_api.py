from .base import SourceAdapter

class WeatherApiSource(SourceAdapter):
    """Provider-specific API adapter; credentials are intentionally environment-only."""
    def collect(self) -> list[dict]: return []
