"""SSE event bus — fan-out asyncio queues for dashboard live updates."""

from __future__ import annotations

import asyncio
import json
from typing import Union

from app.models import (
    AgitationUpdateEvent,
    EpisodeEndEvent,
    EpisodeStartEvent,
    NotificationEvent,
    SensorUpdateEvent,
    TranscriptionEvent,
    VitalsUpdateEvent,
)

SSEEvent = Union[
    AgitationUpdateEvent,
    EpisodeStartEvent,
    EpisodeEndEvent,
    NotificationEvent,
    SensorUpdateEvent,
    TranscriptionEvent,
    VitalsUpdateEvent,
]


class EventBus:
    def __init__(self) -> None:
        self._subscribers: list[asyncio.Queue[SSEEvent]] = []

    def subscribe(self) -> asyncio.Queue[SSEEvent]:
        q: asyncio.Queue[SSEEvent] = asyncio.Queue(maxsize=100)
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[SSEEvent]) -> None:
        self._subscribers.remove(q)

    async def publish(self, event: SSEEvent) -> None:
        for q in list(self._subscribers):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass  # slow consumer — drop rather than block

    def format_sse(self, event: SSEEvent) -> str:
        # No named event: field — browser EventSource.onmessage only fires for unnamed events
        return f"data: {json.dumps(event.model_dump())}\n\n"


# Module-level singleton
event_bus = EventBus()
