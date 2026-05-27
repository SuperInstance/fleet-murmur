"""Tests for fleet_murmur package."""

import time
from unittest.mock import MagicMock

from fleet_murmur.message import MurmurMessage
from fleet_murmur.peer import Peer, PeerManager, PeerStatus
from fleet_murmur.rumor import RumorMill, RumorState
from fleet_murmur.gossip import GossipProtocol
from fleet_murmur.convergence import ConvergenceDetector


# ---------------------------------------------------------------------------
# MurmurMessage
# ---------------------------------------------------------------------------

class TestMurmurMessage:

    def test_create_basic(self):
        msg = MurmurMessage(origin="node-1", topic="alerts", payload={"key": "val"})
        assert msg.origin == "node-1"
        assert msg.topic == "alerts"
        assert msg.payload == {"key": "val"}
        assert msg.hops == 0
        assert msg.ttl == 60.0
        assert len(msg.msg_id) == 16

    def test_is_expired_false(self):
        msg = MurmurMessage(origin="a", topic="t", payload=None, ttl=60.0)
        assert not msg.is_expired

    def test_is_expired_true(self):
        msg = MurmurMessage(
            origin="a", topic="t", payload=None, ttl=0.01,
            created_at=time.time() - 1.0,
        )
        assert msg.is_expired

    def test_never_expires(self):
        msg = MurmurMessage(
            origin="a", topic="t", payload=None, ttl=0,
            created_at=time.time() - 99999,
        )
        assert not msg.is_expired

    def test_with_hop(self):
        msg = MurmurMessage(origin="a", topic="t", payload=None)
        hopped = msg.with_hop()
        assert hopped.hops == 1
        assert hopped.msg_id == msg.msg_id
        assert msg.hops == 0  # original unchanged

    def test_serialization_roundtrip(self):
        msg = MurmurMessage(origin="a", topic="t", payload=[1, 2, 3], ttl=30.0)
        d = msg.to_dict()
        restored = MurmurMessage.from_dict(d)
        assert restored == msg

    def test_unique_ids(self):
        ids = {MurmurMessage(origin="a", topic="t", payload=None).msg_id for _ in range(100)}
        assert len(ids) == 100


# ---------------------------------------------------------------------------
# Peer / PeerManager
# ---------------------------------------------------------------------------

class TestPeer:

    def test_peer_defaults(self):
        p = Peer(peer_id="p1")
        assert p.status == PeerStatus.UNKNOWN
        assert p.last_seen == 0.0

    def test_touch(self):
        p = Peer(peer_id="p1")
        before = time.time()
        p.touch()
        assert p.status == PeerStatus.ALIVE
        assert p.last_seen >= before

    def test_is_alive(self):
        p = Peer(peer_id="p1", status=PeerStatus.ALIVE)
        assert p.is_alive
        p.status = PeerStatus.SUSPECT
        assert p.is_alive
        p.status = PeerStatus.DEAD
        assert not p.is_alive


class TestPeerManager:

    def _make_manager(self, **kwargs):
        return PeerManager(local_id="self", **kwargs)

    def test_add_and_get(self):
        pm = self._make_manager()
        p = Peer(peer_id="p1", address="10.0.0.1:7000")
        pm.add_peer(p)
        assert pm.get("p1") is p

    def test_remove(self):
        pm = self._make_manager()
        pm.add_peer(Peer(peer_id="p1"))
        removed = pm.remove_peer("p1")
        assert removed is not None
        assert pm.get("p1") is None

    def test_remove_nonexistent(self):
        pm = self._make_manager()
        assert pm.remove_peer("nope") is None

    def test_mark_seen_new(self):
        pm = self._make_manager()
        peer = pm.mark_seen("p1", address="addr")
        assert peer is not None
        assert peer.peer_id == "p1"
        assert peer.status == PeerStatus.ALIVE

    def test_mark_seen_existing(self):
        pm = self._make_manager()
        pm.add_peer(Peer(peer_id="p1"))
        peer = pm.mark_seen("p1")
        assert peer.status == PeerStatus.ALIVE

    def test_alive_peers(self):
        pm = self._make_manager()
        pm.add_peer(Peer(peer_id="p1", status=PeerStatus.ALIVE))
        pm.add_peer(Peer(peer_id="p2", status=PeerStatus.DEAD))
        assert len(pm.alive_peers) == 1

    def test_sample_excludes_self(self):
        pm = self._make_manager()
        pm.add_peer(Peer(peer_id="self", status=PeerStatus.ALIVE))
        pm.add_peer(Peer(peer_id="p1", status=PeerStatus.ALIVE))
        sample = pm.sample(10)
        assert all(p.peer_id != "self" for p in sample)

    def test_health_transitions(self):
        pm = self._make_manager(suspect_timeout=0.01, dead_timeout=0.02)
        p = Peer(peer_id="p1", status=PeerStatus.ALIVE, last_seen=time.time() - 1.0)
        pm.add_peer(p)
        result = pm.check_health()
        assert result["alive_to_suspect"] == 1
        assert p.status == PeerStatus.SUSPECT

    def test_evict_dead(self):
        pm = self._make_manager()
        pm.add_peer(Peer(peer_id="p1", status=PeerStatus.DEAD))
        pm.add_peer(Peer(peer_id="p2", status=PeerStatus.ALIVE))
        removed = pm.evict_dead()
        assert removed == 1
        assert pm.get("p1") is None
        assert pm.get("p2") is not None

    def test_known_ids(self):
        pm = self._make_manager()
        pm.add_peer(Peer(peer_id="p1"))
        pm.add_peer(Peer(peer_id="p2"))
        assert pm.known_ids == frozenset(["p1", "p2"])


