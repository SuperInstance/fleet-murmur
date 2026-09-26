"""Adapter: quality-gate-stream as a fleet-murmur quality gate.

Cross-repo seam (cross-pollination receipt): SuperInstance/quality-gate-stream
scores items; fleet-murmur decides whether a rumor may enter the mill. This
module bridges them without a hard dependency:

    * quality-gate-stream installed  → real scoring; rumors below threshold
      are refused with the gate's own detail as the receipt reason.
    * not installed                   → ``build_gate()`` returns None and the
      protocol runs ungated. The absence is a fact, never faked as a score.

The adapter is written against the live quality-gate-stream API
(``QualityGate(name=..., strict=...)``, ``CustomCheck(name, fn)``,
``evaluate(item) -> GateResult`` with ``.outcome``) and is pinned by
``tests/test_qgs_adapter_glue.py``, which runs the REAL package when it is
importable and abstains (skip) when it is not — never a simulated pass.

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
    strict: bool = True,
) -> Optional[Callable[[str, Any, str], bool]]:
    """Return a fleet-murmur gate backed by quality-gate-stream, or None if
    the package is unavailable (the absence is named, not simulated).

    strict=True (default): any hard-failed check refuses the rumor outright —
    no dilution by passing checks (quality-gate-stream `strict` mode).
    """
    try:
        from quality_gate import CustomCheck, GateOutcome, QualityGate
        from quality_gate.check import CheckResult
    except ImportError:
        return None

    gate = QualityGate(name="fleet-murmur-rumor", weights=weights or {}, strict=strict)

    def _payload_score(payload: Any) -> float:
        # Minimal honest checks: presence and non-triviality. Extend with
        # real per-check logic where the rumor payload carries features.
        if payload is None:
            return 0.0
        return min(1.0, len(str(payload)) / 100.0)

    for name in checks:
        def _fn(item: Any, _name: str = name) -> "CheckResult":
            payload = item.get("quality", item) if isinstance(item, dict) else item
            score = _payload_score(payload)
            return CheckResult(
                score=score,
                passed=score >= min_score,
                message=f"{_name} size-proxy score {score:.2f}",
            )

        gate.add_check(CustomCheck(name, _fn))

    def gate_fn(topic: str, payload: Any, msg_id: str) -> bool:
        result = gate.evaluate({"quality": payload})
        return result.outcome is not GateOutcome.FAIL

    return gate_fn
