"""Glue pins: tools/quality_gate_adapter.py against the REAL quality-gate-stream.

FAIL-first: on pristine main the adapter calls a stale quality-gate-stream API
(add_check(name=...), report.passed), so every live pin below is RED there.
Live pins import the real SuperInstance/quality-gate-stream package; when it
is not importable they SKIP (honest abstention, never a simulated pass).
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from tools.quality_gate_adapter import build_gate  # noqa: E402


def _require_qgs():
    """Import the real quality-gate-stream or skip this live pin (honest
    abstention — never a simulated pass)."""
    return pytest.importorskip(
        "quality_gate",
        reason="quality-gate-stream not installed — live pin abstains",
    )


def test_adapter_returns_callable_with_real_qgs():
    _require_qgs()
    gate = build_gate()
    assert callable(gate), "with quality-gate-stream importable, build_gate must return a gate"


def test_empty_payload_refused_real_scoring():
    _require_qgs()
    gate = build_gate(min_score=0.5, checks=("novelty",))
    assert gate("alerts", None, "msg-1") is False
    assert gate("alerts", "", "msg-2") is False


def test_nontrivial_payload_passes_real_scoring():
    _require_qgs()
    gate = build_gate(min_score=0.5, checks=("novelty",))
    assert gate("alerts", {"level": "critical", "msg": "disk full on node agent-7"}, "msg-3") is True


def test_refused_rumor_leaves_refusal_receipt_not_spread():
    _require_qgs()
    from fleet_murmur.gossip import GossipProtocol
    from fleet_murmur.ledger import MurmurLedger

    ledger = MurmurLedger(REPO / "tests" / "tmp-qgs-glue-ledger.jsonl")
    try:
        gossip = GossipProtocol("agent-1", gate=build_gate(min_score=0.5), ledger=ledger)
        refused = gossip.broadcast("alerts", None)
        assert refused is None, "refused rumor must not enter the mill"
        accepted = gossip.broadcast("alerts", {"level": "critical", "msg": "disk full on node agent-7"})
        assert accepted is not None, "passing rumor must enter the mill"
        refusals = [r for r in ledger.replay() if r.get("event") == "REFUSE"]
        assert len(refusals) == 1 and refusals[0].get("mode") == "REFUSED"
        assert refusals[0].get("msg_id") != accepted.msg_id, (
            "the refusal receipt must name the refused rumor, not the accepted one"
        )
    finally:
        p = REPO / "tests" / "tmp-qgs-glue-ledger.jsonl"
        if p.exists():
            p.unlink()


def test_absence_returns_none_never_faked(monkeypatch):
    monkeypatch.setitem(sys.modules, "quality_gate", None)
    monkeypatch.setitem(sys.modules, "quality_gate.check", None)
    assert build_gate() is None, "missing dependency must abstain as None, not fake a score"


def test_adapter_names_source_repo():
    src = (REPO / "tools" / "quality_gate_adapter.py").read_text()
    assert "SuperInstance/quality-gate-stream" in src, (
        "weight law: the seam must name its source repo, not absorb it silently"
    )
