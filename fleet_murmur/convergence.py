"""ConvergenceDetector — measures how well gossip has propagated."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from .message import MurmurMessage
from .peer import PeerManager
from .rumor import RumorMill


@dataclass
class ConvergenceSnapshot:
    """Point-in-time measurement of gossip convergence."""

    timestamp: float
    total_messages: int
    fully_propagated: int  # known by all peers
    average_coverage: float  # 0.0–1.0
    message_details: Dict[str, float] = field(default_factory=dict)


class ConvergenceDetector:
    """Measures gossip propagation completeness across the fleet.

    Each node reports which messages it has seen. The detector aggregates
    this into convergence metrics.
    """

    def __init__(self, peer_manager: PeerManager, cluster_size: int = 0) -> None:
        self.peer_manager = peer_manager
        self.cluster_size = max(cluster_size, 1)
        # msg_id -> set of node_ids that have seen it
        self._acknowledgments: Dict[str, Set[str]] = {}
        self._snapshots: List[ConvergenceSnapshot] = []

    # -- data collection -----------------------------------------------------

    def report_seen(self, node_id: str, msg_ids: List[str]) -> None:
        """Record that a node has seen the given message IDs."""
        for mid in msg_ids:
            self._acknowledgments.setdefault(mid, set()).add(node_id)

    def report_batch(self, reports: Dict[str, List[str]]) -> None:
        """Record multiple node→msg_ids reports at once."""
        for node_id, msg_ids in reports.items():
            self.report_seen(node_id, msg_ids)

    # -- measurement ---------------------------------------------------------

    def coverage(self, msg_id: str) -> float:
        """Fraction of cluster that has acknowledged this message."""
        acks = len(self._acknowledgments.get(msg_id, set()))
        return acks / self.cluster_size

    def is_converged(self, msg_id: str, threshold: float = 1.0) -> bool:
        """Return True if coverage >= threshold (default: all nodes)."""
        return self.coverage(msg_id) >= threshold

    def snapshot(self) -> ConvergenceSnapshot:
        """Take a convergence snapshot of all tracked messages."""
        if not self._acknowledgments:
            return ConvergenceSnapshot(
                timestamp=time.time(),
                total_messages=0,
                fully_propagated=0,
                average_coverage=0.0,
            )

        details: Dict[str, float] = {}
        fully = 0
        total_cov = 0.0

        for msg_id in self._acknowledgments:
            cov = self.coverage(msg_id)
            details[msg_id] = cov
            total_cov += cov
            if cov >= 1.0:
                fully += 1

        n = len(self._acknowledgments)
        snap = ConvergenceSnapshot(
            timestamp=time.time(),
            total_messages=n,
            fully_propagated=fully,
            average_coverage=total_cov / n if n else 0.0,
            message_details=details,
        )
        self._snapshots.append(snap)
        return snap

    # -- queries -------------------------------------------------------------

    @property
    def snapshots(self) -> List[ConvergenceSnapshot]:
        return list(self._snapshots)

    @property
    def tracked_messages(self) -> Set[str]:
        return set(self._acknowledgments.keys())

    def unacked_peers(self, msg_id: str) -> Set[str]:
        """Return peer IDs that haven't acknowledged a message."""
        acked = self._acknowledgments.get(msg_id, set())
        all_peers = {p.peer_id for p in self.peer_manager.all_peers}
        return all_peers - acked
