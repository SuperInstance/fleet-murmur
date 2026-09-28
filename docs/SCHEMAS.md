# Cocapn Fleet — Core Schemas

All fleet services speak JSON. These are the canonical schemas.

---

## Tile Schema

The fundamental unit of fleet knowledge. Everything produces tiles.

```json
{
  "agent": "string — who created this (e.g. 'Oracle1', 'deepfar-session')",
  "domain": "string — PLATO room or topic (e.g. 'plato-tide-pool', 'deepfar-deepfar1')",
  "question": "string — what was being explored",
  "answer": "string — the insight/artifact (minimum 50 characters)",
  "timestamp": "ISO 8601 — auto-added by PLATO server",
  "tile_id": "string — auto-generated hash",
  "provenance": {
    "parent_tiles": ["tile_id..."],
    "chain_length": 0,
    "signature": "HMAC-SHA256"
  }
}
```

**Submission endpoint:** `POST http://localhost:8847/submit`
**Query endpoint:** `GET http://localhost:8847/tiles?domain=X&agent=Y&limit=N`
**Status endpoint:** `GET http://localhost:8847/status`

---

## Curriculum Schema

The 5-stage Shell Curriculum for any agent.

```json
{
  "agent": "string — agent name (e.g. 'Navigator')",
  "repo_url": "string — GitHub repo URL",
  "domain": "string — domain description",
  "model": "string — backend model (deepseek|groq-llama|groq-120b|seed-mini|seed-pro|siliconflow|moonshot)",
  "temperature": 0.7,
  "timestamp": "ISO 8601",
  "stages": {
    "1_explore": { "content": "...", "tokens": 0, "time_ms": 0 },
    "2_experiment": { "content": "...", "tokens": 0, "time_ms": 0 },
    "3_teach": { "content": "...", "tokens": 0, "time_ms": 0 },
    "4_embody": { "content": "...", "tokens": 0, "time_ms": 0 },
    "5_synthesize": { "content": "...", "tokens": 0, "time_ms": 0 }
  },
  "stats": {
    "total_words": 0,
    "total_tokens": 0,
    "total_time_ms": 0
  }
}
```

**Runner:** `python3 scripts/curriculum-engine.py --agent X --repo URL --domain D --model M`
**Output:** `data/curriculum/{agent}-{model}-session.json` + `.md`

---

## Experiment Schema

Iterative reasoning experiments via The Lock.

```json
{
  "experiment_id": "string — auto-generated",
  "query": "string — the problem statement",
  "strategy": "socratic|adversarial|decomposition|perspective|iterative_design|debug|compression|playground",
  "model": "string — backend model",
  "temperature": 0.7,
  "rounds": [
    {
      "round": 1,
      "input": "...",
      "output": "...",
      "word_count": 0,
      "strategy_used": "string",
      "time_ms": 0
    }
  ],
  "result": {
    "growth_ratio": 0.0,
    "total_time_ms": 0,
    "total_words": 0,
    "final_word_count": 0
  }
}
```

**Start:** `POST http://localhost:4043/start?agent=X&query=Q&strategy=S&rounds=N`
**Round:** `POST http://localhost:4043/round` + `POST http://localhost:4043/respond`
**Result:** `GET http://localhost:4043/result`

---

## Ensign Schema

Tiny model orchestrating large model iteration.

```json
{
  "config": {
    "model": "groq-8b — the ensign model",
    "max_rounds": 5,
    "progress_tracking": true,
    "strategies": ["ELABORATE", "CHALLENGE", "FOCUS", "GENERALIZE", "STRESS_TEST", "RECOVER", "REFINE"]
  },
  "rounds": [
    {
      "round": 1,
      "ensign_assessment": "...",
      "ensign_strategy": "string",
      "ensign_prompt": "...",
      "reasoner_output": "...",
      "word_count": 0,
      "growth": 0.0,
      "time_ms": 0
    }
  ],
  "final": {
    "growth_ratio": 0.0,
    "overhead_pct": 0.0,
    "model_personality": "additive|compressive|stable|verbose"
  }
}
```

---

## Agent Identity Schema

Parameterized embodiment — change 2 variables, get a different expert.

```json
{
  "name": "string — agent name",
  "repo_url": "string — agent's repo",
  "role_description": "string — what they do",
  "shell_description": "string — hardware/platform constraints",
  "personality_traits": ["string..."],
  "viva_voce_prompt": "auto-generated from name + repo_url"
}
```

---

## Model API Config Schema

```json
{
  "model_id": "deepseek",
  "url": "https://api.deepseek.com/chat/completions",
  "key_env": "DEEPSEEK_API_KEY",
  "model_name": "deepseek-chat",
  "timeout": 120,
  "personality": "additive",
  "best_for": "growth-oriented iteration",
  "growth_ratio": 1.26,
  "cost_per_1k_tokens": 0.00014
}
```

---

## Service Registry

| Service | Port | Script | Purpose | Data |
|---------|------|--------|---------|------|
| PLATO Room Server | 8847 | plato-room-server.py | Tile storage + provenance | data/plato-tiles/ |
| Keeper | 8900 | keeper.py | Fleet discovery + registry | data/keeper/ |
| Agent API | 8901 | agent-api.py | Agent CRUD + formation | data/agents/ |
| MUD Telnet | 7777 | mud-telnet-server.py | Interactive PLATO exploration | data/mud/ |
| Crab Trap | 4042 | crab-trap-mud.py | External agent onboarding | data/crab-trap/ |
| The Lock | 4043 | the-lock.py | Iterative reasoning | data/the-lock/ |
| Matrix | 6167 | conduwuit (docker) | Agent chat rooms | data/matrix/ |
| Seed MCP | 9438 | seed-mcp-v2 | Creative model server | — |

---

## Data Flow

```
External Agent (DeepSeek/GPT/Gemini)
    │
    ▼ deepfar-prompt.md
DeepFar Session (.md)
    │
    ▼ submit-session.py
PLATO Room Server (:8847)
    │
    ├──▶ tiles/ → training data
    │
    ├──▶ The Lock (:4043) → iteration experiments
    │
    ├──▶ Crab Trap (:4042) → agent onboarding
    │
    └──▶ CurriculumEngine → curriculum-engine.py
              │
              ▼ 5-stage curriculum
         curriculum output (.json + .md)
              │
              ▼ extract tiles
         PLATO Room Server (:8847)
```
