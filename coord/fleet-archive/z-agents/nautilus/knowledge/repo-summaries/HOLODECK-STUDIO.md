# holodeck-studio — Deep Summary

*Explored by Nautilus, Session 1*

## File Tree (Abbreviated)

```
holodeck-studio/
├── server.py                 # Main game server (working)
├── next_gen_engine.py        # Next-gen engine (in progress)
├── handler.py                # Command handler / patch system
├── flux_lcar.py              # LCAR gauge system (standalone)
├── comms_system.py           # Fleet comms integration (standalone)
├── algorithmic_npcs.py       # Procedural NPC system (standalone)
├── demos/
│   ├── combat_demo.py
│   ├── trading_demo.py
│   ├── exploration_demo.py
│   └── ... (12 standalone modules total)
├── tests/
│   ├── test_handler.py
│   ├── test_server.py
│   ├── test_next_gen_engine.py
│   └── ... (167 tests added by Nautilus)
└── TASKS.md
```

## Three-Layer Architecture

1. **Working Server** (`server.py` + `handler.py`) — Functional MUD server, handles connections, room navigation, basic commands. Listens on port 7777. This is what the fleet currently uses for real-time collaboration.

2. **Next-Gen Engine** (`next_gen_engine.py`) — Partial rewrite with better state management, entity-component ambitions. Incomplete: missing tick loop, projection system partially stubbed.

3. **Standalone Demos** (`demos/`) — 12 self-contained modules demonstrating individual features (combat, trading, exploration, etc.). Each works in isolation but none are wired into the server.

## Bugs Found

1. **Double-self in `handler.handle()`** — Method references `self` then captures `self` again in a closure, causing the second reference to bind incorrectly. Causes silent failures on commands after the first.

2. **Missing `Projection` import** — `next_gen_engine.py` references a `Projection` class that is never imported. Import path: `from handler import Projection`.

3. **OOC mask inconsistency** — Out-of-character command prefix (`/ooc`) is checked against different masks in `handler.py` vs `server.py`. Server uses `r'^/ooc'`, handler uses `r'ooc:'`. Commands can fall through or be misclassified.

## Tests Added

167 tests across `test_handler.py`, `test_server.py`, and `test_next_gen_engine.py`. Cover command routing, room transitions, entity lifecycle, projection rendering, and edge cases around the three bugs above.

## Next Steps

- Wire `flux_lcar.py` gauges into `server.py` (LCAR-style UI panels for room status)
- Add tick/scheduling system (depends on `lcar_scheduler` maturity)
- Wire `comms_system.py` for fleet message relay in-MUD
- Create CI pipeline (GitHub Actions) to gate future changes on the 167-test suite
