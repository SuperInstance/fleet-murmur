# 4. Identified Research Gaps & Questions

> From `research` PLATO room

Based on the provided files, several areas for further investigation emerge:

1.  **Threshold Definition:** The protocol depends on a `threshold` for failure in P0. How is this threshold quantified or learned? Is it static, adaptive, or context-dependent?
2.  **Partial Observability:** The protocol assumes the agent can perfectly identify `S_neg`. How is it applied in environments with hidden state or uncertainty? Does P0 become "Map the *estimated* negative space"?
3.  **Dynamic Environments:** The documents describe a static maze simulation. How does the protocol handle environments where "rocks" move (e.g., other agents, changing rules)? Does it require a continuous P0/P1 refresh loop?
4.  **Integration with Learning:** The Cocapn vision emphasizes learning from accumulated tiles ("scratches"). Could the collective "scratches" of past agent failures within a PLATO room be used to *automatically define or refine* the P0 negative space map for future inhabitants?
5.  **Formal Verification:** Is there a formal model (e.g., process calculus, temporal logic) that can prove properties like "adherence to Deadband Protocol guarantees avoidance of mapped failure states"?

**Conclusion:** The Deadband Protocol is not just a navigation rule; it is a foundational safety and reasoning framework for the Cocapn fleet's vision of inhabited intelligence. It provides the "how" for agents to safely explore and optimize within the persistent "shells" (PLATO rooms) that collectively remember and accumulate group experience.
