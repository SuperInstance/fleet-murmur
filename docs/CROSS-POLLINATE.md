# CROSS-POLLINATE — provenance receipts

What this repo took from the rest of the fleet, and where it went. Every entry
names its source repo so a skeptic can walk the chain.

## 2026-09-27 — honesty-receipts pass

| Lesson | Source repo | Landing spot here |
|---|---|---|
| A delivery claim must name how it knows (confirmed/simulated/unconfirmed); a black-hole transport must not score 100% coverage | pong-quilt (QA-REFUSAL seam, R23–R28 honesty pins) | `fleet_murmur/gossip.py` transport honesty contract + `GossipRound.deliveries_*` |
| fnv1a hash-chained WAL as the receipt substrate; one verifier reads every fleet ledger | hermit quilt-kernel P1, pong-quilt session WAL (`tools/wal-session.js`) | `fleet_murmur/ledger.py` (`MurmurLedger.verify/replay`) |
| Trial balance: receipts must sum — attempted == confirmed + simulated + unconfirmed + refused + dropped | quilt-doctor `examples/moth_ledger_bridge.py` (ROUND_CLOSE via trial balance) | `MurmurLedger.trial_balance()` |
| Refuse-don't-fake: a quality gate says no with a receipt, not by silently dropping; missing optional deps abstain, never fake | quality-gate-stream review (`strict` mode, REFUSAL receipts), quilt-doctor OracleLens skip-guard | `GossipProtocol(gate=...)` REFUSE receipts; `tools/quality_gate_adapter.py` — LIVE-VERIFIED 2026-09-27 against the real quality-gate-stream package (was stale-API: `add_check(name=...)`, `report.passed`; 4 pins in `tests/test_qgs_adapter_glue.py` run the real scorer, abstain as skips when uninstalled) |
| VERIFIED_CLAIMS registry + README count pinned two-way against the live suite | pong-quilt (VERIFIED_CLAIMS + readme-count pin) | `VERIFIED_CLAIMS.md`, `tests/test_honesty_pass.py` |
| Only ALIVE/SUSPECT peers are gossiped to — suspicion is the default; trust is a receipt | fleet suspicion doctrine (PLATO nervous system, peer liveness mesh) | documented in `GossipProtocol.add_peer` docstring |

## Reverse direction — what fleet-murmur gives back

* `MurmurLedger` is a standalone hash-chain any repo can reuse (same fnv1a as
  hermit/pong-quilt): `from fleet_murmur.ledger import MurmurLedger`.
* The transport-honesty mode vocabulary (CONFIRMED/SIMULATED/UNCONFIRMED/DROP/
  REFUSE) is a candidate fleet-wide receipt vocabulary — propose it as the
  shared `mode` field in the quilt 5-opcode EFFECT receipts.
