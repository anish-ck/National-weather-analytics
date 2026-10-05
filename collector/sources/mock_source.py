from datetime import datetime, timezone
from uuid import uuid4
from .base import SourceAdapter

class MockSource(SourceAdapter):
    samples = [
      ("Heavy rainfall and waterlogging near Madurai railway station.", 9.9195, 78.1193, "HEAVY_RAINFALL", "Madurai"),
      ("Flooding reported in low-lying areas of Chennai after intense rain.", 13.0827, 80.2707, "FLOOD", "Chennai"),
      ("Thunderstorm with strong winds in Coimbatore.", 11.0168, 76.9558, "THUNDERSTORM", "Coimbatore"),
      ("Heatwave conditions reported across Rajasthan.", 26.9124, 75.7873, "HEATWAVE", "Rajasthan"),
    ]
    def __init__(self): self.index = 0
    def collect(self):
        text, lat, lon, kind, place = self.samples[self.index % len(self.samples)]; self.index += 1
        return [{"event_id": str(uuid4()), "source": "MOCK", "text": text, "latitude": lat, "longitude": lon, "event_type": kind, "location_name": place, "timestamp": datetime.now(timezone.utc).isoformat(), "metadata": {"adapter": "mock"}}]
