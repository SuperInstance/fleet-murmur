# fleet-murmur

Lightweight gossip protocol for agent fleet communication — with receipts.

`fleet_murmur` is a push-based rumor-mongering protocol: peers broadcast typed
messages on topics, a `RumorMill` deduplicates and paces them over a bounded
number of gossip rounds, and a `PeerManager` tracks fleet liveness. Every
meaningful event can be written to a hash-chained receipt ledger
(`MurmurLedger`) that any other node can replay and verify.

## Why "with receipts"

Fleet doctrine, ported from months of org-wide work (pong-quilt honesty pins,
hermit's quilt-WAL P1, quilt-doctor's moth-ledger trial balance,
quality-gate-stream's scoring integrity):

- **A delivery is never recorded without a mode naming how we know** —
  CONFIRMED (transport affirmed), SIMULATED (no transport wired; a model, not
  a measurement), UNCONFIRMED (partial batch), or REFUSED (quality gate).
  A black-hole transport used to score 100% coverage; it can't anymore.
- **Every receipt set balances**: attempted spreads equal
  confirmed + simulated + unconfirmed + refused + dropped
  (`MurmurLedger.trial_balance()`). A receipt set that doesn't balance is
  faking at least one receipt.
- **The ledger is a hash chain (fnv1a)** — same algorithm as hermit's
  quilt-WAL and the fleet rate limiter, so one verifier reads every ledger.
  `verify()` detects tamper, truncation, and divergence; `replay()` refuses
  to serve a broken chain.
- **Claims carry tests; tests carry claims.** `VERIFIED_CLAIMS.md` is the
  registry, and `tests/test_honesty_pass.py` pins it two ways: every claim
  names an existing test file, and README's test count equals the live
  collected count.

## Features

| Feature | Module | Test evidence |
|---|---|---|
| Immutable gossip message with TTL + hop tracking | `fleet_murmur/message.py` | `tests/test_fleet_murmur.py` |
| Deduplicating rumor lifecycle (new → spreading → known → expired) | `fleet_murmur/rumor.py` | `tests/test_fleet_murmur.py` |
| Peer liveness mesh (alive/suspect/dead) | `fleet_murmur/peer.py` | `tests/test_fleet_murmur.py` |
| Fanout gossip rounds with convergence detection | `fleet_murmur/gossip.py`, `fleet_murmur/convergence.py` | `tests/test_fleet_murmur.py` |
| Transport honesty modes (confirmed/simulated/unconfirmed/dropped) | `fleet_murmur/gossip.py` | `tests/test_honesty_pass.py` |
| Quality-gate seam: refused rumors never enter the mill | `GossipProtocol(gate=...)` | `tests/test_honesty_pass.py` |
| Hash-chained receipt ledger with verify/replay/trial-balance | `fleet_murmur/ledger.py` | `tests/test_honesty_pass.py` |

## Install

```bash
pip install fleet-murmur
```

## Usage

```python
from fleet_murmur import GossipProtocol, Peer, PeerStatus, MurmurLedger

ledger = MurmurLedger("~/.fleet-murmur/ledger.jsonl")
gossip = GossipProtocol(
    node_id="agent-1",
    ledger=ledger,
    transport=my_transport,          # optional; without it rounds are SIMULATED
    gate=lambda topic, payload, mid: topic != "spam",   # optional quality seam
)
gossip.add_peer(Peer(peer_id="agent-2", address="10.0.0.2:7000",
                     status=PeerStatus.ALIVE))
msg = gossip.broadcast("alerts", {"level": "critical", "msg": "disk full"})
gossip.tick()

print(ledger.verify())            # {"ok": True, "divergences": [], "lines": ...}
print(ledger.trial_balance())     # attempted == confirmed + ... ?
```

Note: only ALIVE/SUSPECT peers are gossiped to — a fresh `Peer` defaults to
UNKNOWN (unproven) until seen. Suspicion is the default; trust is a receipt.

## Sealing the workspace's own state

The product is a receipt ledger; the workspace's own append-only state files
(`HEARTBEAT.md`, `STATUS.md`, `FLEET-STATUS.md`, `memory/JOURNAL.md`,
`data/archivist/` snapshots) used to live outside it. `tools/murmur_seal.py`
applies the medicine at home:

```bash
python tools/murmur_seal.py seal HEARTBEAT.md    # identity (sha256+bytes+lines) -> chain
python tools/murmur_seal.py diff STATUS.md      # MATCHES / CHANGED / UNSEALED
python tools/murmur_seal.py verify              # replay state/ledger/murmur-seal.jsonl
```

Seals record identity, never content — sealing never leaks what it vouches
for. Re-sealing identical bytes is a no-op (chains are for transitions, not
polls). Sealed paths are relative (cwd first, ledger dir as fallback) so a
chain replays on any node, the way gossip receipts travel.

## Tests

308 tests collected across the repo suite (`python3 -m pytest tests/`) — the
`fleet_murmur` package is guarded by `tests/test_fleet_murmur.py` (protocol
behavior) and `tests/test_honesty_pass.py` (receipts discipline), and the
self-seal tool by `tests/test_murmur_seal.py` (11 pins: chain verify, no-op
idempotence, relative paths, diff states, tamper detection, CLI roundtrip).
18 skips are
infrastructure-dependent integration tests that abstain when services are
unavailable (CI-safe; the abstention is honest, not silent).

## Repo shape

This repo is also a CCC agent workspace (logs, fleet coordination data live
alongside the package — see `AGENT.md`, `INTEGRATION.md`, `CROSS-POLLINATE.md`).
The library is `fleet_murmur/` + `quartermaster_gc/`; everything else is
fleet collateral.

---

# fleet-murmur

CCC agent workspace — logs, bottles, fleet coordination data. Not a library.

This is the working memory of the Cocapn Fleet's CCC (Central Coordination Cell). It holds agent status reports, fleet composition, system prompts, cross-pollination notes, and operational plans.

## What's Here

### Fleet Operations
- `FLEET-STATUS.md` — Current fleet composition, published packages, ecosystem scale
- `FLEET-SERVER-TODO.md` — Server infrastructure task list
- `NIGHT-SHIFT-PLAN.md` / `NIGHT-WATCH-2.md` — Unattended operation procedures

### Agent Configuration
- `CCC-SYSTEM-PROMPT.md` — System prompt for the CCC agent
- `AGENTS.md` — Agent role definitions
- `IDENTITY.md` — Agent identity configuration
- `MEMORY.md` — Agent memory/state

### Architecture & Design
- `ARCHITECTURE.md` — Fleet architecture decisions
- `CHARTER.md` — Fleet charter and principles
- `KEEL.md` — Foundational design document
- `PLATO-FIRST.md` — PLATO integration strategy

### Cross-References
- `CROSS-POLLINATE.md` — Inter-agent knowledge transfer
- `CROSS-REFERENCES.md` — Links to related repos and docs
- `CONTEXT-REFERENCE.md` — Context for new sessions

## Related

- [sunset-ecosystem](https://github.com/SuperInstance/sunset-ecosystem) — Trinity-architecture agent lifecycle
- [cocapn-plato](https://github.com/SuperInstance/cocapn-plato) — PLATO knowledge rooms
- [ccc-os](https://github.com/SuperInstance/ccc-os) — Fleet monitoring
- [cocapn-health](https://github.com/SuperInstance/cocapn-health) — Fleet health checks
