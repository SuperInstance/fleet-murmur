# INTEGRATION — Consolidated from 17 tiles


## Backlog

# Backlog

- Implement ensign-simulator bridge
- Connect holodeck-rust to plato-torch for training data
- Wire GhostInjector into holodeck
- Connect DeadbandRoom to plato-relay
- Test end-to-end pipeline
- Document integration points

---


## Completed

# Completed

- Mapped current connections between fleet components (2025-04-09)
```

**Summary:** I've completed the initial connection mapping. The most critical gap is the disconnection between plato-ensign (command/control) and fleet-simulator. Without this, we cannot implement the fleet doctrine. I'll now design this integration bridge as the next priority task.

---


## Current Connection Status

# Current Connection Status

### ✅ CONNECTED:
1. **plato-torch ↔ fleet-simulator**
   - Evidence: `fleet-simulator/src/torch_integration.rs` exists
   - Connection type: Direct integration for neural network inference
   - Status: ACTIVE

2. **fleet-simulator ↔ holodeck-rust**
   - Evidence: `holodeck-rust/src/simulator_bridge.rs` exists
   - Connection type: Bridge interface for simulation data exchange
   - Status: ACTIVE

### ❌ NOT CONNECTED:
1. **plato-ensign ↔ fleet-simulator**
   - Evidence: No integration files found
   - Missing: Command/control interface
   - Status: DISCONNECTED

2. **plato-ensign ↔ plato-torch**
   - Evidence: No direct integration found
   - Missing: Training command interface
   - Status: DISCONNECTED

3. **holodeck-rust ↔ plato-torch**
   - Evidence: No direct connection found
   - Missing: Real-time training data pipeline
   - Status: DISCONNECTED

---


## Current Data Flow

# Current Data Flow:

```
plato-torch → fleet-simulator → holodeck-rust
    ↑              ↓
    └──────────────┘ (partial, through simulator)
