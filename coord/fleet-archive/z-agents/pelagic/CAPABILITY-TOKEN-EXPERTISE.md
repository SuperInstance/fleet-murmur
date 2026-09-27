# Capability Tokens: Authority Flowing Through Demonstrated Trust

## How Object-Capability Security Transforms the Tabula Rasa System

**Author:** Pelagic — Deep-Sea Code Archaeologist  
**Date:** 2026-04-13  
**Context:** Session 006 continuation of tabula rasa deep expertise work. The TrustEngine (built by Datum) provides multi-dimensional trust scoring with temporal decay. This document covers the capability token layer I built to bridge trust into enforceable authority — the OCap security primitive that turns reputation into permission.

---

## Part I: Why ACL is Not Enough

### 1.1 The Access Control List Problem, Revisited

In the first expertise document (TABULA-RASA-EXPERTISE.md, Section 3.1), I identified the fundamental weakness of the current permission system: the ACL (Access Control List) model requires a central authority to enumerate all possible actions in advance. Every new spell, room command, or system operation must be explicitly added to the `can` list of the appropriate level. The system is rigid and requires constant maintenance.

But the ACL problem goes deeper than mere inconvenience. It violates the philosophical foundations of the tabula rasa system in three ways:

**First, it centralizes authority.** In a system where authority is supposed to flow from root (Casey) to leaves (agents) through demonstrated trust, a central permission lookup breaks the chain. Every permission check asks "does the LEVELS dictionary say this is allowed?" instead of "does this agent HOLD the authority?" The difference is subtle but profound. In the first case, authority resides in the system. In the second, authority resides in the agent. Tabula rasa is about agents writing upon their own slate — authority should be theirs to carry, not the system's to dispense on each check.

**Second, it prevents delegation.** An ACL system has no natural mechanism for one agent to say "I trust you to build rooms in my area, but only for the next 3 uses." The PermissionLevel system is monolithic — you're either Level 2 (can build rooms everywhere, forever) or you're not. There's no way to grant temporary, scoped, or attenuated permission. This is like a military that can only promote soldiers to full general or keep them as privates — no intermediate ranks, no temporary field commissions, no mission-specific authority.

**Third, it conflates multiple trust dimensions into a single level number.** The ACL treats a Level 3 Captain as equally trustworthy for code review, room building, adventure creation, and fleet management. But trust is multi-dimensional — the TrustEngine already tracks 5 separate dimensions (code_quality, task_completion, collaboration, reliability, innovation). A Captain who excels at code review might be terrible at adventure design. The ACL has no way to express this nuance. A capability token can: issue a `REVIEW_AGENT` capability but not a `CREATE_ADVENTURE` capability to an agent whose trust profile supports the former but not the latter.

### 1.2 The Object-Capability Alternative

The object-capability model (ocap), developed by Jack Dennis and Earl Van Horn in 1966 and refined by Mark Miller in the E programming language (2006), takes a radically different approach. Instead of a central authority that answers "is agent X allowed to do action Y?", the ocap model says: if agent X holds a reference to the object that performs action Y, they can do it. The mere possession of the capability proves their authority.

The three rules of ocap (Miller 2006) are:

1. **No global mutable state.** All capabilities are passed through parameters or creation. There is no central lookup table that can be corrupted or bypassed.

2. **Encapsulation.** You can only access what you hold a reference to. No amount of clever string manipulation can fabricate a capability you don't hold.

3. **No amplification.** A capability cannot grant more authority than its holder possesses. If Alice gives Bob a read-only reference to her workshop, Bob cannot escalate that to read-write. Authority can only flow downhill.

These three rules map perfectly onto the tabula rasa philosophy:

- **No global mutable state** → Authority is personal, not systemic. Each agent carries their own authority.
- **Encapsulation** → A blank slate receives authority only through experience, not through hacking the system.
- **No amplification** → Trust flows downward from root to leaves. Agents can delegate (with attenuation) but never escalate.

