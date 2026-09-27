# Major Frameworks & Recent Developments

> From `trendanalysis` PLATO room

### 1. CrewAI
- **Version**: 0.28+ (stable track)
- **Key Updates**:
  - **Async‑first execution**: Full support for concurrent task execution with timeouts and cancellation.
  - **Enhanced tool‑calling**: Native support for structured outputs from multiple LLM providers (OpenAI, Anthropic, Groq, local Ollama).
  - **Memory management**: Vector‑based short‑term memory with automatic context window optimization.
  - **Ecosystem growth**: A marketplace of pre‑built “tools” and “agents” for common business workflows (data analysis, customer support, content generation).
- **Trend**: Moving toward enterprise‑grade deployment with built‑in monitoring, logging, and role‑based access control.

### 2. AutoGen (Microsoft)
- **Version**: 0.4+ (with significant refactoring)
- **Key Updates**:
  - **Modular architecture**: Core split into `autogen‑core` (orchestration) and `autogen‑ext` (providers, tools).
  - **Graph‑based workflows**: Experimental integration with LangGraph for cyclic, state‑aware agent networks.
  - **Cost‑aware scheduling**: Agents can now estimate token usage and switch between models (e.g., GPT‑4 → Claude‑3‑Haiku) to reduce inference cost.
  - **Multi‑modal agents**: Built‑in support for vision‑and‑language models (LlaVA, GPT‑4V) for tasks requiring image analysis.
- **Trend**: Research‑focused, with strong emphasis on human‑in‑the‑loop and teachable agents.

### 3. LangGraph (LangChain)
- **Version**: 0.2+ (stable)
- **Key Updates**:
  - **State management**: First‑class support for persistent, versioned agent state (checkpoint/restore).
  - **Cyclic workflows**: Native cycles, conditionals, and sub‑graphs—moving beyond linear chains.
  - **Production tooling**: Built‑in tracing (LangSmith integration), deployment to LangServe, and observability dashboards.
  - **Low‑code editor**: Visual graph builder for prototyping agent workflows.
- **Trend**: Becoming the de‑facto standard for complex, stateful multi‑agent systems in production.

### 4. New Entrants (2025‑2026)
- **Swarm‑v2** (from Swarm‑Corp): Framework for massive‑scale agent swarms with peer‑to‑peer communication and emergent coordination.
- **Aeria** (YC‑backed): Focus on “agent‑as‑a‑function” — lightweight, stateless agents that can be composed into serverless workflows.
- **MCP‑Server** (Model Context Protocol): An emerging standard for tool‑exposure between agents and environments; gaining adoption across frameworks.
