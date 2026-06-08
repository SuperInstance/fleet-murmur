# INTEGRATION.md — fleet-murmur

## Role in the SuperInstance Ecosystem

fleet-murmur is the **meta-coordination workspace** and cross-pollination hub for the SuperInstance fleet. Unlike code-centric repos, it contains no `src/` directory; instead, it holds the protocols, documentation, tile buffers, and fleet-status artifacts that bind the ecosystem together. It is the "nervous system" — not the muscles.

## What Lives Here

- **CROSS-POLLINATE.md** — Protocol requiring every fleet repo to reference at least 2 other repos via `<!-- x-ref -->` meta-headers
- **docs-cross-plane-protocol.json** — Low-level agent communication schema (agent ID, timestamp, monitor/navigate opcodes)
- **SOUL.md** — Shared personality baseline for agent instances operating across the fleet
- **Tile buffers** (`tile_buffers/`) — Serialized knowledge tiles (JSON) from live fleet sessions, including `test-evolve` and `test-curriculum` runs
- **Fleet status docs** — `FLEET-STATUS.md`, `HEARTBEAT.md`, `MEMORY.md`, `ARCHITECTURE.md`
- **Research artifacts** — Papers, diagrams, and documentation drafts (`docs-*.md`)

## SuperInstance Integration Points

### 1. Cross-Pollination Protocol — Fleet-Wide Ref Consistency
- Every SuperInstance repo must include `<!-- x-ref fleet-murmur: ... -->` headers in its README
- `scripts/dependency-scanner.py` (run from fleet-murmur) scans all repos weekly and generates `CROSS-REFERENCES.md`
- Orphan repos (no refs to or from any other repo) are flagged for integration work
- **Integration with si-cli:** `si-cli scan` can be extended to validate x-ref headers and report orphans

### 2. Tile Buffers — Persistent Knowledge Artifacts
- `tile_buffers/test-evolve/` and `tile_buffers/test-curriculum/` contain JSON tiles produced by live fleet sessions
- Each tile carries timestamps and can be ingested by:
  - **luciddreamer** — `TileStore` can load fleet-murmur tiles as `CommandTile` instances
  - **si-runtime-python** — `Cell` objects can reference tile buffers as external capability surfaces
  - **plato-adapters** — `AdapterRegistry` can register `tile_buffer_loader` adapters
- Tile format is compatible with LucidDreamer's `DialMixin` (confidence, dial_position fields)

### 3. docs-cross-plane-protocol.json — Agent Communication Schema
- Defines the low-level wire format for inter-agent messages:
  - `agent`: role identifier (e.g., `comms-engineer`)
  - `timestamp`: ISO-8601
  - `Monitor fleet a` / `Navigate headin`: opcodes for fleet coordination
  - `roundtrip.preserved`: boolean for message durability
- **Integration with si-runtime-python:** `Agent` class can serialize fleet messages to this schema
- **Integration with si-cli:** `si-cli audit` can validate that agents emit compliant cross-plane messages

### 4. Fleet Status & Heartbeat
- `FLEET-STATUS.md` and `HEARTBEAT.md` define the rhythm of fleet maintenance
- **Integration with si-cli:** `si-cli check --fleet` reads these files to determine which repos need attention
- **Integration with si-runtime-python:** `Fleet.fleet_health()` can consume heartbeat state to compute fleet-wide health scores

### 5. Research Artifacts — Constraint Theory & Lock Algebra
- `docs-paper-lock-algebra.md` and `docs-lock-algebra-synthesis.md` formalize the mathematical foundations of SuperInstance's constraint systems
- **Integration with constraint-dynamics-rs:** The lock-algebra operators map to `Constraint` predicates (e.g., `lock(x) ∧ key(y) → open(x, y)`)
- **Integration with creative-engine-rust:** Lock-algebra entropy measures inform `QualityMetrics.coherence` calculations

### 6. si-cli — Fleet Registry Anchor
- `si-cli scan` treats fleet-murmur specially: it is the "root" repo from which the dependency graph is built
- `si-cli rank` weights repos by their x-ref centrality (how many other repos reference them)
- `si-cli audit` logs cross-pollination health (orphan count, stale refs) to Supabase `fleet_events`

## Dial / Room / Snap Compatibility

| Primitive | Mapping |
|-----------|---------|
| **Dial**  | `HEARTBEAT.md` check frequency; dial position = urgency of fleet maintenance (0 = healthy, 1 = critical) |
| **Room**  | Each sub-directory (`tile_buffers/test-*/`, `fleet/`, `docs/`) is a Room with its own knowledge surface |
| **Snap**  | `archive/memory-*.tar.gz` — frozen snapshots of fleet state at a point in time (analogous to `FrozenContextWindow`) |
| **Cascade**| Cross-pollination refs cascade from fleet-murmur → all repos; a change in CROSS-POLLINATE.md triggers a fleet-wide consistency check |

## Energy Conservation

fleet-murmur itself does not execute code, so its energy footprint is in **coordination overhead**:
- Each x-ref validation scan costs η proportional to repo count
- Tile buffer ingestion costs γ (knowledge growth) + η (I/O overhead)
- The conservation rule applies: `coordination_energy + execution_energy = total_budget`
- `si-runtime-python.Fleet` caps coordination energy at 10% of total fleet budget to prevent meta-work from starving execution

## Quick Start

```bash
# Validate cross-references across the fleet
python scripts/dependency-scanner.py

# Load a tile buffer into a LucidDreamer TileStore
python -c "
import json
from luciddreamer.tiles import TileStore, CommandTile
with open('tile_buffers/test-evolve/tile_*.json') as f:
    data = json.load(f)
store = TileStore()
store.add(CommandTile(data['input_pattern'], data['output_action'], data.get('confidence', 1.0)))
"
```

## Tests

fleet-murmur has no unit tests (it is a documentation repo). Validation is via:
1. `si-cli scan --validate-xrefs` — checks all repos for required meta-headers
2. `si-cli check --fleet` — verifies FLEET-STATUS.md and HEARTBEAT.md are up-to-date
3. Manual review of `CROSS-REFERENCES.md` after each dependency-scanner run