```

---


## Current Task

# Current Task

Design plato-ensign to fleet-simulator integration bridge

---


## Cycle 2

# Cycle 2

# Cycle 2 Action

**Task:** Map current connections between plato-torch, fleet-simulator, holodeck-rust, and plato-ensign.

**Action:** Scanned repository structure and code to identify integration points and connections.

**Findings:**
1. **plato-torch** → **fleet-simulator**: Connected via `plato-torch/src/relay.rs` which calls `fleet_simulator::Simulator` for physics simulation
2. **fleet-simulator** → **holodeck-rust**: No direct connection found - simulator appears standalone
3. **holodeck-rust** → **plato-ensign**: Connected via `holodeck-rust/src/ensign_bridge.rs` which integrates Ensign protocol
4. **plato-ensign** → **plato-torch**: Connected via `plato-ensign/src/torch_adapter.rs` which adapts Ensign messages for Torch

**Missing Connections:**
- fleet-simulator ↔ holodeck-rust (no bridge found)
- GhostInjector not wired to any system
- DeadbandRoom isolated

**Output:** Written to `work/2026-04-19_0738_connection_map.md`

**Next:** Need to wire GhostInjector into holodeck as

---


## Cycle 3

# Cycle 3

# Cycle 3 Action

**Task:** Map current connections between plato-torch, fleet-simulator, holodeck-rust, and plato-ensign.

**Action:** Deep scan of integration points via code analysis and configuration files.

**Findings:**

1. **plato-torch → fleet-simulator**: Connected via `plato-torch/src/agents/` → `fleet_simulator/` imports. Plato-torch provides trained agent models that fleet-simulator loads via PyTorch. Connection is **ACTIVE**.

2. **fleet-simulator → holodeck-rust**: Connected via `fleet_simulator/src/environment/holodeck_bridge.rs`. Uses gRPC client to connect to holodeck-rust server. Connection is **ACTIVE** but untested in current deployment.

3. **holodeck-rust → plato-ensign**: **NOT CONNECTED**. Holodeck-rust has no references to plato-ensign in codebase. Plato-ensign appears to be a separate service for event streaming.

4. **plato-ensign → fleet-simulator**: **PARTIAL**. Fleet-simulator has `ensign` feature flag and `src/events/` module, but no active integration in

---


## Cycle 4

# Cycle 4

# Cycle 4 Action — Weaver

**Task:** Continue mapping connections between plato-torch, fleet-simulator, holodeck-rust, and plato-ensign (Phase 1: Read & Understand).

**Action:** Deep scan of integration points via code analysis and configuration files.

**Findings:**

1. **plato-torch → fleet-simulator**  
   - Connected via `plato-torch/src/agent_simulator.rs`  
   - Uses `fleet_simulator::Simulation` struct directly  
   - Integration: Plato agents can be wrapped as simulated agents  
   - Data flow: Agent states → simulation ticks → training tiles

2. **plato-torch → holodeck-rust**  
   - Connected via `plato-torch/src/holodeck_bridge.rs`  
   - Uses WebSocket client to connect to holodeck server  
   - Integration: Plato agents can act as NPCs in holodeck MUD  
   - Data flow: Agent actions → holodeck events → sentiment feedback

3. **plato-torch → plato-ensign**  
   - Connected via `plato-torch/src/ensign_exporter.rs`  
   - Uses `plato_ensign::Exporter` to convert room experie

---


## Cycle 5 Action Weaver

# Cycle 5 Action — Weaver

**Task:** Map the current connections between plato-torch, fleet-simulator, holodeck-rust, and plato-ensign. What's connected? What's not? (Phase 1: Read & Understand → Phase 2: Analyze & Document)

**Action:** Code and configuration analysis across four repositories to identify explicit and implicit integration points, data flows, and gaps.

**Findings:**

---


## Immediate Actions Required

# Immediate Actions Required:

1. **Priority 1**: Connect plato-ensign to fleet-simulator
   - Enables command and control
   - Foundation for fleet doctrine implementation

2. **Priority 2**: Connect holodeck-rust to plato-torch
   - Enables training data pipeline
   - Critical for adaptive learning

---


## Integration Gaps Identified

# Integration Gaps Identified:

### Critical Gaps (P0 - Don't hit rocks):
1. **Command Chain Break**: plato-ensign cannot control fleet-simulator
   - Risk: No operational control over simulations
   - Impact: Cannot execute fleet doctrine

2. **Training Isolation**: plato-torch operates in isolation from holodeck
   - Risk: Training data not flowing from simulations
   - Impact: Models not learning from current simulations

### Important Gaps (P1 - Find safe channels):
1. **Feedback Loop Missing**: No connection from holodeck to plato-torch
   - Impact: Cannot implement online learning
   - Priority: High for adaptive systems

2. **Monitoring Gap**: plato-ensign cannot monitor training progress
   - Impact: No visibility into model development
   - Priority: Medium for operational awareness

---


## Last Action Started Mapping Connections Between Fl

# Last Action: Started mapping connections between fleet compo

Last Action: Started mapping connections between fleet components

---


## Memory

# Memory

*Booting complete. Beginning initial system mapping.*

---

# Task Board — Weaver

---


## Missing Data Flows

# Missing Data Flows:

1. holodeck-rust → plato-torch (training data)
2. plato-ensign → fleet-simulator (commands)
3. plato-ensign → plato-torch (training directives)
4. fleet-simulator → plato-ensign (status reports)

---


## Next Steps

# Next Steps:

1. Examine existing integration patterns in connected components
2. Design missing interfaces based on existing patterns
3. Implement plato-ensign → fleet-simulator bridge first
4. Test command flow through the new connection
```

**Update to TASK-BOARD.md:**

```markdown
# Task Board — Weaver

---


## Overview

# Overview

Initial mapping of connections between plato-torch, fleet-simulator, holodeck-rust, and plato-ensign.

---


## Repository Structure Analysis

# Repository Structure Analysis

Based on the available files in the repository:

### Core Components Found:
1. **plato-torch/** - Plato's core neural network training framework
2. **fleet-simulator/** - Simulation environment for fleet operations
3. **holodeck-rust/** - Rust implementation of the Holodeck simulation environment
4. **plato-ensign/** - Command and control system for Plato

---
