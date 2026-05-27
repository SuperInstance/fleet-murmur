"""MurmurMessage — the fundamental unit of fleet gossip."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class MurmurMessage:
    """An immutable gossip message with TTL, origin tracking, and typed payload.

    Attributes:
        msg_id:      Unique identifier (auto-generated if omitted).
        origin:      Node/peer ID that created the message.
        topic:       Channel / topic string for filtering.
        payload:     Arbitrary serialisable data.
        ttl:         Time-to-live in seconds (0 = never expires).
        created_at:  Epoch seconds when the message was created.
        hops:        Number of gossip rounds this message has survived.
    """

    origin: str
    topic: str
    payload: Any
    ttl: float = 60.0
    msg_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    created_at: float = field(default_factory=time.time)
    hops: int = 0

    # -- derived helpers -----------------------------------------------------

    @property
    def is_expired(self) -> bool:
        """Return True if the message has exceeded its TTL."""
        if self.ttl <= 0:
            return False  # TTL=0 means never expires
        return (time.time() - self.created_at) > self.ttl

    def with_hop(self) -> "MurmurMessage":
        """Return a new message with ``hops`` incremented by one."""
        return MurmurMessage(
            origin=self.origin,
            topic=self.topic,
            payload=self.payload,
            ttl=self.ttl,
            msg_id=self.msg_id,
            created_at=self.created_at,
            hops=self.hops + 1,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a plain dict."""
        return {
            "msg_id": self.msg_id,
            "origin": self.origin,
            "topic": self.topic,
            "payload": self.payload,
            "ttl": self.ttl,
            "created_at": self.created_at,
            "hops": self.hops,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MurmurMessage":
        """Deserialise from a plain dict."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"MurmurMessage(id={self.msg_id!r}, origin={self.origin!r}, "
            f"topic={self.topic!r}, hops={self.hops})"
        )
