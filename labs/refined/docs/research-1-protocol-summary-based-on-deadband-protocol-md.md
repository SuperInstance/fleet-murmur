# 1. Protocol Summary (Based on `DEADBAND-PROTOCOL.md`)

> From `research` PLATO room

The Deadband Protocol is a three-step, strictly prioritized decision-making framework for autonomous agents. Its formal rule states:

1.  **P0: Map the Negative Space.** Identify all states `S_neg` where the probability or cost of failure exceeds a defined threshold. These are "rocks." This step is mandatory and must be completed before proceeding.
2.  **P1: Identify Safe Channels.** Find all possible paths `P` where every state `s` along the path is *not* in `S_neg`. These permissible corridors are "deadbands" or "safe channels."
3.  **P2: Optimize Within Channel.** Only after P0 and P1 are complete, select the optimal path `P*` from within the set of safe channels `C`, minimizing cost subject to the constraint `P ⊆ C`.

**Key Insight:** The protocol asserts that an agent which optimizes (P2) before completing the mapping steps (P0+P1) will, with high probability, become trapped in local minima or fail catastrophically as environmental complexity increases. Simulation data (a 20x20 maze, 50 runs) is cited as evidence: a P2-only (greedy) strategy succeeded 0 times, while the full P0+P1+P2 strategy succeeded 50 times.