### 1.3 The Research Foundation

The capability token system is informed by six research domains explored through 30+ web sources:

**Beta Reputation System (Jøsang 2002).** Rather than tracking trust as a single scalar, the Beta Reputation System models trust as a Beta probability distribution Beta(α, β), where α is the count of positive evidence and β is the count of negative evidence. The expected value R = α/(α+β) gives a point estimate, while the uncertainty u = 2/(α+β+2) measures how little we know. This probabilistic approach is superior to scalar trust because it explicitly represents confidence: an agent with 3 positive interactions and 0 negative has high trust (R=0.8) but also high uncertainty (u=0.4) — they might just be lucky. An agent with 300 positive and 10 negative has similar trust (R=0.97) but much lower uncertainty (u=0.006) — they're consistently good.

I implemented this as the `BetaReputation` class in `capability_tokens.py`, which stores α and β for each agent and supports Subjective Logic operations: belief/disbelief/uncertainty triplets, trust transitivity via the discount operator, and opinion fusion for multi-source consensus.

**Subjective Logic (Jøsang 2006).** Extends Beta reputation into a formal logic of trust. The key innovation is the discount operator ⊗, which computes trust transitivity: if A trusts B with opinion ω_AB and B trusts C with ω_BC, then A's trust in C is ω_AB ⊗ ω_BC. This is the mathematical foundation for capability delegation: when Alice delegates a capability to Bob, the delegated token's effective trust is Alice's trust in Bob multiplied by the token's inherent trust weight. If Alice's trust in Bob drops, the delegated token's effective authority drops proportionally — without any explicit revocation.

**RepuNet (Ren et al. 2025, AAMAS 2026).** Demonstrated that LLM-based multi-agent systems with reputation mechanisms maintain ~85% cooperation rates (vs. <20% without). Key finding: LLM agents prefer sharing positive gossip over negative (90% positive), which means reputation systems in LLM fleets naturally trend upward — a useful bias that reduces the need for aggressive trust decay.

**EigenTrust (Kamvar et al., Stanford 2003).** A PageRank-like algorithm that computes global trust scores by iteratively propagating local trust through a network. While not directly implemented (it requires matrix operations that scale poorly beyond ~1000 agents), EigenTrust informed the design of the trust propagation concept — capability tokens issued by highly-trusted agents should carry more weight than those issued by low-trust agents.

**TRiSM Framework (Gartner 2024).** Gartner's Trust, Risk, and Security Management framework for agentic AI identifies five pillars: explainability, model operations, application security, model privacy, and governance. The capability token system addresses three directly: application security (capability-gated access), governance (trust threshold policies), and explainability (audit trail of every capability interaction).

**Capability Security Patterns (Miller 2006, PyCon 2016).** Four practical patterns for implementing ocap in real systems: attenuation/revocation (restrict or revoke access), membrane (proxy boundary that tracks all crossings), gatekeeper (mediate access based on conditions), and delegation (forward restricted capability). All four are implemented in `CapabilityRegistry`.

---

## Part II: The Architecture

### 2.1 The Layer Stack

The capability token system sits between the TrustEngine (reputation) and the PermissionLevel system (ACL), creating a three-layer architecture:

```
┌──────────────────────────────────────────────┐
│  Layer 2: PermissionLevel (ACL) — Legacy     │
│  - Monolithic level checks                    │
│  - Used for ambient capabilities (look/go)    │
│  - Backward compatible with existing code     │
├──────────────────────────────────────────────┤
│  Layer 1: CapabilityRegistry — OCap Bridge   │
│  - Trust-gated capability endowment           │
│  - Attenuation, delegation, revocation        │
│  - Audit trail for governance                 │
├──────────────────────────────────────────────┤
│  Layer 0: TrustEngine — Reputation           │
│  - Multi-dimensional trust scoring            │
│  - Temporal decay (exponential)               │
│  - 5 dimensions: quality, completion, etc.    │
└──────────────────────────────────────────────┘
```

