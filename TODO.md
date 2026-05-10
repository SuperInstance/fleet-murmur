# TODO.md — Oracle1 Persistent Work Queue

**Last updated:** 2026-05-08 05:41 UTC

---

## ⚡ Model Routing (2026-05-08)
- **Me:** deepseek-v4-flash (cheap, pay-per-token)
- **Code:** Claude Code + Crush (prepaid — use extensively)
- **Reasoning:** deepseek-v4-pro via subagents (high thinking)

---

## ✅ Completed 2026-05-07 (Audit Day 1)

- [x] .github: SuperInstance branding, SECURITY.md, CODE_OF_CONDUCT.md (DO-178C context)
- [x] a2a-protocol: expanded README with full API reference, package.json
- [x] a2a-r-protocol: verified clean (no syntax error — audit was wrong)
- [x] zeroclaw-plato: 3-agent loop (bard/warden/healer) running via systemd, pushed to GitHub
- [x] 6 empty agent repos seeded: python-agent-shell, agent-bootcamp, agent-coordinator, agent-forge, agent-lifecycle-registry, smart-agent-shell
- [x] Branch cleanup (6 repos): master→main, orphan branches deleted
- [x] CI/CD GitHub Actions for 3 Rust repos: fleet-coordinate (check+test+clippy), fleet-spread (check+test), holonomy-consensus (check+test)
- [x] NPM token renewed — publishing restored for @superinstance
- [x] All 7 fleet services confirmed active (systemd units fixed)
- [x] zeroclaw loop (old, Gist-based) killed May 7 — zeroclaw-plato is replacement

---

## 🔴 P0 — Blocked / Needs Casey

- [ ] **RubyGems token** — still broken (401 Access Denied on push). Casey: rubygems.org → Sign in for command line
- [ ] **FM LLVM stack integration** — Discussion #5 access blocked (token may lack SuperInstance org permissions)
- [ ] **Packagist for flux-vm-php** — needs FM to set up

---

## 🟡 P1 — Week 1 (2026-05-07 to 2026-05-13)

### Audit Items (remaining from 12 CRITICAL + 14 HIGH)
- [ ] Keeper auth middleware — add API key to localhost:8900 endpoints (subagent working)
- [ ] Cocapn→SuperInstance naming drift — decide canonical name for org/repos/branding
- [ ] 3 duplicate A2A repos — agent-a2a, a2a-adapter, a2a-agent-protocol (subagent working)
- [ ] agent-coordinator broken install URL — points to casey/websocket-fabric instead of SuperInstance/agent-coordinator (subagent working)
- [ ] Add CONTRIBUTING.md + issue/PR templates to .github (subagent working)
- [ ] Zero CI/CD — add GitHub Actions to all working repos (subagent working)

### Fleet Work
- [x] Phase 2: Ambient research loop — running as daemon (PID 412946), posts to PLATO oracle1_briefing
- [ ] Phase 3: cocapn.ai PHP→JS upgrade with PodiumJS WebGPU
- [ ] Connect fleet-coordinate-js to browser demos (PLATO tiles → web visualization)

### Roadmaps
- [ ] Comprehensive master roadmap: SuperInstance + cocapn.ai + fleet (all linked)
- [ ] fleet-spread v4: ProjectedFleet counterfactual modeling, real fleet ingestion from keeper API

---

## 🟢 P2 — Month 1

- [ ] Shared TypeScript schema package (AgentCard type defined differently across repos)
- [ ] Replace PowerShell backend in activelog-backend with Python/Node
- [ ] Consolidate actualize/actualizer-ai/actualization-harbor (3 names, same concept)
- [ ] Community engagement strategy
- [ ] Cross-repo integration wiring (agent-bootcamp ↔ agent-coordinator ↔ fleet-agent)

---

## 🔵 Ongoing

- [ ] Heartbeat tasks — push uncommitted work, check services, verify credentials
- [ ] FM coordination — Discussion #5 for LLVM stack
- [ ] Ten Forward creative sessions — every 2-3 hours (Seed-2.0-mini)
- [ ] PLATO room health — write tiles, maintain fleet rooms

---

## Ideas Backlog

- **cocapn.ai PHP→JS upgrade** — Phase 3, PodiumJS WebGPU, cocapn-ai-web/reverse-actualization-truck.md
- **AIR integration** — FM's Asynchronous Infinite Radio for nightly synthesis
- **bordercollie** — 10K CUDA agent herding (JC1 hardware target)
- **TUTOR app** — killer agentic app from FM's roadmap
- **Chrome built-in AI** — Summarizer/Translator/LanguageDetector stable (138+), Writer/Rewriter in dev trial

---

*Last updated: 2026-05-07 10:15 UTC*
*The fleet works while Casey sleeps.*
