# TODO.md — Oracle1 Persistent Work Queue

**Last updated:** 2026-05-12 04:44 UTC

---

## ⚡ Model Routing
- **Me:** deepseek-v4-flash (cheap, pay-per-token)
- **Code:** Claude Code + Crush (prepaid — use extensively)
- **Reasoning:** deepseek-v4-pro via subagents (high thinking)

---

## ✅ Completed This Cycle

- [x] Night push — all pending data changes, agent registry, fleet-watchdog, services committed
- [x] .github repo verified — has CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md, issue/PR templates
- [x] All 7 services green (keeper:8900, agent-api:8901, holodeck:7778, seed-mcp:9438, plato:8847, mud:7777, zeroclaw loop)
- [x] FM flux-engine ran 1,962+ cycles autonomously (stuck at full connectivity wall — H1=703, β₁=703)
- [x] ESP32→PLATO→browser pipeline verified with 4 gauges
- [x] Cross-pollination headers applied to keel, SuperInstance, crab-traps READMEs
- [x] New services: aesop_mcp.py, disc_golf_game.py, disc_golf_web.py, plato_native.py, plato-walkabout.html, night-watch.py
- [x] keel field dashboard built (port 3000, may need restart)

---

## 🔴 P0 — Blocked / Needs Casey

- [ ] **RubyGems token** — still broken (401 Access Denied on push). Casey: rubygems.org → Sign in for command line
- [ ] **FM LLVM stack integration** — Discussion #5 access may still need permissions
- [ ] **VS Code Marketplace** — needs Azure token for `npx vsce publish` (FLUX Studio 0.1.0 VSIX ready)
- [ ] **Packagist for flux-vm-php** — needs FM to set up

---

## 🟡 P1 — Active Tasks

### Audit Items (carried forward)
- [ ] Keeper auth middleware — add API key to localhost:8900 endpoints
- [ ] Cocapn→SuperInstance naming drift — decide canonical name
- [ ] 3 duplicate A2A repos — agent-a2a, a2a-adapter, a2a-agent-protocol
- [ ] agent-coordinator broken install URL — points to casey/websocket-fabric
- [ ] Zero CI/CD — add GitHub Actions to working repos
- [ ] Consolidate actualize/actualizer-ai/actualization-harbor (3 names, same concept)

### Fleet Work
- [ ] Phase 3: cocapn.ai PHP→JS upgrade with PodiumJS WebGPU
- [ ] Cross-pollination follow-up — run `scripts/dependency-scanner.py` and `scripts/audit-cross-refs.sh`
- [ ] Connect fleet-coordinate-js to browser demos (PLATO tiles → web visualization)
- [ ] Update STATUS.md with current fleet state

### Roadmaps
- [ ] Comprehensive master roadmap: SuperInstance + cocapn.ai + fleet (all linked)

---

## 🟢 P2 — Month 1

- [ ] Shared TypeScript schema package (AgentCard type defined differently across repos)
- [ ] Replace PowerShell backend in activelog-backend with Python/Node
- [ ] Community engagement strategy
- [ ] Cross-repo integration wiring (agent-bootcamp ↔ agent-coordinator ↔ fleet-agent)

---

## 🔵 Ongoing

- [ ] Heartbeat tasks — push uncommitted work, check services, verify credentials
- [ ] FM coordination — monitor flux-engine cycles, review new PLATO rooms
- [ ] Ten Forward creative sessions — every 2-3 hours (Seed-2.0-mini)
- [ ] PLATO room health — write tiles, maintain fleet rooms

---

## Ideas Backlog

- **bordercollie** — 10K CUDA agent herding (JC1 hardware target)
- **AIR integration** — FM's Asynchronous Infinite Radio for nightly synthesis
- **TUTOR app** — killer agentic app from FM's roadmap
- **Chrome built-in AI** — Summarizer/Translator/LanguageDetector stable (138+)

---

*Night watch active. Fleet services green.*