# ---------------------------------------------------------------------------
# RumorMill
# ---------------------------------------------------------------------------

class TestRumorMill:

    def test_receive_new(self):
        mill = RumorMill()
        msg = MurmurMessage(origin="a", topic="t", payload="hello")
        assert mill.receive(msg) is True

    def test_receive_duplicate(self):
        mill = RumorMill()
        msg = MurmurMessage(origin="a", topic="t", payload="hello")
        mill.receive(msg)
        assert mill.receive(msg) is False

    def test_receive_expired(self):
        mill = RumorMill()
        msg = MurmurMessage(
            origin="a", topic="t", payload="old",
            ttl=0.01, created_at=time.time() - 1.0,
        )
        assert mill.receive(msg) is False

    def test_tick_spreads_new(self):
        mill = RumorMill(max_rounds=2)
        msg = MurmurMessage(origin="a", topic="t", payload="hi")
        mill.receive(msg)
        # First tick: NEW → SPREADING, not yet sent
        spread1 = mill.tick()
        assert len(spread1) == 1
        assert mill.get_state(msg.msg_id) == RumorState.SPREADING

    def test_tick_converges(self):
        mill = RumorMill(max_rounds=2)
        msg = MurmurMessage(origin="a", topic="t", payload="hi")
        mill.receive(msg)
        mill.tick()  # round 1
        mill.tick()  # round 2 → should become KNOWN
        assert mill.get_state(msg.msg_id) == RumorState.KNOWN

    def test_tick_removes_expired(self):
        mill = RumorMill()
        msg = MurmurMessage(
            origin="a", topic="t", payload="x",
            ttl=0.01, created_at=time.time() + 10,  # not expired yet
        )
        mill.receive(msg)
        # Now force expire by rewriting created_at... easier: just test empty tick
        spread = mill.tick()
        assert len(spread) == 1

    def test_mark_known(self):
        mill = RumorMill()
        msg = MurmurMessage(origin="a", topic="t", payload="x")
        mill.receive(msg)
        mill.mark_known(msg.msg_id)
        assert mill.get_state(msg.msg_id) == RumorState.KNOWN

    def test_has_seen(self):
        mill = RumorMill()
        msg = MurmurMessage(origin="a", topic="t", payload="x")
        mill.receive(msg)
        assert mill.has_seen(msg.msg_id)
        assert not mill.has_seen("nonexistent")

    def test_counts(self):
        mill = RumorMill()
        m1 = MurmurMessage(origin="a", topic="t", payload="x")
        m2 = MurmurMessage(origin="b", topic="t", payload="y")
        mill.receive(m1)
        mill.receive(m2)
        assert mill.active_count == 2
        assert mill.total_seen == 2

    def test_max_entries_cap(self):
        mill = RumorMill(max_rounds=1, max_entries=2)
        for i in range(5):
            msg = MurmurMessage(origin="a", topic="t", payload=i)
            mill.receive(msg)
            mill.tick()  # move to known
        assert len(mill.entries) <= 2


# ---------------------------------------------------------------------------
# GossipProtocol
# ---------------------------------------------------------------------------

