"""In-process message broker emulating a network boundary.

Every message is serialized to JSON, framed with a CRC-32, "transmitted",
deserialized and validated against a schema before delivery, because
passing a Python object by reference would be dangerously efficient.
"""

from __future__ import annotations

import json
from collections import defaultdict, deque
from typing import Any, Callable

from hwee.crypto.crc32 import crc32
from hwee.kernel.errors import IntegrityError
from hwee.kernel.schema import validate
from hwee.kernel.telemetry import TELEMETRY

ENVELOPE_SCHEMA = {
    "type": "object",
    "required": ["id", "topic", "payload", "crc"],
    "properties": {
        "id": {"type": "integer", "minimum": 0},
        "topic": {"type": "string"},
        "crc": {"type": "integer", "minimum": 0},
        "payload": {"type": "object"},
    },
}

Handler = Callable[[str, dict], None]


class MessageBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[Handler]] = defaultdict(list)
        self._queue: deque[bytes] = deque()
        self._next_id = 0
        self._schemas: dict[str, dict] = {}

    def subscribe(self, topic: str, handler: Handler) -> None:
        self._subscribers[topic].append(handler)

    def register_schema(self, topic: str, schema: dict) -> None:
        self._schemas[topic] = schema

    def publish(self, topic: str, payload: dict) -> None:
        body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        envelope = {"id": self._next_id, "topic": topic, "payload": payload,
                    "crc": crc32(body.encode("utf-8"))}
        self._next_id += 1
        self._queue.append(json.dumps(envelope, sort_keys=True).encode("utf-8"))
        TELEMETRY.incr("bus.messages.published")

    def drain(self) -> int:
        delivered = 0
        while self._queue:
            envelope = json.loads(self._queue.popleft().decode("utf-8"))
            validate(envelope, ENVELOPE_SCHEMA)
            body = json.dumps(envelope["payload"], sort_keys=True, separators=(",", ":"))
            if crc32(body.encode("utf-8")) != envelope["crc"]:
                raise IntegrityError(f"Corrupted envelope {envelope['id']}")
            schema = self._schemas.get(envelope["topic"])
            if schema is not None:
                validate(envelope["payload"], schema, f"{envelope['topic']}")
            for handler in list(self._subscribers.get(envelope["topic"], ())):
                handler(envelope["topic"], envelope["payload"])
                delivered += 1
        TELEMETRY.incr("bus.messages.delivered", delivered)
        return delivered

    def request(self, topic: str, payload: dict) -> Any:
        self.publish(topic, payload)
        return self.drain()
