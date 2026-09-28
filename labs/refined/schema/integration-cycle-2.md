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