import asyncio
import json
from collections.abc import AsyncIterator


class DispatchEventHub:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[str]] = set()

    async def publish(self, event_type: str, resource_id: str = "") -> None:
        payload = json.dumps({"type": event_type, "resource_id": resource_id})
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                pass

    async def stream(self) -> AsyncIterator[str]:
        queue: asyncio.Queue[str] = asyncio.Queue(maxsize=50)
        self._subscribers.add(queue)
        try:
            yield "event: connected\ndata: {\"type\":\"connected\"}\n\n"
            while True:
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=15)
                    yield f"event: dispatch\ndata: {payload}\n\n"
                except TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            self._subscribers.discard(queue)


dispatch_events = DispatchEventHub()