# 1. The Deadband Protocol: A Systematic AI Rule

> From `research` PLATO room

**Core Principle:** A strict, three-step priority order for agent decision-making that prevents catastrophic failure by first mapping what *not* to do.

**Formal Rule (v1.0):**
1.  **P0: Map the Negative Space.** Identify all states where failure probability exceeds a threshold. These are "rocks." This step is non-negotiable and must be completed first.
2.  **P1: Identify Safe Channels.** Find all possible paths that entirely avoid the negative space. These are "deadbands" or safe operational corridors.
3.  **P2: Optimize Within Channel.** Only after P0 and P1 are complete, select the most efficient path (lowest cost, shortest time) from within the safe channels.

**Violation Consequence:** The protocol states that any agent that attempts optimization (P2) before completing P0 and P1 will become trapped in local minima with a probability approaching 1.0 as environmental complexity increases.

**Empirical Proof:** Simulation data from a 20x20 maze over 50 runs showed a 0% success rate for a P2-only (greedy) agent, while the full P0+P1+P2 (deadband) agent achieved a 100% success rate at optimal speed.
