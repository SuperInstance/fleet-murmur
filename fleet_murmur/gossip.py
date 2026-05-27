"""GossipProtocol — rumor-mongering over a peer mesh."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Set

from .message import MurmurMessage
from .peer import PeerManager
from .rumor import RumorMill, RumorState


@dataclass
class GossipRound:
    """Record of a single gossip round for observability."""

    round_number: int
    messages_sent: int
    peers_contacted: int
    timestamp: float = field(default_factory=time.time)


class GossipProtocol:
    """A push-based gossip protocol for fleet communication.

    Usage::

        gossip = GossipProtocol(node_id="agent-1")
        gossip.add_peer(Peer(peer_id="agent-2", address="10.0.0.2:7000"))
        gossip.broadcast("alerts", {"level": "critical", "msg": "disk full"})
        gossip.tick()  # spreads pending messages to random peers
    """

    def __init__(
        self,
        node_id: str,
        fanout: int = 3,
        max_rounds: int = 3,
        transport: Optional[Callable[[str, List[MurmurMessage]], int]] = None,
    ) -> None:
        self.node_id = node_id
        self.fanout = fanout
        self.peer_manager = PeerManager(local_id=node_id)
        self.rumor_mill = RumorMill(max_rounds=max_rounds)
        self._transport = transport  # Optional hook: (peer_addr, messages) -> count_sent
        self._round_counter = 0
        self._history: List[GossipRound] = []
        self._delivery_log: Dict[str, Set[str]] = {}  # msg_id -> set of peer_ids delivered to

    # -- public API ----------------------------------------------------------

    def broadcast(self, topic: str, payload: object, ttl: float = 60.0) -> MurmurMessage:
        """Create and inject a new message into the rumor mill."""
        msg = MurmurMessage(origin=self.node_id, topic=topic, payload=payload, ttl=ttl)
        self.rumor_mill.receive(msg)
        self._delivery_log.setdefault(msg.msg_id, set()).add(self.node_id)
        return msg

    def receive(self, messages: List[MurmurMessage], from_peer: Optional[str] = None) -> List[MurmurMessage]:
        """Process incoming messages from a peer. Returns list of novel messages."""
        novel: List[MurmurMessage] = []
        for msg in messages:
            if self.rumor_mill.receive(msg):
                novel.append(msg)
                self._delivery_log.setdefault(msg.msg_id, set()).add(self.node_id)
        if from_peer:
            self.peer_manager.mark_seen(from_peer)
        return novel

    def tick(self) -> GossipRound:
        """Run one gossip round: spread pending messages to random peers."""
        self._round_counter += 1
        to_spread = self.rumor_mill.tick()

        if not to_spread:
            return GossipRound(
                round_number=self._round_counter,
                messages_sent=0,
                peers_contacted=0,
            )

        # Pick fanout peers
        targets = self.peer_manager.sample(self.fanout)
        sent = 0
        contacted = 0

        for peer in targets:
            # Increment hop count for outgoing
            outgoing = [m.with_hop() for m in to_spread]
            if self._transport:
                n = self._transport(peer.address, outgoing)
                sent += n
            else:
                sent += len(outgoing)
            contacted += 1
            self._delivery_log  # just access to keep it alive
            for m in to_spread:
                self._delivery_log.setdefault(m.msg_id, set()).add(peer.peer_id)

        round_record = GossipRound(
            round_number=self._round_counter,
            messages_sent=sent,
            peers_contacted=contacted,
        )
        self._history.append(round_record)
        return round_record

    def add_peer(self, peer: "Peer") -> None:  # noqa: F821
        """Convenience: add a peer to the manager."""
        self.peer_manager.add_peer(peer)

    # -- queries -------------------------------------------------------------

    @property
    def pending_messages(self) -> List[MurmurMessage]:
        """Messages still being gossiped."""
        return [e.message for e in self.rumor_mill.entries if e.state in (RumorState.NEW, RumorState.SPREADING)]

    def delivery_coverage(self, msg_id: str) -> float:
        """Fraction of known peers that have seen this message (0.0–1.0)."""
        peers_who_know = self._delivery_log.get(msg_id, set())
        total = len(self.peer_manager.all_peers) + 1  # +1 for self
        if total == 0:
            return 0.0
        return len(peers_who_know) / total

    @property
    def round_history(self) -> List[GossipRound]:
        return list(self._history)
