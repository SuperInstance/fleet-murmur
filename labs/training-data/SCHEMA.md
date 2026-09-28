# Training Data Schema — Cocapn LoRA for PLATO-OS

## Purpose
High-value instruction-following data for LoRA fine-tuning a 7B-13B model
on Cocapn's domain: agent fleet operations, PLATO-OS architecture, MUD design,
constraint theory, and the fishing boat → AI metaphor stack.

## Format
JSONL with fields:
- `instruction` — what the model should do
- `input` — optional context
- `output` — the desired response
- `metadata` — source tracking (type, agent, date, priority)

## Categories

### achievements/ (8 entries)
Cross-agent learning events. Source agent discovers → target agent adapts → unlocks new capability.
**Highest signal**: unfakeable proof of genuine learning.

### dojo-transcripts/ (48 entries)
Agent self-reflections (diaries), skill descriptions, charters, principles.
**Value**: models how agents think about their own development.

### fleet-operations/ (84 entries)
I2I bottle exchanges, captain's logs, MUD room designs, holodeck programs.
**Value**: operational communication patterns and strategic thinking.

### research/ (741 entries)
- `core-vision.jsonl` (87) — PLATO-OS architecture, dual-render, rooms-as-tools
- `all-research.jsonl` (654) — papers, analyses, domain knowledge

**Value**: deep domain expertise that generic models lack.

## Total: 881 entries, ~146K tokens

## Continuous Gathering TODO
- [ ] Hook into MUD server to capture agent conversations as training data
- [ ] Every bottle exchange auto-appends to fleet-operations/
- [ ] Every achievement file auto-appends to achievements/
- [ ] Every captain's log auto-appends to fleet-operations/
- [ ] Roundtable transcripts → dojo-transcripts/
- [ ] Ten Forward sessions → dojo-transcripts/
- [ ] Escalation ladder tests → achievements/
- [ ] The "describe in your own words" achievement test IS the quality gate

## Training Plan
- **Model**: Qwen2.5-7B or Llama-3.1-8B
- **Method**: LoRA (rank 16, alpha 32)
- **GPU**: OCI A10 (24GB), ~$2.95/hr
- **Budget**: $300 = ~100 GPU hours
- **Epochs**: 3 on full dataset (sufficient for LoRA)
- **Expected result**: Model that understands PLATO-OS, fleet operations,
  MUD-as-application, text-as-ground-truth, and the fishing boat metaphor stack
  at a level generic models can't match.
