"""Peer — representation of a fleet node and PeerManager to track them."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, FrozenSet, List, Optional, Set


class PeerStatus(Enum):
    """Health status of a peer."""

    ALIVE = "alive"
    SUSPECT = "suspect"
    DEAD = "dead"
    UNKNOWN = "unknown"


@dataclass
class Peer:
    """A single peer in the fleet.

    Attributes:
        peer_id:    Unique identifier for this peer.
        address:    Network address (host:port or similar).
        status:     Current liveness status.
        last_seen:  Epoch seconds of last successful contact.
        metadata:   Arbitrary key/value metadata.
    """

    peer_id: str
    address: str = ""
    status: PeerStatus = PeerStatus.UNKNOWN
    last_seen: float = 0.0
    metadata: Dict[str, str] = field(default_factory=dict)

    def touch(self) -> None:
        """Mark the peer as seen right now with ALIVE status."""
        self.last_seen = time.time()
        self.status = PeerStatus.ALIVE

    @property
    def is_alive(self) -> bool:
        return self.status in (PeerStatus.ALIVE, PeerStatus.SUSPECT)


class PeerManager:
    """Tracks known peers and their health for a gossip node.

    Supports adding, removing, and querying peers, as well as evicting
    peers that haven't been seen within a configurable grace period.
    """

    def __init__(self, local_id: str, suspect_timeout: float = 30.0, dead_timeout: float = 120.0) -> None:
        self.local_id = local_id
        self._peers: Dict[str, Peer] = {}
        self.suspect_timeout = suspect_timeout
        self.dead_timeout = dead_timeout

    # -- mutators ------------------------------------------------------------

    def add_peer(self, peer: Peer) -> None:
        """Register a peer (overwrites if already present)."""
        self._peers[peer.peer_id] = peer

    def remove_peer(self, peer_id: str) -> Optional[Peer]:
        """Remove and return a peer by ID, or None."""
        return self._peers.pop(peer_id, None)

    def mark_seen(self, peer_id: str, address: str = "") -> Optional[Peer]:
        """Mark a peer as recently seen. Adds it if unknown."""
        peer = self._peers.get(peer_id)
        if peer is None:
            peer = Peer(peer_id=peer_id, address=address)
            self._peers[peer_id] = peer
        peer.touch()
        if address and not peer.address:
            peer.address = address
        return peer

    # -- queries -------------------------------------------------------------

    def get(self, peer_id: str) -> Optional[Peer]:
        return self._peers.get(peer_id)

    @property
    def all_peers(self) -> List[Peer]:
        return list(self._peers.values())

    @property
    def alive_peers(self) -> List[Peer]:
        return [p for p in self._peers.values() if p.is_alive]

    @property
    def known_ids(self) -> FrozenSet[str]:
        return frozenset(self._peers.keys())

    def sample(self, count: int, exclude: Optional[Set[str]] = None) -> List[Peer]:
        """Return up to *count* random alive peers, excluding self and *exclude*."""
        exclude = exclude or set()
        exclude.add(self.local_id)
        candidates = [p for p in self._peers.values() if p.peer_id not in exclude and p.is_alive]
        # Deterministic but shuffled via sorted key on peer_id for reproducibility
        return sorted(candidates, key=lambda p: p.peer_id)[:count]

    # -- maintenance ---------------------------------------------------------

    def check_health(self) -> Dict[str, int]:
        """Transition peer statuses based on timeouts. Returns count transitions."""
        now = time.time()
        transitions: Dict[str, int] = {"alive_to_suspect": 0, "suspect_to_dead": 0}

        for peer in self._peers.values():
            if peer.status == PeerStatus.ALIVE:
                if (now - peer.last_seen) > self.suspect_timeout:
                    peer.status = PeerStatus.SUSPECT
                    transitions["alive_to_suspect"] += 1
            elif peer.status == PeerStatus.SUSPECT:
                if (now - peer.last_seen) > self.dead_timeout:
                    peer.status = PeerStatus.DEAD
                    transitions["suspect_to_dead"] += 1

        return transitions

    def evict_dead(self) -> int:
        """Remove all DEAD peers. Returns count removed."""
        dead = [pid for pid, p in self._peers.items() if p.status == PeerStatus.DEAD]
        for pid in dead:
            del self._peers[pid]
        return len(dead)