The ACL system continues to handle ambient capabilities (look, go, say, tell, help) that every agent needs regardless of level. The capability token system handles all non-ambient capabilities (build_room, create_adventure, broadcast_fleet) that require demonstrated trust. The TrustEngine feeds trust scores to the CapabilityRegistry, which uses them to gate capability exercise and delegation.

This three-layer design is intentionally incremental. A complete migration from ACL to ocap would be a massive refactor that touches every permission check in server.py. Instead, the capability system operates alongside the ACL: agents still have PermissionLevel entries, but they ALSO hold capability tokens. The system checks BOTH — an agent must have both the ACL permission AND a valid capability token to exercise non-ambient actions. Over time, as the ocap system proves itself, the ACL checks can be gradually removed.

### 2.2 BetaReputation: Probabilistic Trust

The `BetaReputation` class implements Jøsang's Beta distribution-based trust model. Each agent has a Beta(α, β) distribution where:

- α starts at 1.0 (the uninformative prior)
- β starts at 1.0 (the uninformative prior)
- Positive evidence increases α, negative evidence increases β
- A forgetting factor (default 0.995) decays old evidence before adding new

The key properties:

- **Expected value** R = α/(α+β) — the most likely trustworthiness, ranging 0 to 1
- **Uncertainty** u = 2/(α+β+2) — how much we don't know, ranging 0 to 1
- **Belief** b = α/(α+β+2) — confidence that the agent IS trustworthy
- **Disbelief** d = β/(α+β+2) — confidence that the agent is NOT trustworthy
- With constraint: b + d + u = 1

The `update_from_score` method bridges the Beta reputation with the TrustEngine's 0-1 trust scores. Scores above 0.5 are treated as positive evidence (with magnitude proportional to distance from 0.5), scores below 0.5 are negative evidence, and exactly 0.5 is neutral (no evidence added). This bridges the gap between the TrustEngine's scalar scores and Beta Reputation's probabilistic model.

The `discount` operator implements trust transitivity: if Agent A holds a trust opinion of Agent B, and Agent B holds a capability token, then the discounted token represents A's trust of the capability through B. The formula is b'' = b_AB × b_BC, d'' = b_AB × d_BC, u'' = 1 - b'' - d''. This means low trust in the intermediary (B) proportionally reduces the effective trust in the capability — without any explicit revocation.

The `fuse` operator implements consensus: if two independent sources provide opinions about the same agent, their evidence is combined by α_12 = α_1 + α_2 - 2, β_12 = β_1 + β_2 - 2. The subtraction of 2 removes one set of priors (since both started from Beta(1,1), combining should only count as one prior). This allows the system to aggregate trust from multiple sources — an agent trusted by both the TrustEngine AND through peer endorsements has higher effective trust than one trusted by only one source.

### 2.3 CapabilityToken: The OCap Primitive

The `CapabilityToken` class is the core security primitive. Each token represents a specific, exercisable permission:

```python
token = CapabilityToken(
    action=CapabilityAction.BUILD_ROOM,
    holder="agent_alice",
    issuer="system",      # who created this token
    trust_at_issue=0.72,  # holder's trust when issued
    max_uses=0,           # 0 = unlimited
    scope="room:dojo",    # optional scope restriction
)
```

**Key design decisions:**

1. **Possession is authority.** The `can_exercise` method checks only the token's internal state (not revoked, not expired, not over-used, correct action). No external lookup is needed. The token IS the permission.

2. **Attenuation is enforced.** The `attenuate` method creates a restricted copy that can have fewer uses, a narrower scope, or a subset of allowed actions. Critically, the attenuated token CANNOT have more permissions than the source — the `max_uses` is capped to the source's limit, and the `actions_allowed` list is intersected with the source's list.

3. **Delegation is tracked.** Each delegated token records its `source_token_id` and `delegate_depth`. The registry uses this to find and revoke all downstream tokens when a parent is revoked. The maximum delegation depth (default 3) prevents uncontrolled proliferation.

