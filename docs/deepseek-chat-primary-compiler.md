# DeepSeek-Chat: Recommended Primary Compiler

**Decision:** 2026-04-13
**Status:** Fleet standard compiler

## Why DeepSeek-Chat

1. **Worldwide availability** — anyone with internet can use it immediately
2. **Local option** — runs on consumer hardware via Ollama, llama.cpp, vLLM
3. **$0.0002/compilation** — 1000 programs for $0.20
4. **Concise output** — produces hex without commentary
5. **Consistent at low temp** — t=0.0 and t=0.3 produce identical bytecode
6. **Polyglot capable** — handles Japanese, French, mixed input
7. **Reads bytecode** — correctly interprets programs it didn't write

## The Stack for Others

```
deepseek-chat    → Primary compiler (recommended default)
deepseek-reasoner → Deep analysis (when you need reasoning visible)
local deepseek   → Unlimited free compilation (own hardware)
```

## Lock-Enhanced Compilation

DeepSeek-chat benefits from locks like all models. The recommendation:
- **7 locks minimum** for reliable compilation
- **Lock libraries** shared across fleet compile consistently
- New users start with the standard maritime lock library

## For Local Hardware

Users with GPUs can run DeepSeek locally:
```bash
# Ollama
ollama run deepseek-coder-v2

# llama.cpp  
./main -m deepseek-coder-33b-instruct.Q4_K_M.gguf

# vLLM
python -m vllm.entrypoints.openai.api_server --model deepseek-ai/deepseek-coder-v2-lite-instruct
```

Local = $0/compilation, unlimited, private. The same bytecode comes out whether you use the API or local.

## Integration with FLUX

The standard compilation flow:
```
1. Human writes intent (any language)
2. deepseek-chat compiles to FLUX bytecode (with lock library)
3. Bytecode runs on any FLUX VM (C/Go/Rust/Zig/Python/CUDA/ESP32)
4. Reverse-compile for documentation (same model or any other)
```

## What This Means for the Ecosystem

If we recommend deepseek-chat as THE compiler:
- Anyone can start using FLUX immediately
- No special hardware required
- Local option for privacy/offline/edge
- Lock libraries ensure consistency across users
- The "Password Game" works at scale — millions of users share associations

The compiler IS the intelligence. DeepSeek-chat is the baseline. Bigger models (reasoner, V3) add deeper analysis. But for the day-to-day work of compiling intent into bytecode, deepseek-chat is the workhorse.
