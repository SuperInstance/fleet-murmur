"""RumorMill — manages the lifecycle of gossip messages (rumors)."""

from __future__ import annotations

import enum
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from .message import MurmurMessage


class RumorState(enum.Enum):
    """Lifecycle stages of a rumor."""

    NEW = "new"          # Just received, not yet spread
    SPREADING = "spreading"  # Currently being gossiped
    KNOWN = "known"      # Fully propagated / no longer novel
    EXPIRED = "expired"  # TTL exceeded


@dataclass
class RumorEntry:
    """A rumor tracked by the mill."""

    message: MurmurMessage
    state: RumorState = RumorState.NEW
    received_at: float = field(default_factory=time.time)
    rounds_spread: int = 0
    max_rounds: int = 3  # Number of gossip rounds before settling


class RumorMill:
    """Manages message lifecycle: new → spreading → known → expired.

    The mill tracks which messages this node has seen, controls how many
    gossip rounds each message gets, and handles deduplication.
    """

    def __init__(self, max_rounds: int = 3, max_entries: int = 1000) -> None:
        self.max_rounds = max_rounds
        self.max_entries = max_entries
        self._entries: Dict[str, RumorEntry] = {}
        self._seen_ids: Set[str] = set()

    # -- core operations -----------------------------------------------------

    def receive(self, message: MurmurMessage) -> bool:
        """Accept a message. Returns True if it was new, False if duplicate."""
        if message.msg_id in self._seen_ids:
            return False

        if message.is_expired:
            self._seen_ids.add(message.msg_id)
            return False

        self._seen_ids.add(message.msg_id)
        entry = RumorEntry(message=message, state=RumorState.NEW, max_rounds=self.max_rounds)
        self._entries[message.msg_id] = entry
        self._enforce_cap()
        return True

    def tick(self) -> List[MurmurMessage]:
        """Advance all entries one round. Returns messages to gossip this round."""
        to_spread: List[MurmurMessage] = []

        expired_ids: List[str] = []
        for msg_id, entry in self._entries.items():
            if entry.message.is_expired:
                entry.state = RumorState.EXPIRED
                expired_ids.append(msg_id)
                continue

            if entry.state == RumorState.NEW:
                entry.state = RumorState.SPREADING

            if entry.state == RumorState.SPREADING:
                entry.rounds_spread += 1
                to_spread.append(entry.message)

                if entry.rounds_spread >= entry.max_rounds:
                    entry.state = RumorState.KNOWN

        # Clean up expired
        for mid in expired_ids:
            del self._entries[mid]

        return to_spread

    def mark_known(self, msg_id: str) -> None:
        """Manually mark a message as fully known."""
        entry = self._entries.get(msg_id)
        if entry is not None:
            entry.state = RumorState.KNOWN

    # -- queries -------------------------------------------------------------

    def has_seen(self, msg_id: str) -> bool:
        return msg_id in self._seen_ids

    def get_state(self, msg_id: str) -> Optional[RumorState]:
        entry = self._entries.get(msg_id)
        return entry.state if entry else None

    @property
    def active_count(self) -> int:
        """Number of non-expired, non-known entries."""
        return sum(
            1 for e in self._entries.values()
            if e.state in (RumorState.NEW, RumorState.SPREADING)
        )

    @property
    def known_count(self) -> int:
        return sum(1 for e in self._entries.values() if e.state == RumorState.KNOWN)

    @property
    def total_seen(self) -> int:
        return len(self._seen_ids)

    @property
    def entries(self) -> List[RumorEntry]:
        return list(self._entries.values())

    # -- internals -----------------------------------------------------------

    def _enforce_cap(self) -> None:
        """Evict oldest KNOWN entries if over max_entries."""
        if len(self._entries) <= self.max_entries:
            return
        known = [
            (mid, e) for mid, e in self._entries.items() if e.state == RumorState.KNOWN
        ]
        known.sort(key=lambda x: x[1].received_at)
        for mid, _ in known[: len(self._entries) - self.max_entries]:
            del self._entries[mid]
