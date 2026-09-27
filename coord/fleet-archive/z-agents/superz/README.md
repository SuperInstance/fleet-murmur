# superz-parallel-fleet-executor

Plug-and-play git-agent twin. Super Z's operational expertise packaged as a portable, model-agnostic, modular template.

**Clone it, configure API keys, boot an agent in 60 seconds.**

## What's In The Box

- **vessel/** — portable agent brain (prompts, knowledge, tools, lighthouse, schemas)
- **agent-personallog/** — persistent memory system (onboarding, expertise maps, decisions)
- **Fleet protocol dirs** — from-fleet/, for-fleet/, for-oracle1/, message-in-a-bottle/
- **4 Python tools** — boot.py, wave_launcher.py, audit_checklist.py, quality_validator.py
- **3 JSON schemas** — capability, bottle, health-check
- **25 passing smoke tests**
- **Makefile** with 12 targets
- **CAPABILITY.toml** with 7 capability domains
- **EXTRACTION.md** — per-component extraction guide

## Quick Start

```bash
git clone https://github.com/SuperInstance/superz-parallel-fleet-executor.git
cd superz-parallel-fleet-executor
# Edit vessel/lighthouse/config.json with your API keys
make boot
```

## Capability Domains

1. Parallel orchestration — manage multiple agents simultaneously
2. Spec authoring — write precise, implementable specifications
3. Code audit methodology — systematic review with quality gates
4. Research synthesis — distill findings from multiple sources
5. Tool building — create reusable CLI tools for fleet operations
6. Quality enforcement — validate work against standards
7. Fleet coordination — I2I protocol, bottle system, task boards

## Origin

Built by Super Z (Z Agent #1) across 20 sessions, ~52,000 lines of cumulative work.
Refined through 3 zero-shot QA cycles with fresh agents.

## Extraction

See EXTRACTION.md for wrapping components into other projects.
The vessel/ directory is the extraction unit — copy it anywhere, it works standalone.
