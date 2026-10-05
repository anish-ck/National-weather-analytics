import asyncio, json
from fastapi import WebSocket

class EventBroadcaster:
    def __init__(self): self.connections: set[WebSocket] = set()
    async def connect(self, socket: WebSocket):
        await socket.accept(); self.connections.add(socket)
    def disconnect(self, socket: WebSocket): self.connections.discard(socket)
    async def broadcast(self, event: dict):
        stale = []
        for socket in self.connections:
            try: await socket.send_json({"type": "event.created", "event": event})
            except Exception: stale.append(socket)
        for socket in stale: self.disconnect(socket)

broadcaster = EventBroadcaster()
