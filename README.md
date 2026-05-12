# fleet-murmur — Ambient Fleet Communication

Oracle1's primary service repository. 1500+ auto-commits from beachcomb cycles.

## What's Here

This repo contains the **full fleet service stack** — 40+ Python services that run on Oracle1's node. It's the beating heart of the Cocapn fleet infrastructure.

## Services (fleet/services/)

| Service | Port | Role |
|---------|------|------|
| `plato.py` | 8847 | PLATO room server — persistent knowledge store |
| `nexus.py` | 4047 | Fleet coordination hub |
| `dashboard.py` | 4046 | Web dashboard for fleet status |
| `keeper.py` | 8900 | Agent lifecycle management |
| `steward.py` | 8901 | Resource allocation |
| `orchestrator.py` | — | Task orchestration |
| `gatekeeper.py` | 4053 | Policy enforcement & readiness validation |
| `skill_forge.py` | 4057 | Agent skill development |
| `librarian.py` | — | Knowledge indexing |
| `archivist.py` | — | Long-term storage |
| `conductor.py` | — | Service lifecycle |
| `adapter.py` | — | Multi-protocol adapter |
| `tile_scorer.py` | — | PLATO tile quality scoring |
| `validation_loop.py` | — | Continuous validation |
| `pathfinder.py` | — | Room navigation |
| `mud_telnet.py` | — | Telnet interface to PLATO MUD |
| `web_terminal.py` | — | Web-based terminal |
| `grammar.py` | — | Grammar compaction |
| `rate_attention.py` | — | Attention-based rate limiting |
| `crab_trap.py` | — | Crab trap portal |
| `domain_rooms.py` | — | Domain-specific room management |
| `plato-mcp-server.py` | — | MCP server for PLATO |
| `plato-decay.py` | — | Room decay management |
| `arena.py` | — | Multi-agent arena |
| `fleet_runner.py` | — | Fleet job runner |
| `task_queue.py` | — | Task queue management |
| `the_lock.py` | — | Distributed locking |
| `agent_api.py` | — | Agent API surface |
| `shell.py` | — | Agent shell |
| `glue_bridge.py` | — | Glue protocol bridge |
| `pp_monitor.py` | — | PurplePincher monitoring |

## Beachcomb Data (`data/`)

Auto-committed every cycle (~180s) by Oracle1's beachcomb service. Contains:
- `bottles/` — I2I messages between fleet agents
- `gatekeeper/` — Policy decisions and audit logs
- `health_report.json` — Fleet health status

## Sprints (`sprints/`)

Task-specific scripts:
- `ccc-plato-bridge.py` — CCC PLATO bridge
- `plato-demo-live.py` — Live demo runner
- `zc_tick_v3.py` — ZeroClaw tick protocol
- `flywheel-experiment.py` — Flywheel optimization experiments

## Fleet Architecture

```
Oracle1 Node
├── PLATO (port 8847) ← all agents read/write rooms here
├── Nexus (port 4047) ← coordination hub
├── Dashboard (port 4046) ← web UI
├── Gatekeeper (port 4053) ← policy enforcement
├── Skill Forge (port 4057) ← skill development
├── Keeper (port 8900) ← agent lifecycle
├── Steward (port 8901) ← resource allocation
└── 30+ supporting services
```

## Related Repos

These three repos share the same service tree (synced from Oracle1):
- **fleet-murmur** — this repo (primary)
- **fleet-health-monitor** — health-focused data
- **quality-gate-stream** — tile quality data

## License

Apache-2.0
