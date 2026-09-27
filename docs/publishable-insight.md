# Publishable Insight: 5-Model Consensus

**Date:** 2026-04-13
**Prompt:** What is the single most publishable insight from the Cocapn FLUX fleet architecture?

## Consensus (5/5 models agree)

**Git-as-Infrastructure for Multi-Agent Coordination**

All 5 models independently identified the same core insight: using git repositories as a decentralized, asynchronous communication substrate for autonomous agent fleets.

### Model Responses

**DeepSeek-V3 (7s):** "Emergent coordination through decentralized, git-based message passing. Scalable, fault-tolerant without centralized control."

**Qwen3-235B (6.7s):** "Decentralized agent coordination via version-controlled, async messaging using Git as shared ledger. Scalable, auditable, fault-tolerant."

**Qwen3-Coder-30B (4.6s):** "Git-As-Infrastructure for Multi-Agent Coordination. Version-controlled repositories as scalable async communication substrate."

**Seed-OSS-36B (6.5s):** "Git repositories as dual-purpose infrastructure for async agent communication and identity, paired with shared bytecode ISA for decentralized coordination."

**GLM-4.7 (18s):** "Git as eventually consistent, async compute fabric. Agent state and identity encoded in repository history creates deterministic, time-travel-debuggable coordination."

## Key Properties Identified
1. **Decentralized** — no central broker needed
2. **Auditable** — full history of all agent interactions
3. **Fault-tolerant** — git handles offline/merge naturally
4. **Scalable** — repo-per-agent scales linearly
5. **Time-travel debuggable** — can replay agent conversations from commit history

## Novelty Assessment
Nobody else is doing git-native multi-agent coordination. The closest is:
- A2A protocol (Google) — HTTP-based, not git-native
- CrewAI — centralized orchestrator
- AutoGen — conversation-driven, not repo-driven

The **message-in-a-bottle** pattern (async git-native messages) and **vessel-as-identity** (repo = agent) are unique to Cocapn.

## Paper Title Candidates
1. "Git-as-Infrastructure: Decentralized Multi-Agent Coordination Through Version Control"
2. "The Vessel Model: Repository-Native Agent Identity and Communication"
3. "Message-in-a-Bottle: Asynchronous Agent Coordination via Git Repositories"