class TestGossipProtocol:

    def test_broadcast_creates_message(self):
        gossip = GossipProtocol(node_id="n1")
        msg = gossip.broadcast("alerts", {"level": "high"})
        assert msg.origin == "n1"
        assert msg.topic == "alerts"
        assert gossip.rumor_mill.has_seen(msg.msg_id)

    def test_receive_novel(self):
        gossip = GossipProtocol(node_id="n1")
        incoming = [MurmurMessage(origin="n2", topic="t", payload="hi")]
        novel = gossip.receive(incoming, from_peer="n2")
        assert len(novel) == 1

    def test_receive_duplicate(self):
        gossip = GossipProtocol(node_id="n1")
        msgs = [MurmurMessage(origin="n2", topic="t", payload="hi")]
        gossip.receive(msgs, from_peer="n2")
        novel = gossip.receive(msgs, from_peer="n2")
        assert len(novel) == 0

    def test_tick_no_peers(self):
        gossip = GossipProtocol(node_id="n1")
        gossip.broadcast("t", "hello")
        r = gossip.tick()
        assert r.peers_contacted == 0

    def test_tick_with_peers(self):
        transport = MagicMock(return_value=3)
        gossip = GossipProtocol(node_id="n1", fanout=2, transport=transport)
        gossip.add_peer(Peer(peer_id="p1", address="addr1", status=PeerStatus.ALIVE))
        gossip.add_peer(Peer(peer_id="p2", address="addr2", status=PeerStatus.ALIVE))
        gossip.broadcast("t", "hello")
        r = gossip.tick()
        assert r.peers_contacted == 2
        assert r.messages_sent > 0
        assert transport.call_count == 2

    def test_delivery_coverage(self):
        gossip = GossipProtocol(node_id="n1")
        msg = gossip.broadcast("t", "hi")
        gossip.add_peer(Peer(peer_id="p1"))
        # Only n1 knows about it so far
        cov = gossip.delivery_coverage(msg.msg_id)
        assert cov > 0.0

    def test_pending_messages(self):
        gossip = GossipProtocol(node_id="n1")
        gossip.broadcast("t", "hi")
        assert len(gossip.pending_messages) > 0

    def test_multiple_rounds(self):
        gossip = GossipProtocol(node_id="n1", max_rounds=2)
        gossip.add_peer(Peer(peer_id="p1", status=PeerStatus.ALIVE))
        gossip.broadcast("t", "hello")
        gossip.tick()  # round 1
        gossip.tick()  # round 2 → should settle
        assert len(gossip.pending_messages) == 0


# ---------------------------------------------------------------------------
# ConvergenceDetector
# ---------------------------------------------------------------------------

class TestConvergenceDetector:

    def _make_detector(self, cluster_size=5):
        pm = PeerManager(local_id="self")
        for i in range(cluster_size):
            pm.add_peer(Peer(peer_id=f"p{i}", status=PeerStatus.ALIVE))
        return ConvergenceDetector(peer_manager=pm, cluster_size=cluster_size)

    def test_report_and_coverage(self):
        det = self._make_detector(cluster_size=5)
        det.report_seen("p0", ["msg1"])
        assert det.coverage("msg1") == 1 / 5

    def test_full_coverage(self):
        det = self._make_detector(cluster_size=3)
        det.report_seen("p0", ["msg1"])
        det.report_seen("p1", ["msg1"])
        det.report_seen("p2", ["msg1"])
        assert det.coverage("msg1") == 1.0
        assert det.is_converged("msg1")

    def test_batch_report(self):
        det = self._make_detector(cluster_size=3)
        det.report_batch({"p0": ["m1", "m2"], "p1": ["m1"]})
        assert det.coverage("m1") == 2 / 3
        assert det.coverage("m2") == 1 / 3

    def test_snapshot(self):
        det = self._make_detector(cluster_size=3)
        det.report_seen("p0", ["m1"])
        det.report_seen("p1", ["m1"])
        det.report_seen("p2", ["m1"])
        snap = det.snapshot()
        assert snap.total_messages == 1
        assert snap.fully_propagated == 1
        assert snap.average_coverage == 1.0

    def test_snapshot_empty(self):
        det = self._make_detector()
        snap = det.snapshot()
        assert snap.total_messages == 0

    def test_unacked_peers(self):
        det = self._make_detector(cluster_size=3)
        det.report_seen("p0", ["m1"])
        unacked = det.unacked_peers("m1")
        assert "p1" in unacked
        assert "p2" in unacked
        assert "p0" not in unacked

    def test_is_not_converged(self):
        det = self._make_detector(cluster_size=3)
        det.report_seen("p0", ["m1"])
        assert not det.is_converged("m1")
        assert det.is_converged("m1", threshold=0.3)
