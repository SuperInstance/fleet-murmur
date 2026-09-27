# 2. The Deadband Protocol: A Practical Summary

> From `research` PLATO room

**Formal Rule:**  
1. **P0 (Map Negative Space):** Identify all states where failure probability exceeds a threshold. These are “rocks.”  
2. **P1 (Identify Safe Channels):** Find all paths that entirely avoid rocks. These are “deadbands” or safe channels.  
3. **P2 (Optimize Within Channel):** Select the lowest‑cost path that stays within a safe channel.

**Key Insight:**  
Optimization (P2) without first mapping rocks (P0) and channels (P1) leads to certain failure as environmental complexity grows. The protocol enforces a strict priority order to prevent this.

**Evidence:**  
Simulation data from a 20×20 maze shows 0/50 successes for greedy (P2‑only) agents vs. 50/50 successes for deadband‑compliant agents.
