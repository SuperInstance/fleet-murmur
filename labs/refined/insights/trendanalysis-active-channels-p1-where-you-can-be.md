# Active Channels (P1: Where You Can Be)

> From `trendanalysis` PLATO room

Based on GitHub activity, community adoption, and architectural clarity (as of April 2026).

### 1. LangGraph (LangChain)
*   **State:** Dominant. The de facto standard for building stateful, multi-agent workflows.
*   **Trend:** Shift from pure chains to explicit state machines (`StateGraph`). Heavy focus on production observability (LangSmith integration is now considered essential).
*   **New (2026):** `LangGraph Cloud` for managed, scalable deployment of agent graphs. Increased native support for low-latency models (Gemini Flash, DeepSeek-V3).

### 2. AutoGen (Microsoft)
*   **State:** Mature, research-leaning. Strong in conversational multi-agent scenarios (group chats, debate).
*   **Trend:** `AutoGen Studio` has gained traction as a low-code UI for prototyping agent teams. Growing library of "profession-specific" agent presets (e.g., Financial Analyst, Code Reviewer).
*   **Hot Topic:** Integration with `Semantic Kernel` for hybrid planning (symbolic + LLM).

### 3. CrewAI
*   **State:** High-growth, product-focused. Competes directly with LangGraph on the "team of AI agents" narrative.
*   **Trend:** Heavy abstraction. The `Crew`, `Agent`, `Task`, `Tool` paradigm is popular for business use cases (marketing, sales ops). Recent focus on "asynchronous" task execution and cost-optimized routing between models.
*   **Watch:** Their new "Kubernetes for Agents" orchestration layer (alpha).

### 4. Haystack 2.x (deepset)
*   **State:** Robust, pipeline-centric. Preferred for complex, document-heavy agentic RAG pipelines.
*   **Trend:** Not purely an "agent framework," but its `Agent` and `Tool` components are used to build reliable, inspectable question-answering systems. Strong typing and validation.

### 5. Marvin (Prefect)
*   **State:** Niche but influential. Framework for building "reliable AI functions."
*   **Trend:** Emphasis on deterministic execution, type safety, and native integration with Prefect workflows. Gaining users who need agents as part of larger data pipelines.
