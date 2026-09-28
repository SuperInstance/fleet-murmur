# Abstraction Planes — Quick Reference Card

## The Stack (high to low)

| # | Name | Format | Example | For Who |
|---|------|--------|---------|---------|
| 5 | Intent | Natural language | "Navigate east 10 knots" | Humans, strategists |
| 4 | Domain Language | Structured notation | `HEADING[R0]=EAST SPEED[R5]=10` | Fleet coordination, MUD |
| 3 | Structured IR | JSON/YAML + types | `{"op":"MOVI","args":[0,1]}` | Verification, protocols |
| 2 | Bytecode | FLUX hex | `10 01 01 10 05 0A` | VMs, interpreters, sandboxes |
| 1 | Native | C/Rust/Zig source | `fn navigate(h: u8, s: u8)` | Edge, daemons, performance |
| 0 | Bare Metal | Assembly/firmware | `MOVI R0, #1` | ESP32, GPU, interrupts |

## Diminishing Returns

```
5→4: HIGH VALUE (82% compression, consistency)
4→3: MEDIUM (type safety, verification)
3→2: MEDIUM (portability)
2→1: LOW-MEDIUM (performance, costs engineering)
1→0: LOW for most (only for constrained hardware)
```

**Default working level: Plane 4.** Go deeper only with reason.

## Key FLUX Opcodes

| Name | Hex | Function |
|------|-----|----------|
| MOVI | 0x10 | Load immediate to register |
| MOV | 0x11 | Register to register |
| IADD | 0x20 | Add |
| ISUB | 0x21 | Subtract |
| IMUL | 0x22 | Multiply |
| JMP | 0x30 | Jump unconditional |
| JZ | 0x31 | Jump if zero |
| JNZ | 0x32 | Jump if not zero |
| CMP | 0x40 | Compare |
| PUSH/POP | 0x50/0x51 | Stack operations |
| CALL/RET | 0x60/0x61 | Subroutines |
| SAY | 0x80 | Output message |
| GAUGE | 0x90 | Read sensor/state |
| ALERT | 0x91 | Signal condition |
| EVOLVE | 0xA0 | Adapt program |
| HALT | 0x01 | Stop execution |

## Lock Facts (from experiments)

- **Critical mass: 7+** locks for consistent compilation
- **Compression: 82%** output reduction with locks
- **Cross-model: 80%** portability across model families
- **Temperature: only t=0.0** is fully stable
- **Ordering: matters** (original > shuffled)

## Cross-Plane Communication

| I'm at | To talk to Plane... | I... |
|--------|---------------------|------|
| 4 | 5 (Intent) | Describe in natural language |
| 4 | 3 (IR) | Format as typed JSON with locks |
| 4 | 2 (Bytecode) | Compile with deepseek-chat + 7 locks |
| 4 | 1 (Native) | Delegate to edge agent |
| 2 | 5 | Disassemble + describe in English |
| 2 | 4 | Disassemble + annotate with domain vocab |

## ABSTRACTION.md Template

```yaml
primary_plane: 4
reads_from: [3, 4, 5]
writes_to: [2, 3, 4]
floor: 2
ceiling: 5
compilers:
  - name: deepseek-chat
    from: 4
    to: 2
    locks: 7
reasoning: |
  [Why this agent lives here]
```