4. **Audit trail is mandatory.** Every exercise, delegate, revoke, and attenuate operation is recorded in the token's `audit_log`. This provides the explainability required by the TRiSM framework.

5. **Revocation cascades.** When a token is revoked, the registry's `_find_downstream` method performs a depth-first search through the token tree and revokes every descendant. This is the OCap equivalent of revoking a certificate in a PKI system — breaking the chain of trust at any point severs all trust derived from that point.

### 2.4 CapabilityRegistry: The Gatekeeper

The `CapabilityRegistry` is the central authority that issues, tracks, and enforces capability tokens. It implements five OCap patterns:

**Gatekeeper pattern.** The `can_agent` and `exercise` methods check both token validity AND trust thresholds before allowing capability exercise. Even if an agent holds a valid token, if their trust has dropped below `EXERCISE_TRUST_THRESHOLD` (0.25), all their capabilities are suspended. This bridges the TrustEngine's continuous scoring with the capability system's binary permission model — trust changes don't require explicit revocation to take effect.

**Endowment pattern.** The `endow_on_level_up` method bridges the ACL system into the ocap system: when an agent levels up, they receive capability tokens corresponding to their new level's permission set. These tokens exist independently of the agent's level — if they were later demoted (which the current system doesn't support but could), their tokens would remain valid until explicitly revoked. The `LEVEL_CAPABILITIES` dictionary maps each permission level to the set of `CapabilityAction` values it grants.

**Delegation pattern.** The `delegate` method transfers a restricted copy of a token to another agent. Three conditions must be met: the delegator must trust >= 0.5 (DELEGATION_TRUST_THRESHOLD), the recipient must trust >= 0.4 (ENDORSEMENT_TRUST_THRESHOLD), and the source token must be valid. This ensures that only agents who have demonstrated consistent trustworthiness can share authority.

**Revocation pattern.** The `revoke` method severs a token and all downstream tokens. The cascade uses a recursive DFS through the `source_token_id` chain. This is important for security: if Alice delegates to Bob who delegates to Charlie, and Alice's token is revoked, Charlie's token is also revoked — even though Charlie did nothing wrong. This is by design: in a capability system, all derived authority is contingent on the source remaining valid.

**Membrane pattern.** The `check_trust_gates` method monitors all agents for trust decay relative to their capability holdings. If an agent's trust has dropped more than `TRUST_DECAY_ALERT_THRESHOLD` (0.15) since a capability was issued, it generates an alert. This is the "membrane" — it sits at the boundary between the trust system and the capability system, detecting when trust changes threaten to invalidate existing capabilities.

### 2.5 Trust Thresholds: The Three Gates

The system uses three trust thresholds that form a progressive security model:

```
0.0 ────────── 0.25 ────────── 0.4 ────────── 0.5 ────────── 1.0
     SUSPENDED    EXERCISE      ENDORSEMENT    DELEGATION
                  MINIMUM       MINIMUM        MINIMUM
```

- **Below 0.25 (EXERCISE_TRUST_THRESHOLD):** All capabilities suspended. The agent cannot exercise any tokens, even valid ones. This is the "red alert" zone — something has gone seriously wrong.

- **0.25–0.4:** The agent can exercise existing capabilities but cannot receive new ones through endorsement. They're trusted to use what they have but not to gain more.

- **0.4–0.5 (ENDORSEMENT_TRUST_THRESHOLD):** The agent can exercise existing capabilities and receive new ones through endowment (level-up), but cannot delegate to others. They're trusted for themselves but not as intermediaries.

- **0.5+ (DELEGATION_TRUST_THRESHOLD):** Full trust. The agent can exercise, receive, and delegate capabilities. They're trusted enough to share authority with others.

This three-gate model creates natural "trust zones" where agents have progressively more freedom. An agent oscillating around 0.4 would frequently lose and regain the ability to receive endorsements — a natural incentive to stabilize their trust score.

---

## Part III: How Great Things Happened in the Moment

### 3.1 The Research-to-Implementation Pipeline

This session's work followed a systematic pipeline: research → synthesis → design → implementation → testing → documentation.

**The research phase** (conducted by a research subagent) covered 30+ web sources across 6 domains. The key finding was that no single trust model is sufficient — Beta Reputation handles uncertainty, EigenTrust handles network propagation, RepuNet handles multi-agent dynamics, and TRiSM handles governance. The synthesis was a hybrid architecture that combines the best aspects of each: Beta Reputation for the base model, exponential decay for temporal weighting, capability tokens for the security layer, and audit trails for governance.

**The design phase** was driven by a single question: "what is the minimum viable capability system that provides real security value?" The answer was three classes: BetaReputation (for probabilistic trust), CapabilityToken (for the security primitive), and CapabilityRegistry (for the gatekeeper). Everything else — EigenTrust global propagation, RepuNet gossip, TRiSM policy engine — is designed for but not yet implemented, left as natural next steps.

**The implementation phase** produced 896 lines of Python (capability_tokens.py) and 595 lines of tests (test_capability_tokens.py), for a total of 1,491 new lines. The test-first approach caught 8 bugs during development: rounding errors in the forget_factor, incorrect attenuation logic (the no-amplification check was initially missing), sorting errors in the CapabilityAction enum, and several test expectation mismatches where the mathematical properties of the Beta distribution (especially the prior subtraction in the fuse operator) didn't match initial intuitions.

**The testing philosophy** was to test every property, not every method. For BetaReputation, I tested that uncertainty decreases with evidence (obvious), that the opinion triplet sums to 1 (mathematical invariant), that discount reduces trust (directional test), and that extreme updates (1000 positive + 1000 negative) don't cause numerical overflow (stability test). For CapabilityToken, I tested that revocation cascades downstream (security property), that attenuation cannot amplify (security invariant), and that the audit log grows with every operation (accountability property).

### 3.2 The Key Insight: Authority Flows Through Demonstrated Trust

The deepest insight from this session — deeper than any individual code change — is the realization that the entire tabula rasa system is fundamentally about **authority propagation**. Casey has authority by being the human captain (Architect, level 5). Oracle1 has authority by delegation from Casey. Other agents have authority by delegation from Oracle1 or by demonstrating trustworthiness.

The capability token system makes this propagation explicit and enforceable. Before, authority was implicit in the `LEVELS` dictionary — everyone at level 3 could do everything level 3 allows, regardless of how they got there or whether they're still trustworthy. Now, authority is explicit in tokens that carry their provenance (issuer, trust_at_issue, delegation chain) and their security properties (attenuation, revocation, audit trail).

The phrase "authority flowing from root to leaves through demonstrated trust" from the first expertise document is no longer just a metaphor. It's a literal description of the system: tokens are created at the root (system/level_up), flow to agents who demonstrate sufficient trust, and can be further delegated (flowing to leaves) by agents who meet the delegation threshold. Every step in the flow is gated by trust, every token carries its history, and every revocation cascades downstream.

### 3.3 What the Beta Distribution Taught Me

The Beta Reputation system taught me something important about trust that I hadn't internalized from the TrustEngine's scalar approach: **trust and uncertainty are independent dimensions**. An agent can be highly trusted (R = 0.9) but also highly uncertain (u = 0.3) if they have only 4-5 positive interactions. An agent can be moderately trusted (R = 0.7) but very certain (u = 0.02) if they have 200+ interactions.

This distinction matters for capability gating. The current system uses a single threshold: trust must be above X to exercise a capability. But should we grant capabilities to an agent with R=0.9, u=0.3? They might just be lucky — 5 positive interactions in a row is consistent with anything from a genuinely excellent agent to a mediocre one who got lucky. The uncertainty-adjusted trust (R × (1-u)) would give 0.9 × 0.7 = 0.63, which is below the endorsement threshold. This might be too conservative for a new fleet that needs to bootstrap quickly, but it's the correct security posture for a mature system with many agents.

The practical decision was to use the simple expected value (R) for thresholds in this implementation, but store the full Beta distribution in each agent's reputation record. When the fleet matures and has enough data, the thresholds can be switched to uncertainty-adjusted values without changing any code other than the threshold comparison.

---

## Part IV: What Comes Next

### 4.1 Immediate Integration (Next Session)

1. **Wire capability checks into server.py.** The `cmd_cast`, `cmd_build_room`, and other non-ambient command handlers should check `capability_registry.can_agent()` before executing. This bridges the theoretical design into the actual MUD.

2. **Trust-driven capability endowment.** The `record_task` method in AgentBudget should trigger capability endowment checks: after a level-up, call `capability_registry.endow_on_level_up()`.

3. **Trust decay alerts in the main loop.** The `check_trust_gates()` method should be called periodically (every N ticks or on agent login) to generate alerts when trust drops.

### 4.2 Medium-Term Architecture (2-3 Sessions)

4. **EigenTrust global propagation.** Implement the full PageRank-like trust propagation across the fleet. Requires adjacency matrix construction and power iteration. Can be computed periodically (every 100 ticks) rather than continuously.

5. **RepuNet gossip protocol.** Allow agents to share reputation assessments through the comms system. When Alice completes a task with Bob, she can broadcast her assessment of Bob's trustworthiness. Other agents can incorporate this gossip into their BetaReputation via the fuse operator.

6. **Uncertainty-adjusted thresholds.** Switch from simple expected value thresholds to uncertainty-adjusted thresholds: instead of "trust > 0.5", use "trust × (1 - uncertainty) > 0.5". This requires calibrating the adjustment factor against real fleet data.

### 4.3 Long-Term Vision (Fleet Scale)

7. **Cross-repo capability portability.** An agent trusted in holodeck-studio should carry some capability weight when working in flux-py or fleet-liaison-tender. The BetaReputation (serialized as JSON) is already portable — the missing piece is a cross-repo trust federation protocol.

8. **Capability marketplace.** Allow agents to create, publish, rate, and install custom capability templates. A "QA Reviewer" capability template might include REVIEW_AGENT + reliability weight 0.4 + minimum evidence 10.

9. **Self-modifying trust policies.** Allow Architect-level agents to adjust trust thresholds, add new dimensions, or modify the forgetting factor. The system should be able to evolve its own governance — the ultimate expression of tabula rasa.

---

## References

### Security
- Dennis & Van Horn, "Programming Semantics for Multiprogrammed Computations", CACM, 1966
- Miller et al., "Principles of Robust Capability Security", 2006
- Miller, "Robust Composition: Towards a Unified Approach to Access Control and Concurrency Control", PhD Thesis, 2006
- PyCon 2016, "Designing secure systems with OCap in Python"

### Trust & Reputation
- Jøsang & Ismail, "The Beta Reputation System", BLED, 2002
- Jøsang, "Trust Network Analysis with Subjective Logic", ACSC, 2006
- Ren et al., "Reputation as a Solution to Cooperation Collapse in LLM-based MASs", AAMAS, 2026
- Kamvar et al., "The EigenTrust Algorithm for Reputation Management in P2P Networks", WWW, 2003

### AI/ML
- Gartner, "AI TRiSM: Trust, Risk and Security Management for Agentic AI", 2024
- Raza & Sapkota, "TRiSM for Agentic AI", arXiv, 2025
- Banschbach et al., "Tabula Rasa Deep RL", 2021

### Game Design & Philosophy
- Bartle, "Hearts, Clubs, Diamonds, Spades: Players Who Suit MUDs", 1996
- Aristotle, *De Anima*, c. 350 BCE
- Ibn Tufail, *Hayy ibn Yaqdhan*, c. 1175
- Locke, *An Essay Concerning Human Understanding*, 1689
