"""MurmurLedger — hash-chained receipt ledger for gossip events.

Every meaningful event in a node's gossip life (broadcast, receive, spread,
delivery, drop, expiry, refusal) is appended as one JSONL row carrying an
fnv1a hash chain. The chain is integrity, not security — same posture as
hermit's quilt-wal (P1) and the pong-quilt session WAL: anyone holding the
file can replay it and detect tamper or truncation, and a second node can
diff two ledgers to find where their views of history diverged.

Mode vocabulary (transport honesty — a receipt must name how it knows):
    CONFIRMED   the transport reported this delivery
    SIMULATED   no transport wired; delivery is a model, not a measurement
    UNCONFIRMED the transport reported a partial/unknown batch remainder
    REFUSED     quality gate rejected the rumor; nothing was spread
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


def fnv1a(text: str, seed: int = 0x811C9DC5) -> str:
    """32-bit fnv1a hash, hex-encoded — chain algorithm shared with the fleet's
    rate limiter and hermit's quilt-wal so one verifier reads every ledger."""
    h = seed
    for ch in text:
        h ^= ord(ch)
        h = (h * 0x01000193) & 0xFFFFFFFF
    return f"{h:08x}"


class MurmurLedger:
    """Append-only JSONL receipt ledger with fnv1a hash chain.

    Usage::

        ledger = MurmurLedger("~/.fleet-murmur/ledger.jsonl")
        ledger.append("BROADCAST", node="n1", msg_id="m1")
        result = ledger.verify()   # {"ok": True, "divergences": [], "lines": 1}
        events = ledger.replay()   # list of event dicts, chain-checked
    """

    def __init__(self, path: Union[str, Path]) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    # -- core ---------------------------------------------------------------

    def append(self, event: str, **fields: Any) -> Dict[str, Any]:
        """Append one receipt. Returns the stored row (with chain hashes)."""
        prev = self._last_hash()
        row = {
            "event": event,
            "ts": time.time(),
            "prev": prev,
            **fields,
        }
        row["hash"] = fnv1a(self._canonical(row))
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, sort_keys=True, default=str) + "\n")
        return row

    def verify(self) -> Dict[str, Any]:
        """Replay the chain; report tamper, truncation, or divergence."""
        divergences: List[Dict[str, Any]] = []
        expected_prev = "GENESIS"
        lines = 0
        for lineno, row in self._rows():
            lines = lineno
            if row.get("prev") != expected_prev:
                divergences.append({
                    "line": lineno,
                    "kind": "prev-mismatch",
                    "expected": expected_prev,
                    "found": row.get("prev"),
                })
                continue
            recomputed = fnv1a(self._canonical(row))
            if row.get("hash") != recomputed:
                divergences.append({
                    "line": lineno,
                    "kind": "hash-mismatch",
                    "event": row.get("event"),
                })
                continue
            expected_prev = row["hash"]
        return {"ok": not divergences, "divergences": divergences, "lines": lines}

    def replay(self) -> List[Dict[str, Any]]:
        """Return all events. Aborts with ValueError if the chain fails verify."""
        result = self.verify()
        if not result["ok"]:
            raise ValueError(f"ledger chain broken: {result['divergences']}")
        return [row for _, row in self._rows()]

    # -- analytics ----------------------------------------------------------

    def trial_balance(self) -> Dict[str, Any]:
        """The moth-ledger discipline ported to gossip: attempted deliveries must
        equal confirmed + simulated + unconfirmed + refused. A receipt set that
        does not balance is faking at least one receipt."""
        events = self.replay()

        def count(e: Dict[str, Any]) -> int:
            return int(e.get("count", 1))

        attempted = confirmed = simulated = unconfirmed = refused = dropped = 0
        for e in events:
            mode = str(e.get("mode", "")).upper()
            if e["event"] == "SPREAD":
                attempted += count(e)
            elif e["event"] == "DELIVER" and mode == "CONFIRMED":
                confirmed += count(e)
            elif e["event"] == "DELIVER" and mode == "SIMULATED":
                simulated += count(e)
            elif e["event"] == "UNCONFIRMED":
                unconfirmed += count(e)
            elif e["event"] == "REFUSE":
                refused += count(e)
            elif e["event"] == "DROP":
                dropped += count(e)
        remainder = attempted - confirmed - simulated - unconfirmed - refused - dropped
        return {
            "attempted": attempted,
            "confirmed": confirmed,
            "simulated": simulated,
            "unconfirmed": unconfirmed,
            "refused": refused,
            "dropped": dropped,
            "balanced": remainder == 0,
            "remainder": remainder,
        }

    # -- internals ----------------------------------------------------------

    def _last_hash(self) -> str:
        last = "GENESIS"
        for _, row in self._rows():
            last = row.get("hash", last)
        return last

    def _rows(self):
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    yield lineno, json.loads(line)
                except json.JSONDecodeError:
                    yield lineno, {"event": "CORRUPT", "raw": line}

    @staticmethod
    def _canonical(row: Dict[str, Any]) -> str:
        payload = {k: v for k, v in row.items() if k not in ("hash",)}
        return json.dumps(payload, sort_keys=True, default=str)
