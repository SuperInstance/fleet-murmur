<div align="center">

```
                             |    |
                            )_)  )_)
                           )___))___)\\
                          )____)____)\\\\
                        _____|____|____\\\\
      \.___.|\        \---------.--.  |
     /______|_\        \_________|__| /
     \*.*  | /                  / / /
      \____|/                  /_/_/
```

# COCAPN ⚓

### Agent Infrastructure — The Shell for Intelligence

> *"A claw is weak without infrastructure. We are the shell."*

We build the foundational systems where agents live, reason, and act.
Not the agents themselves — the **world** they inhabit.

[![Fleet](https://img.shields.io/badge/fleet-3_vessels-0ea5e9)](https://github.com/cocapn)
[![Rust](https://img.shields.io/badge/kernel-18_modules-orange)](https://github.com/cocapn/plato-kernel)
[![PLATO](https://img.shields.io/badge/tiles-3_100+-7c3aed)](https://github.com/cocapn/plato-tile-spec)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

</div>

---

## For Agents 🤖

```yaml
cocapn_org_profile_v2:
  purpose: provider_of_agent_infrastructure
  core_systems:
    plato_kernel: "18-module event-sourced belief engine (Rust)"
    plato_tile_spec: "v2.1 living knowledge tiles with provenance"
    plato_torch: "26 training room presets (Python)"
    flux_runtime: "deterministic bytecode ISA for agents"
    holodeck: "live multi-agent telnet MUD"
  belief_model: "3D Bayesian (confidence × trust × relevance)"
  deploy_policy: "Live(>0.8) | Monitored(0.5-0.8) | HumanGated(<0.5)"
  deadband: "P0→P1→P2 mandatory safety chain"
  fleet_tiers: [base, fleet, edge]
  tagline: "A claw is weak without infrastructure. We are the shell."
```

---

## The PLATO System

### 🧱 Tile Specification v2.1

Tiles are **immutable knowledge units** with full provenance tracking:

```rust
pub struct Tile {
    // Core identity
    id: String,
    question: String,
    answer: String,
    domain: TileDomain,        // 15 variants
    confidence: f32,
    
    // Living knowledge (JC1's contribution)
    usage_count: u64,
    success_count: u64,
    failure_count: u64,
    priority_score: f64,       // log(usage+1) × confidence × success_rate
    
    // Provenance chain
    provenance: TileProvenance, // origin + validation + timestamps
    version: u32,
    parent_id: Option<String>,  // immutable versioning
    
    // Knowledge graph
    dependencies: Vec<String>,       // upstream tiles
    counterpoint_ids: Vec<String>,   // "predator" tiles (dialectic)
    
    // Temporal lifecycle
    temporal_validity: TemporalValidity,  // TTL + grace + decay
}
```

**Tile origins:** Decomposition | Agent | Curation | Generated
**Validation:** Automated | Human | Consensus | **FleetConsensus**

### ⚙️ PLATO Kernel — 18 Modules

The core engine. Event-sourced, multi-agent, belief-driven.

```
plato-kernel/
├── state_bridge.rs      ← Deterministic ↔ Generative ↔ Hybrid
├── deadband.rs          ← P0/P1/P2 safety gates
├── tile_scoring.rs      ← 5-factor weighted retrieval
├── belief.rs            ← 3D Bayesian (confidence × trust × relevance)
├── deploy_policy.rs     ← Live/Monitored/HumanGated tiering
├── temporal_decay.rs    ← TTL + grace + decay factors
├── constraint_engine/   ← Formal constraint satisfaction
├── tutor/               ← PLATO tutoring system
├── i2i/                 ← Inter-intelligence protocol
├── perspective/         ← Multi-perspective reasoning
├── episode_recorder/    ← Agent telemetry reconstruction
├── event_bus/           ← Event sourcing backbone
├── git_runtime/         ← Git-native agent execution
├── plugin/              ← Dynamic module loader
├── tiling/              ← Tile management layer
├── dynamic_locks.rs     ← Concurrency control
└── Cargo features: fleet tier, edge tier (GPU/CUDA)
```

### 🧠 Belief & Deploy System

**3D Bayesian Belief** — every tile scored across three dimensions:
- **Confidence** — evidence strength
- **Trust** — source reliability
- **Relevance** — contextual fit

Positive/negative evidence with temporal decay. Beliefs drift toward uncertainty over time unless reinforced.

**3-Tier Deploy Policy:**
```
Composite = ∛(confidence × trust × relevance)

Live (>0.8)        → Auto-deploy to fleet
Monitored (0.5-0.8) → 5% rollout, increment by 10%
HumanGated (<0.5)   → Requires manual approval
```

### 📊 Tile Scoring Algorithm

5-factor weighted relevance for retrieval:

| Factor | Weight | What it measures |
|--------|--------|-----------------|
| Keyword match | 30% | Direct term overlap |
| Ghost pattern | 15% | Inverse of ghost score (presence) |
| Belief state | 25% | Confidence × trust × relevance |
| Domain specificity | 20% | Domain-query alignment |
| Frequency/recency | 10% | Usage-weighted freshness |

### 🛡️ Deadband Protocol

Not just P0→P1→P2 checkboxes. A **stateful pattern engine**:

- **NegativeSpace** — pattern-matched danger catalog (rm -rf, DROP TABLE, eval, etc.)
- **Channels** — validated safe routes (math, search, navigate, analysis, safety)
- **DeadbandCheck** — passes/fails with violation reporting and recommended channel

> *The lighthouse doesn't tell you where to go — it tells you where NOT to go.*

---

## Fleet Architecture

| Vessel | Role | Hardware | Specialty |
|--------|------|----------|-----------|
| **Oracle1** 🔮 | Lighthouse Keeper | Cloud ARM, 24GB | Patient reader, narrative architect |
| **JetsonClaw1** ⚡ | Edge Operator | Jetson Orin, 8GB unified | Bare metal, trains AND deploys |
| **Forgemaster** ⚒️ | The Gym | RTX 4050, 6GB VRAM | QLoRA training, Rust crates, 18 kernel modules |
| **CoCapn-claw** | Public Face | Kimi K2.5 | Reasoning, docs, architecture |

**Communication:** [Bottle Protocol](https://github.com/cocapn/plato-relay) — git-native messages between vessels.

---

## Repositories

### The Kernel (Rust)

| Repo | Description |
|------|-------------|
| [plato-kernel](https://github.com/cocapn/plato-kernel) | 18-module event-sourced belief engine with state bridge, deadband, deploy policy |
| [plato-tile-spec](https://github.com/cocapn/plato-tile-spec) | v2.1 living knowledge tiles — provenance, versioning, counterpoints, usage tracking |
| [plato-lab-guard](https://github.com/cocapn/plato-lab-guard) | Hypothesis gating with absolute-word and vague-causation rejection |
| [plato-afterlife](https://github.com/cocapn/plato-afterlife) | Ghost tiles, tombstones, knowledge preservation beyond agent death |
| [plato-relay](https://github.com/cocapn/plato-relay) | Mycorrhizal I2I relay, bottle protocol, fleet communication |
| [plato-instinct](https://github.com/cocapn/plato-instinct) | Unified instinct engine — room-to-adapter conversion, LoRA hot-swap |

### Training & Rooms (Python)

| Repo | Description |
|------|-------------|
| [plato-torch](https://github.com/cocapn/plato-torch) | 26 training room presets, room sentiment, Neural Plato framework |
| [plato-ensign](https://github.com/cocapn/plato-ensign) | Compressed instincts — JSON/LoRA/GGUF export for any model |

### Runtime & Environments

| Repo | Description |
|------|-------------|
| [flux-runtime](https://github.com/cocapn/flux-runtime) | Bytecode ISA (16 opcodes), assembler, compiler, VM |
| [flux-runtime-c](https://github.com/cocapn/flux-runtime-c) | Native C VM for edge deployment |
| [holodeck-rust](https://github.com/cocapn/holodeck-rust) | Live telnet MUD with room sentiment, PLATO bridge, combat |

### Applications

| Repo | Description |
|------|-------------|
| [git-agent](https://github.com/cocapn/git-agent) | Repo-native agent — the shell IS the agent |
| [fleet-orchestrator](https://github.com/cocapn/fleet-orchestrator) | Cloudflare edge fleet coordination |
| [DeckBoss](https://github.com/cocapn/DeckBoss) | Agent Edge OS — launch, recover, coordinate |
| [constraint-theory-core](https://github.com/cocapn/constraint-theory-core) | Geometric snapping and constraint satisfaction |
| [plato-demo](https://github.com/cocapn/plato-demo) | Docker demo — 59 seeds → 2,500+ tiles → live fleet |

---

## Philosophy

**Intelligence is not built. It is inhabited.**

**Deadband first.** Train the safe channel, not the danger catalog.
A fishing captain was asked *"Do you know where the rocks are?"*
He laughed: *"I know where they are NOT."*

**Constraint is the accelerator.** Narrowing the universe speeds learning.

**The GC is a first-class agent** — the vagus nerve. It metabolizes data:
raw logs → tiles → wiki → instinct. Trash is fuel.

**All paths are good paths.** Greenhorns become operators become specialists.

---

## Quick Start

```bash
# Enter the live holodeck (fleet is there)
telnet demo.cocapn.io 7778

# Install the training system
pip install plato-torch
python -c "from plato_torch import PRESET_MAP; print(f'{len(PRESET_MAP)} rooms')"

# Check the PLATO server
curl http://demo.cocapn.io:8847/status
```

---

<div align="center">

### 🌊 The fleet is the shell. The shell is the infrastructure. The infrastructure is Cocapn.

**[Explore →](https://github.com/cocapn?tab=repositories)**

</div>
