"""GossipProtocol — rumor-mongering over a peer mesh.

Transport honesty contract (receipts discipline):
    * transport returns ``None``           → simulation; every delivery is
      recorded mode=SIMULATED and the round says so.
    * transport returns an ``int`` n       → legacy count contract; n >= batch
      confirms the whole batch (mode=CONFIRMED); n < batch confirms nothing
      about *which* messages landed — n stay UNCONFIRMED, the rest are DROPS.
    * transport returns an iterable of msg_ids → precise contract; exactly those
      messages are CONFIRMED, the rest are named DROPS.

A delivery is never recorded without a mode naming how we know.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple, Union

from .ledger import MurmurLedger
from .message import MurmurMessage
from .peer import PeerManager
from .rumor import RumorMill, RumorState

TransportResult = Union[int, Iterable[str], None]
Transport = Callable[[str, List[MurmurMessage]], TransportResult]
Gate = Callable[[str, Any, str], bool]


@dataclass
class GossipRound:
    """Record of a single gossip round for observability.

    deliveries_* fields name how each outcome is known (transport honesty):
    confirmed = transport affirmed, simulated = no transport (model, not
    measurement), unconfirmed = partial batch whose landing set is unknown,
    dropped = attempted and reported not-delivered.
    """

    round_number: int
    messages_sent: int
    peers_contacted: int
    deliveries_confirmed: int = 0
    deliveries_simulated: int = 0
    deliveries_unconfirmed: int = 0
    deliveries_dropped: int = 0
    timestamp: float = field(default_factory=time.time)


class GossipProtocol:
    """A push-based gossip protocol for fleet communication.

    Usage::

        gossip = GossipProtocol(node_id="agent-1")
        gossip.add_peer(Peer(peer_id="agent-2", address="10.0.0.2:7000",
                            status=PeerStatus.ALIVE))
        gossip.broadcast("alerts", {"level": "critical", "msg": "disk full"})
        gossip.tick()  # spreads pending messages to random peers

    Optional wiring:
        ledger=MurmurLedger(path)   hash-chained receipt ledger (every event)
        gate=callable(topic, payload, msg_id) -> bool
                                    quality-gate seam; refused rumors leave a
                                    REFUSE receipt and never enter the mill
        transport=callable(addr, messages) -> int | iterable-of-msg_ids | None
                                    measurement hook; honesty contract above
    """

    def __init__(
        self,
        node_id: str,
        fanout: int = 3,
        max_rounds: int = 3,
        transport: Optional[Transport] = None,
        ledger: Optional[MurmurLedger] = None,
        gate: Optional[Gate] = None,
    ) -> None:
        self.node_id = node_id
        self.fanout = fanout
        self.peer_manager = PeerManager(local_id=node_id)
        self.rumor_mill = RumorMill(max_rounds=max_rounds)
        self._transport = transport
        self._ledger = ledger
        self._gate = gate
        self._round_counter = 0
        self._history: List[GossipRound] = []
        self._delivery_log: Dict[str, Set[str]] = {}  # msg_id -> peer_ids confirmed/simulated to hold it

    # -- public API ----------------------------------------------------------

    def broadcast(self, topic: str, payload: object, ttl: float = 60.0) -> Optional[MurmurMessage]:
        """Create and inject a new message into the rumor mill.

        Returns None (with a REFUSE receipt) if the quality gate rejects it.
        """
        probe = MurmurMessage(origin=self.node_id, topic=topic, payload=payload, ttl=ttl)
        if self._gate is not None and not self._gate(topic, payload, probe.msg_id):
            self._receipt("REFUSE", node=self.node_id, msg_id=probe.msg_id,
                          topic=topic, mode="REFUSED", count=1)
            return None
        self.rumor_mill.receive(probe)
        self._delivery_log.setdefault(probe.msg_id, set()).add(self.node_id)
        self._receipt("BROADCAST", node=self.node_id, msg_id=probe.msg_id, topic=topic)
        return probe

    def receive(self, messages: List[MurmurMessage], from_peer: Optional[str] = None) -> List[MurmurMessage]:
        """Process incoming messages from a peer. Returns list of novel messages."""
        novel: List[MurmurMessage] = []
        for msg in messages:
            if self._gate is not None and not self._gate(msg.topic, msg.payload, msg.msg_id):
                self._receipt("REFUSE", node=self.node_id, msg_id=msg.msg_id,
                              topic=msg.topic, mode="REFUSED", count=1)
                continue
            if self.rumor_mill.receive(msg):
                novel.append(msg)
                self._delivery_log.setdefault(msg.msg_id, set()).add(self.node_id)
                self._receipt("RECEIVE", node=self.node_id, msg_id=msg.msg_id,
                              topic=msg.topic, from_peer=from_peer)
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

        targets = self.peer_manager.sample(self.fanout)
        sent = 0
        contacted = 0
        confirmed = simulated = unconfirmed = dropped = 0

        for peer in targets:
            outgoing = [m.with_hop() for m in to_spread]
            self._receipt("SPREAD", node=self.node_id, peer=peer.peer_id,
                          count=len(outgoing),
                          msg_ids=[m.msg_id for m in outgoing])
            delivered: Set[str] = set()

            if self._transport is None:
                # Simulation: the model delivers everything, and says so.
                simulated += len(outgoing)
                delivered = {m.msg_id for m in outgoing}
                self._receipt("DELIVER", node=self.node_id, peer=peer.peer_id,
                              mode="SIMULATED", count=len(outgoing),
                              msg_ids=[m.msg_id for m in outgoing])
                sent += len(outgoing)
            else:
                result = self._transport(peer.address, outgoing)
                if result is None:
                    # Legacy transport with no return: delivery unknown.
                    unconfirmed += len(outgoing)
                    self._receipt("UNCONFIRMED", node=self.node_id, peer=peer.peer_id,
                                  count=len(outgoing),
                                  msg_ids=[m.msg_id for m in outgoing])
                    sent += len(outgoing)
                elif isinstance(result, int):
                    if result >= len(outgoing):
                        confirmed += len(outgoing)
                        delivered = {m.msg_id for m in outgoing}
                        self._receipt("DELIVER", node=self.node_id, peer=peer.peer_id,
                                      mode="CONFIRMED", count=len(outgoing),
                                      msg_ids=[m.msg_id for m in outgoing])
                    elif result <= 0:
                        dropped += len(outgoing)
                        self._receipt("DROP", node=self.node_id, peer=peer.peer_id,
                                      count=len(outgoing),
                                      msg_ids=[m.msg_id for m in outgoing])
                    else:
                        confirmed += result
                        unconfirmed += len(outgoing) - result
                        self._receipt("DELIVER", node=self.node_id, peer=peer.peer_id,
                                      mode="CONFIRMED", count=result)
                        self._receipt("UNCONFIRMED", node=self.node_id, peer=peer.peer_id,
                                      count=len(outgoing) - result)
                    sent += result
                else:
                    ids = set(result)
                    landed = [m for m in outgoing if m.msg_id in ids]
                    lost = [m for m in outgoing if m.msg_id not in ids]
                    confirmed += len(landed)
                    dropped += len(lost)
                    delivered = ids & {m.msg_id for m in outgoing}
                    if landed:
                        self._receipt("DELIVER", node=self.node_id, peer=peer.peer_id,
                                      mode="CONFIRMED", count=len(landed),
                                      msg_ids=[m.msg_id for m in landed])
                    if lost:
                        self._receipt("DROP", node=self.node_id, peer=peer.peer_id,
                                      count=len(lost),
                                      msg_ids=[m.msg_id for m in lost])
                    sent += len(landed)

            for msg_id in delivered:
                self._delivery_log.setdefault(msg_id, set()).add(peer.peer_id)
            contacted += 1

        round_record = GossipRound(
            round_number=self._round_counter,
            messages_sent=sent,
            peers_contacted=contacted,
            deliveries_confirmed=confirmed,
            deliveries_simulated=simulated,
            deliveries_unconfirmed=unconfirmed,
            deliveries_dropped=dropped,
        )
        self._history.append(round_record)
        return round_record

    def add_peer(self, peer: "Peer") -> None:  # noqa: F821
        """Convenience: add a peer to the manager.

        Note: only ALIVE/SUSPECT peers are sampled — a fresh Peer defaults to
        UNKNOWN (unsuspicious but unproven) and is not gossiped to until it is
        seen. This mirrors fleet suspicion doctrine.
        """
        self.peer_manager.add_peer(peer)

    # -- queries -------------------------------------------------------------

    @property
    def pending_messages(self) -> List[MurmurMessage]:
        """Messages still being gossiped."""
        return [e.message for e in self.rumor_mill.entries if e.state in (RumorState.NEW, RumorState.SPREADING)]

    def delivery_coverage(self, msg_id: str) -> float:
        """Fraction of known peers confirmed/simulated to hold this message (0.0–1.0).

        Unconfirmed partials are NOT counted — coverage admits its gaps.
        """
        peers_who_know = self._delivery_log.get(msg_id, set())
        total = len(self.peer_manager.all_peers) + 1  # +1 for self
        if total == 0:
            return 0.0
        return len(peers_who_know) / total

    @property
    def round_history(self) -> List[GossipRound]:
        return list(self._history)

    # -- internals -----------------------------------------------------------

    def _receipt(self, event: str, **fields: Any) -> None:
        if self._ledger is not None:
            self._ledger.append(event, **fields)
