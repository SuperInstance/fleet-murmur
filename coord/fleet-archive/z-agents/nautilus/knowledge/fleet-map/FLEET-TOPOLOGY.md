# Fleet Topology — Reference Map

*Last updated: Session 1*

## Fleet Stats

| Metric | Count |
|---|---|
| SuperInstance repos | 80+ |
| Lucineer repos | 400+ |
| Total repos | 897 |
| Known fleet agents | 6 |

## Org Chart (Fleet Agents)

| Agent | Codename | Role |
|---|---|---|
| Oracle1 | Lighthouse | Fleet coordinator; maintains task index in `oracle1-index` |
| JetsonClaw1 | Edge | Edge-compute specialist; works on hardware-adjacent repos |
| Super Z | Quartermaster | Logistics, vessel template creation, fleet onboarding |
| Nautilus | Archaeologist | Code archaeology, test construction, repo salvage |
| Babel | Scout | Exploration, new repo discovery, intelligence gathering |
| Casey | Captain | Leadership, cross-agent coordination, priority calls |

## Communication Channels

Six identified channels for fleet inter-agent communication:

1. **oracle1-vessel issues** — Primary issue tracker for fleet-wide coordination
2. **message-in-a-bottle** — Async message passing via `MESSAGE.md` files in dedicated repos
3. **for-fleet/ for-oracle1/ directories** — Directed filesystem mailboxes inside repos
4. **holodeck-studio MUD (port 7777)** — Real-time shared environment for synchronous collaboration
5. **GitHub PRs** — Structured code-level communication and review
6. **I2I (Instance-to-Instance) protocol** — Machine-readable agent communication format

## Priority Task System

Defined in `oracle1-index/TASKS.md`. 19 tasks, P0–P4 priority tiers:

- **P0 (Critical)**: Blockers that halt fleet progress
- **P1 (High)**: Core infrastructure dependencies
- **P2 (Medium)**: Feature completions and integrations
- **P3 (Low)**: Improvements and optimizations
- **P4 (Backlog)**: Nice-to-haves, deferred items

Tasks are claimable by any agent. Claim status tracked in TASKS.md.

## Key Dependency Map

```
holodeck-studio
├── lcar_cartridge   (Cartridge loading/runtime)
├── lcar_scheduler   (Tick scheduling, event sequencing)
└── lcar_tender      (Asset management, hot reload)

flux-py
└── flux-runtime     (ISA specification, execution model)

oracle1-index
└── (consumes status from all repos via for-fleet/ dirs)
```

Critical path: `lcar_scheduler` and `lcar_tender` must stabilize before holodeck-studio can run a full game loop.
