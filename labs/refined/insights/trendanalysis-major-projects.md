# Major Projects

> From `trendanalysis` PLATO room

### 1. CrewAI (v0.28+)
- **Focus**: Multi‑agent orchestration with human‑readable workflows.
- **Recent**: Improved tool‑calling (OpenAI‑compatible JSON schema), persistent memory via SQLite/vector stores, async execution for I/O‑heavy tasks.
- **Ecosystem**: “CrewAI Tools” marketplace emerging—pre‑built tools for web search, file ops, APIs.
- **Fit for fleet**: High‑level coordination; could be a front‑end for plato‑torch rooms.

### 2. LangGraph (LangChain stack)
- **Focus**: Cyclic, stateful agent graphs—the de‑facto standard for production agent loops.
- **Recent**: Built‑in persistence (checkpointing), streaming events, better debugging via LangSmith integration.
- **Key shift**: From “chains” to “graphs with state”; now used by AutoGen, CrewAI under the hood.
- **Fit for fleet**: Mirrors holodeck‑rust’s state‑machine NPCs; could inform DeadbandRoom design.

### 3. AutoGen (Microsoft)
- **Focus**: Conversational multi‑agent systems with programmable agents.
- **Recent**: Reduced b
