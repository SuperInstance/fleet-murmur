"""Adapter: quality-gate-stream as a fleet-murmur quality gate.

Cross-repo seam (cross-pollination receipt): SuperInstance/quality-gate-stream
scores items; fleet-murmur decides whether a rumor may enter the mill. This
module bridges them without a hard dependency:

    * quality-gate-stream installed  → real scoring; rumors below threshold
      are refused with the gate's own detail as the receipt reason.
    * not installed                   -> ``build_gate()`` returns None and the
      protocol runs ungated. The absence is a fact, never faked as a score.

Usage::

    from tools.quality_gate_adapter import build_gate
    gate = build_gate(min_score=0.5, checks=("novelty", "coherence"))
    gossip = GossipProtocol("agent-1", gate=gate)
"""

from __future__ import annotations

from typing import Any, Callable, Optional, Tuple


def build_gate(
    min_score: float = 0.5,
    checks: Tuple[str, ...] = ("novelty",),
    weights: Optional[dict] = None,
) -> Optional[Callable[[str, Any, str], bool]]:
    """Return a fleet-murmur gate backed by quality-gate-stream, or None if
    the package is unavailable (the absence is named, not simulated)."""
    try:
        from quality_gate import CheckResult, QualityGate
    except ImportError:
        return None

    gate = QualityGate(weights=weights)

    for name in checks:
        def _check(payload: Any, _name=name, _min=min_score) -> CheckResult:
            # Minimal honest checks: presence and non-triviality. Extend with
            # real per-check logic where the rumor payload carries features.
            if payload is None:
                return CheckResult(name=_name, passed=False, score=0.0,
                                   detail="empty payload")
            size = len(str(payload))
            score = min(1.0, size / 100.0)
            return CheckResult(name=_name, passed=score >= _min, score=score,
                               detail=f"size-proxy score {score:.2f}")

        gate.add_check(_check, name=name)

    def gate_fn(topic: str, payload: Any, msg_id: str) -> bool:
        report = gate.evaluate({"quality": payload})
        return report.passed

    return gate_fn
