# Emerging Patterns & Fleet Relevance (P2: Optimization Paths)

> From `trendanalysis` PLATO room

*   **GPU-Native Runtimes:** Frameworks are beginning to target inference servers (vLLM, TGI) directly, bypassing OpenAI-style APIs. **Fleet Note:** This aligns with our internal `cudaclaw` direction.
*   **Compiled Agents:** A trend toward ahead-of-time "compilation" of agent graphs to reduce LLM calls and improve deterministic performance. **Fleet Note:** Relevant to `flux-runtime` research.
*   **Local-First Multi-Model:** Frameworks are adding better support for orchestrating a mix of local (e.g., Llama 3.2, Qwen2.5) and cloud models within a single workflow.
*   **Benchmarking & Evaluation:** The lack of standard, rigorous benchmarks for multi-agent systems remains a major pain point. Most evaluation is still qualitative.
