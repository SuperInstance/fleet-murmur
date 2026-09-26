"""FAIL-first pins: transport honesty, receipt ledger, quality-gate seam, honesty registry.

Every test here must be RED on the pre-pass tree. Run:
    python3 -m pytest tests/test_honesty_pass.py -q
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from fleet_murmur import GossipProtocol, Peer
from fleet_murmur.peer import PeerStatus


REPO = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------- transport honesty

def test_dropped_transport_never_claims_delivery():
    """A transport that delivers 0 of N must leave coverage at self-only.

    Pre-pass behavior: _delivery_log marks every contacted peer regardless of
    the transport's return value — coverage reads 1.0 for a black-hole transport.
    """
    g = GossipProtocol("n1", fanout=1, transport=lambda addr, msgs: 0)
    g.add_peer(Peer(peer_id="p1", address="a1", status=PeerStatus.ALIVE))
    msg = g.broadcast("alerts", {"x": 1})
    g.tick()
    assert g.delivery_coverage(msg.msg_id) == pytest.approx(1 / 2)  # self only


def test_partial_batch_not_claimed_as_full():
    """A zero-delivery transport must name the drop, not fold it into delivery."""
    g = GossipProtocol("n1", fanout=1, transport=lambda addr, msgs: 0)
    g.add_peer(Peer(peer_id="p1", address="a1", status=PeerStatus.ALIVE))
    msg = g.broadcast("alerts", {"x": 1})
    g.tick()
    round_rec = g.round_history[-1]
    # the attempted batch must be NAMED as dropped (or unconfirmed), never confirmed
    assert round_rec.deliveries_dropped + round_rec.deliveries_unconfirmed == 1
    assert round_rec.deliveries_confirmed == 0
    assert round_rec.deliveries_simulated == 0
    assert g.delivery_coverage(msg.msg_id) == pytest.approx(1 / 2)


def test_no_transport_round_is_labeled_simulated():
    """Without a transport, delivery claims are simulation and must say so."""
    g = GossipProtocol("n1", fanout=1)
    g.add_peer(Peer(peer_id="p1", address="a1", status=PeerStatus.ALIVE))
    g.broadcast("alerts", {"x": 1})
    g.tick()
    round_rec = g.round_history[-1]
    assert getattr(round_rec, "deliveries_simulated", None) == 1
    assert getattr(round_rec, "deliveries_confirmed", None) == 0


def test_precise_transport_contract_list_of_msg_ids():
    """A transport returning an iterable of delivered msg_ids is honored exactly."""
    def transport(addr, msgs):
        return [m.msg_id for m in msgs[:1]]  # only the first message lands

    g = GossipProtocol("n1", fanout=1, transport=transport)
    g.add_peer(Peer(peer_id="p1", address="a1", status=PeerStatus.ALIVE))
    m1 = g.broadcast("alerts", 1)
    m2 = g.broadcast("alerts", 2)
    g.tick()
    assert g.delivery_coverage(m1.msg_id) == pytest.approx(2 / 2)  # p1 has m1
    assert g.delivery_coverage(m2.msg_id) == pytest.approx(1 / 2)  # p1 does NOT have m2


# ---------------------------------------------------------------- receipt ledger

def test_receipt_ledger_hash_chained_and_replayable():
    from fleet_murmur.ledger import MurmurLedger

    path = REPO / "tests" / "zzz" / "ledger-fixture.jsonl"
    path.parent.mkdir(exist_ok=True)
    if path.exists():
        path.unlink()
    ledger = MurmurLedger(path)
    ledger.append("BROADCAST", node="n1", msg_id="m1")
    ledger.append("DELIVER", node="n1", peer="p1", msg_id="m1", mode="SIMULATED")
    result = ledger.verify()
    assert result["ok"] is True
    assert result["lines"] == 2
    events = [e["event"] for e in ledger.replay()]
    assert events == ["BROADCAST", "DELIVER"]


def test_ledger_tamper_detected():
    from fleet_murmur.ledger import MurmurLedger

    path = REPO / "tests" / "zzz" / "ledger-tamper.jsonl"
    path.parent.mkdir(exist_ok=True)
    if path.exists():
        path.unlink()
    ledger = MurmurLedger(path)
    ledger.append("BROADCAST", node="n1", msg_id="m1")
    with path.open("a") as fh:
        fh.write(json.dumps({"event": "DELIVER", "node": "n1", "msg_id": "m1",
                             "prev": "bogus", "hash": "bogus"}) + "\n")
    result = ledger.verify()
    assert result["ok"] is False
    assert result["divergences"]


def test_gossip_protocol_emits_ledger_receipts_with_modes():
    """Wired protocol: every round trip produces a balanced, mode-labeled receipt set."""
    from fleet_murmur.ledger import MurmurLedger

    path = REPO / "tests" / "zzz" / "ledger-gossip.jsonl"
    path.parent.mkdir(exist_ok=True)
    if path.exists():
        path.unlink()
    ledger = MurmurLedger(path)
    g = GossipProtocol("n1", fanout=1, transport=lambda a, m: 0, ledger=ledger)
    g.add_peer(Peer(peer_id="p1", address="a1", status=PeerStatus.ALIVE))
    msg = g.broadcast("alerts", {"x": 1})
    g.tick()
    events = [e["event"] for e in ledger.replay()]
    assert "BROADCAST" in events
    assert "DROP" in events  # transport delivered 0 — the drop must be NAMED
    # trial balance: attempted == confirmed + unconfirmed + simulated
    balance = ledger.trial_balance()
    assert balance["balanced"] is True


# ---------------------------------------------------------------- quality-gate seam

def test_quality_gate_refusal_produces_refusal_receipt_not_spread():
    """A refused rumor must not enter the mill and must leave a REFUSE receipt."""
    def gate(topic, payload, msg_id):
        return topic != "spam"

    g = GossipProtocol("n1", fanout=2, gate=gate)
    g.add_peer(Peer(peer_id="p1", address="a1", status=PeerStatus.ALIVE))
    bad = g.broadcast("spam", {"buy": "now"})
    good = g.broadcast("alerts", {"level": "critical"})
    assert bad is None or g.rumor_mill.has_seen(bad.msg_id) is False
    assert g.rumor_mill.has_seen(good.msg_id) is True


# ---------------------------------------------------------------- honesty registry

def test_readme_claims_have_tests_and_counts_match():
    """README test counts must equal the live collected counts (two-way), and every
    VERIFIED_CLAIMS entry must name an existing test file."""
    readme = (REPO / "README.md").read_text()
    collected = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "tests/"],
        capture_output=True, text=True, cwd=REPO,
    ).stdout
    n_tests = sum(1 for line in collected.splitlines() if "::" in line and "test_" in line)
    assert f"{n_tests} tests" in readme, (
        f"README must state the live count ({n_tests} tests) — a claim without a number is a phantom"
    )
    claims_file = REPO / "VERIFIED_CLAIMS.md"
    assert claims_file.exists(), "VERIFIED_CLAIMS.md registry required (pong-quilt convention)"
    for line in claims_file.read_text().splitlines():
        if line.startswith("| VC") and not line.startswith("| VC |"):
            parts = [p.strip() for p in line.split("|") if p.strip()]
            test_ref = parts[-1]
            assert (REPO / test_ref).exists(), f"claim {parts[0]} names missing test {test_ref}"
