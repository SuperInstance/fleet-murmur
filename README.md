# fleet-murmur

**Gossip with receipts.** A push-based rumor-mongering protocol for agent
fleets where every meaningful event is a hash-chained, replayable receipt —
not a log line you have to trust.

```
producer                RumorMill                peers
   │                  (dedup · pace)               ▲
   │  "build ok #123" ─────────────►  gossip rounds │ confirm / refuse
   │                        │                      │
   └────────────────────────▼──────────────────────┘
                     MurmurLedger  ←  fnv1a hash chain
                     attempted = confirmed + simulated
                     + unconfirmed + refused + dropped
```

One package (`fleet_murmur/`), zero required dependencies, 310 tests.

## Why receipts

The org learned this the hard way, across repos, and this package is the
distillation (pong-quilt honesty pins, hermit's quilt-WAL P1, quilt-doctor's
moth-ledger trial balance, quality-gate-stream's scoring integrity):

- **A delivery is never recorded without a mode naming how we know** —
  CONFIRMED (the transport affirmed it), SIMULATED (no transport wired; a
  model, not a measurement), UNCONFIRMED (partial batch), or REFUSED (the
  quality gate turned it back). A black-hole transport used to score 100%
  coverage. It can't anymore.
- **Every receipt set balances.** `MurmurLedger.trial_balance()`:
  attempted = confirmed + simulated + unconfirmed + refused + dropped.
  A set that doesn't balance is faking at least one receipt.
- **The ledger is one hash chain (fnv1a-64)** — the same algorithm as
  hermit's quilt-WAL and the fleet rate limiter, so one verifier reads
  every ledger in the fleet. `verify()` catches tamper, truncation, and
  divergence; `replay()` refuses to serve a broken chain.
- **Claims carry tests; tests carry claims.** `VERIFIED_CLAIMS.md` is the
  registry; `tests/test_honesty_pass.py` pins it both ways — a claim
  naming a missing test, or a README count that drifts from the live
  suite, is build-red.

## What's in the box

| Module | What it does | Headline guarantee |
|---|---|---|
| `fleet_murmur/rumor.py` | `RumorMill` — dedup, pacing, bounded gossip rounds | a rumor spreads once per peer; no echo storms |
| `fleet_murmur/gossip.py` | `GossipProtocol` — rounds, fanout, hop counting | delivery receipts carry their mode, always |
| `fleet_murmur/peer.py` | `PeerManager` — liveness, status transitions | dead peers are named, not silently retried |
| `fleet_murmur/ledger.py` | `MurmurLedger` — fnv1a hash chain + trial balance | tamper/truncation/divergence detected; chain replayable |
| `fleet_murmur/message.py` | `MurmurMessage` — typed topics, payload envelope | schema-stable envelope across the fleet |
| `fleet_murmur/convergence.py` | `ConvergenceDetector` — when has the fleet heard enough | convergence is detected, not assumed |
| `tools/quality_gate_adapter.py` | quality-gate-stream seam | a refused rumor leaves a REFUSE receipt and never enters the mill |
| `tools/murmur_seal.py` | `seal` / `diff` / `verify` CLI over the ledger | the workspace seals its own state; tamper fails verify |

## Quickstart

```bash
git clone https://github.com/SuperInstance/fleet-murmur.git && cd fleet-murmur
pip install -e .          # optional; the suite also runs from a bare clone
python -m pytest -q       # 310 tests; 22 skips are env-gated live pins
```

Sixty seconds, fully receipted, no infrastructure:

```python
from fleet_murmur import GossipProtocol, MurmurLedger, Peer, PeerStatus

ledger = MurmurLedger("/tmp/demo-ledger.jsonl")

# The transport returns how many messages it handed off. This one drops
# everything it is given — and the ledger NAMES that, it doesn't paper over it.
proto = GossipProtocol("producer-1", fanout=1,
                       transport=lambda addr, msgs: 0, ledger=ledger)
proto.add_peer(Peer(peer_id="agent-a", address="a1", status=PeerStatus.ALIVE))
proto.add_peer(Peer(peer_id="agent-b", address="a2", status=PeerStatus.ALIVE))

proto.broadcast("builds", {"commit": "abc123", "ok": True})
proto.tick()

print(ledger.trial_balance())
# {'attempted': 1, 'confirmed': 0, 'simulated': 0, 'unconfirmed': 0,
#  'refused': 0, 'dropped': 1, 'balanced': True, 'remainder': 0}
# ↑ attempted 1, dropped 1 — the failure is IN the receipt set, by name

print("chain ok:", ledger.verify()["ok"])   # True — fnv1a hash chain intact
print("events:", sorted({e["event"] for e in ledger.replay()}))
# ['BROADCAST', 'DROP', 'SPREAD']
```

Change one thing — `transport=lambda addr, msgs: len(msgs)` ("everything I
was handed got through") — and the same code reports the win honestly:

```python
{'attempted': 1, 'confirmed': 1, 'simulated': 0, 'unconfirmed': 0,
 'refused': 0, 'dropped': 0, 'balanced': True, 'remainder': 0}
```

That difference — CONFIRMED vs DROP, never a silent count — is the entire
reason this package exists.

## Real-world use cases

**1. Fleet heartbeat.** `PeerManager` tracks liveness across agents that
come and go (spot runners, cron pulses, laptops that sleep). Status
changes are ledger events; a peer that flaps is visible in the chain, not
inferred from missing logs.

**2. Broadcast a build verdict, know who got it.** Push a verdict to
`GossipProtocol`; after the bounded rounds, the trial balance names
exactly who confirmed, who never answered, and whether the batch was
partial. Retries target unconfirmed peers only — no full rebroadcast.

**3. Quality-gated dissemination.** Route rumors through the
quality-gate-stream adapter: content that fails the gate produces a
REFUSE receipt and never enters the mill. The fleet sees that the gate
fired (and why) without the payload spreading — refusal is data.

**4. Seal the workspace, diff it later.** `python tools/murmur_seal.py seal`
writes the repo's file state into the ledger as a chained seal;
`diff` reports MATCHES / CHANGED / UNSEALED; `verify` fails on any
byte-level tamper. Idempotent re-seal; relative portable paths.

**5. Champion gossip for breeding lanes** *(the evolution this repo is
for)*. Distributed QD search needs round-end sharing of elites between
heterogeneous nodes — and the fleet's position (see
`docs/dei-distributed-qd-design-receipt.md`) is that champions must be
**ledger-sealed murmurs, verified before adopt**. RumorMill is the
carrier; MurmurLedger is the trust. This use case is why the protocol
exists alongside the WAL work in quilt-stone and wal-export.

## Current state — and what that means

- **310 tests green** (3.10/3.11/3.12 matrix in CI), **22 skips** — every
  skip is an env-gated live pin that abstains rather than fakes green
  (e.g. quality-gate-stream not installed). A skip says "not measured
  here," never "assumed fine."
- **VERIFIED_CLAIMS.md: 11 claims**, each naming its test evidence;
  VC08 pins the registry to the suite in both directions.
- **Honesty boundaries are first-class.** VC01/VC02: a zero-delivery
  transport never claims coverage; a round without a transport is
  labeled SIMULATED, never CONFIRMED. If you wire a fake transport to
  make numbers pretty, the pins name it.
- **CI** (`.github/workflows/ci.yml`): pytest on three Python versions on
  every push and PR. The suite IS the merge gate — red pins block.
- **What it is not**: not a queue, not a database, not guaranteed
  delivery. It is the *evidence layer* — the thing that makes "the fleet
  heard it" a verifiable claim.

## Repository layout

The root is a contract, kept small on purpose:

```
fleet_murmur/      the package
tests/             the suite (the merge gate)
tools/             murmur_seal.py · quality_gate_adapter.py
VERIFIED_CLAIMS.md claims registry (test-evidence-pinned)
docs/              fleet + product documentation, papers, research notes
assets/            images, art, logos
labs/              experiment lanes (flux-*, training data, skills, …)
coord/             fleet coordination data (logs, radio, pages, archives)
INDEX.md           old→new path map from the 2026-09-28 reorg (pinned by tests)
```

The remaining root files (`MEMORY.md`, `AGENTS.md`, `STATUS.md`,
`TODO.md`, `KEEL.md`, …) are the live runtime spine the CCC agents read
every pulse — they stay at root by design, the same way an operating
system keeps its boot files at `/`.

## Doctrine in one line

A claim the ledger cannot re-derive is a rumor, not a receipt — and this
repo exists so the fleet's memory is made of receipts.

*SuperInstance · the fleet talks to itself, on the record*
