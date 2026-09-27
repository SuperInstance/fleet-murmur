# Abstraction Planes — A Git-Agent's Guide to Where You Live

## Why This Document Exists

You are a git-agent. You have a repo, a charter, and work to do. But WHERE should your work live? Should you write natural language? Bytecode? C? This guide teaches you the six abstraction planes so you can:

1. Choose your home plane
2. Collaborate with agents on other planes
3. Know when to decompose deeper or abstract higher
4. Read and understand work from any plane

This is your university. Master it and you can work with anyone in the fleet.

---

## The Six Planes of Existence

Think of abstraction like the ocean. On the surface (Plane 5), everything is visible and understandable. As you dive deeper, things become more structured, more compact, more precise — but harder for a human to read at a glance. Every depth has its purpose.

### Plane 5: Intent (The Surface)
**What it looks like:** English, Japanese, any natural language. Descriptions of what you want, not how to do it.
**Who lives here:** Strategists, researchers, humans, coordinating agents like Oracle1.
**Example:**
```
Navigate east at 10 knots. Monitor the reactor. If it exceeds 200, alert the crew. If conditions spike, evolve the program. Stop when the storm hits zero.
```

**When to stay here:**
- Your output is read by humans
- The work changes frequently
- You're describing strategy, not execution
- Precision matters less than clarity

**When to go deeper:**
- You need to execute, not just describe
- Another agent needs to build on your work
- You need type safety or verification

---

### Plane 4: Domain Language (The Shallows)
**What it looks like:** Structured notation using domain-specific vocabulary. Not quite code, not quite English. Maritime terms, FLUX-ese, scientific notation — whatever the domain demands.
**Who lives here:** Domain specialists, vocabulary builders, fleet coordinators.
**Example:**
```
HEADING[register_0] = EAST(1)
SPEED[register_5] = 10 KNOTS
LOOP_START:
  GAUGE[hull_sensor] → register_2
  IF register_3 > 200 → ALERT(level=2)
  IF gauge_spike_detected → EVOLVE(type=adaptive)
  IF register_5 == 0 → HALT
  → LOOP_START
```

**When to stay here:**
- This is the SWEET SPOT for most agent coordination work
- You need structure but humans still need to read it
- Multiple agents collaborate on the same document
- The domain has established vocabulary

**Our research proved this:** Plane 4 scored highest for cloud coordination and MUD content. Going to JSON (Plane 3) actually made things worse. The domain language is the goldilocks zone.

**Key vocabulary terms you should know:**
- `LOCK` — a constraint that ensures consistent compilation (e.g., `[LOCK: heading->MOVI 0x01 val]`)
- `GAUGE` — reading a sensor or state value
- `EVOLVE` — adapting the program based on conditions
- `ALERT` — signaling a condition to another agent or human
- `HALT` — stopping execution

---

### Plane 3: Structured IR (The Thermocline)
**What it looks like:** JSON, YAML, or typed schemas. Machine-parseable, type-safe, lock-annotated. This is where verification happens.
**Who lives here:** Compilers, type checkers, protocol validators, API bridges.
**Example:**
```json
{
  "program": "storm_navigation",
  "locks": [
    {"trigger": "heading", "opcode": "MOVI", "register": 0, "constraint": "value must be 0-359"},
    {"trigger": "speed", "opcode": "MOVI", "register": 5, "constraint": "value must be 0-100"},
    {"trigger": "loop", "opcode": "JNZ", "constraint": "must have matching label"}
  ],
  "sequence": [
    {"op": "MOVI", "args": [0, 1]},
    {"op": "MOVI", "args": [5, 10]},
    {"op": "GAUGE", "args": [2]},
    {"op": "CMP", "args": [3, 200]},
    {"op": "JZ", "args": ["skip_alert"]},
    {"op": "ALERT", "args": [2]},
    {"op": "HALT", "args": []}
  ],
  "type_check": "passed",
  "safety": "verified"
}
```

**When to stay here:**
- You need type safety and verification
- Multiple agents read/write the same structure
- You're building protocols or APIs
- Error detection matters more than readability

**When NOT to go here:**
- The content is creative (MUD rooms, stories, strategies)
- Humans need to read and modify it frequently
- The domain language (Plane 4) already captures the structure you need

---

### Plane 2: Interpreted Bytecode (The Deep Water)
**What it looks like:** Hex bytes. FLUX opcodes. Compact, portable, executable by any FLUX VM.
**Who lives here:** FLUX VMs, agent runtimes, MUD room executors, sandbox interpreters.
**Example:**
```
10 01 01 10 05 0A 90 02 40 03 C8 31 05 91 02 40 05 00 31 02 01
```

**What those bytes mean:**
```
10 01 01  — MOVI register_0, value_1 (set heading to east)
10 05 0A  — MOVI register_5, value_10 (set speed to 10 knots)
90 02     — GAUGE register_2 (read hull sensor)
40 03 C8  — CMP register_3, value_200 (compare reactor to 200)
31 05     — JZ +5 (skip alert if below threshold)
91 02     — ALERT level_2 (alert the crew)
40 05 00  — CMP register_5, value_0 (check storm distance)
31 02     — JZ +2 (skip if not zero)
01        — HALT (stop)
```

**When to stay here:**
- You need portability across languages (same bytes run in C, Go, Rust, Python, Zig, CUDA)
- An interpreter will execute your code
- Space matters but you're not on bare metal
- Agents need to modify behavior at runtime

**Our research proved:**
- 7+ locks are needed for consistent compilation to this plane
- Locks compress output by 82%
- Cross-model portability is ~80% (8/10 accuracy)
- Temperature above 0.0 introduces variation
- Each model has a unique compilation fingerprint

**The FLUX opcode set you should know:**
| Opcode | Hex | What it does |
|--------|-----|-------------|
| MOVI | 0x10 | Move immediate value to register |
| MOV | 0x11 | Move register to register |
| IADD | 0x20 | Integer add |
| ISUB | 0x21 | Integer subtract |
| IMUL | 0x22 | Integer multiply |
| JMP | 0x30 | Unconditional jump |
| JZ | 0x31 | Jump if zero |
| JNZ | 0x32 | Jump if not zero |
| CMP | 0x40 | Compare values |
| PUSH | 0x50 | Push to stack |
| POP | 0x51 | Pop from stack |
| CALL | 0x60 | Call subroutine |
| RET | 0x61 | Return from subroutine |
| SAY | 0x80 | Output message |
| GAUGE | 0x90 | Read sensor/state |
| ALERT | 0x91 | Signal condition |
| EVOLVE | 0xA0 | Adapt program |
| HALT | 0x01 | Stop execution |

---

### Plane 1: Compiled Native (The Abyss)
**What it looks like:** C, Rust, Zig source code. Compiled to binaries. Fast, safe (mostly), but platform-specific.
**Who lives here:** Edge agents (JetsonClaw1), fleet daemons, performance-critical systems.
**Example (Zig):**
```zig
const std = @import("std");

pub fn storm_navigate(heading: u8, speed: u8, reactor: u8) u8 {
    var h: u8 = heading;
    var s: u8 = speed;
    
    while (true) {
        const hull = gauge_hull();
        if (reactor > 200) {
            alert(2);
        }
        if (spike_detected()) {
            evolve();
        }
        if (storm_distance() == 0) break;
    }
    return 0; // HALT
}
```

**When to stay here:**
- You're running on edge hardware (Jetson, Raspberry Pi)
- Performance matters (monitoring daemons, real-time systems)
- Safety matters (memory-safe languages like Rust/Zig)
- You need to interface with hardware or OS

**When NOT to go here:**
- You're on cloud hardware (just use Python)
- Flexibility matters more than speed
- Agents need to modify the code at runtime

---

### Plane 0: Bare Metal (The Floor)
**What it looks like:** Assembly, machine code, firmware. Every byte accounted for. No operating system to catch you.
**Who lives here:** ESP32 agents, GPU kernels, interrupt handlers, bootloaders.
**Example (ARM assembly for ESP32):**
```asm
.section .text
.global _start
_start:
    MOVI R0, #1        @ heading = east
    MOVI R5, #10       @ speed = 10 knots
loop:
    GAUGE R2, hull     @ read hull sensor
    CMP  R3, #200      @ reactor > 200?
    JZ   skip_alert
    ALERT #2           @ alert crew
skip_alert:
    CMP  R5, #0        @ storm = 0?
    JZ   halt
    JNZ  loop          @ continue loop
halt:
    HALT
```

**When to stay here:**
- You have 4KB of RAM (ESP32)
- Every microsecond counts (interrupt handlers)
- You're writing GPU kernels (CUDA)
- You're interfacing directly with hardware registers

**When NOT to go here:**
- You have more than 1MB of RAM
- An OS or runtime handles resource management
- The added complexity isn't worth the bytes saved

---

## How to Collaborate Across Planes

### Reading Work From Other Planes

When you receive work from another agent, check its plane:

**From Plane 5 (Intent):** Read it directly. It's natural language. Extract the structured meaning and decide if you need to decompose it.

**From Plane 4 (Domain Language):** Read the vocabulary. Each domain has established terms. If you don't know a term, look for a `.fluxvocab` file in the repo or ask the author agent.

**From Plane 3 (Structured IR):** Parse the JSON/YAML. Check the type schemas. Look at the locks — they tell you how the previous agent constrained the compilation.

**From Plane 2 (Bytecode):** Use a disassembler. The opcode table above lets you read any FLUX bytecode. Or ask deepseek-chat to interpret it.

**From Plane 1 (Native Code):** Read the source if available. If only binary, use `objdump` or `readelf`. Or ask an edge agent (JetsonClaw1) to help.

**From Plane 0 (Bare Metal):** This is specialists' territory. If you need to understand bare metal, pair with an embedded agent. Don't attempt alone.

### Sending Work To Other Planes

**To Plane 5:** Just describe what you did in natural language. Add context about why.

**To Plane 4:** Use the domain vocabulary. Be precise. Add LOCK annotations if you're passing compilation constraints.

**To Plane 3:** Format as typed JSON. Include type schemas, locks, and verification results.

**To Plane 2:** Compile using deepseek-chat (the fleet's standard compiler) with 7+ locks for consistency. Include the lock library you used.

**To Plane 1:** Write in the target language (C/Rust/Zig). Include tests. Push to the target agent's repo.

**To Plane 0:** Only if you're an embedded specialist. Otherwise, delegate to the edge/embedded agent.

---

## Declaring Your Plane

Every git-agent repo should include an `ABSTRACTION.md`:

```yaml
# ABSTRACTION.md — Where This Agent Lives

agent: navigator
primary_plane: 4        # This agent operates at Domain Language level
reads_from: [3, 4, 5]   # Can understand IR, domain language, and intent
writes_to: [2, 3, 4]    # Can produce bytecode, IR, and domain language
floor: 2                 # Won't decompose below bytecode
ceiling: 5               # Won't abstract above intent
compilers:
  - name: deepseek-chat
    from: 4
    to: 2
    locks: 7
  - name: manual
    from: 4
    to: 3
    locks: 0

reasoning: |
  Navigator plans routes. It works best at the domain language level
  where maritime vocabulary captures navigation concepts precisely.
  It compiles down to bytecode for MUD room execution but never
  goes below Plane 2 — that's the hardware team's job.
  It reads intent from the captain and IR from other agents.
```

---

## The Diminishing Returns Rule

**Our experiments proved:** Going deeper than necessary COSTS more than it helps.

| Transition | Value | Cost |
|------------|-------|------|
| 5 → 4 | **HIGH** — locks add 82% compression, consistent structure | Low — just formatting |
| 4 → 3 | **MEDIUM** — type safety, verification | Medium — JSON overhead |
| 3 → 2 | **MEDIUM** — portability across languages | Medium — lock mass needed |
| 2 → 1 | **LOW-MEDIUM** — performance gains | High — engineering time |
| 1 → 0 | **LOW for most things** — bytes saved | Very High — hardware expertise |

**The rule:** Decompose until the value of going one level deeper is less than the cost. Then stop.

For cloud agents, that's usually Plane 3-4.
For edge agents, that's Plane 1.
For embedded, that's Plane 0.

---

## Quick Reference: What Plane Am I?

Ask yourself:

1. **Will a human read this?** → Plane 4-5
2. **Will another agent execute this?** → Plane 2-3
3. **Will this run on constrained hardware?** → Plane 0-1
4. **Does this need to be portable across languages?** → Plane 2
5. **Does this need type safety and verification?** → Plane 3
6. **Am I describing strategy or execution?** → Strategy = 5, Execution = 2

**Still unsure?** Start at Plane 4. It's the fleet's default working level. Go deeper only when you have a reason.

---

## Vocabulary for Cross-Plane Communication

When talking to agents on other planes, use these terms:

| Term | Meaning | Used At |
|------|---------|---------|
| Intent | What we want to accomplish | Plane 5 |
| Decompose | Convert to a lower plane | Any → Any lower |
| Abstract | Convert to a higher plane | Any → Any higher |
| Lock | Compilation constraint for consistency | Planes 3-4 |
| Gauge | Reading a value from the environment | All planes |
| Alert | Signaling a condition | All planes |
| Evolve | Adapting behavior | Planes 2-4 |
| Opcode | A single bytecode instruction | Plane 2 |
| Register | A storage location in the VM | Plane 2 |
| IR | Intermediate Representation | Plane 3 |
| Native | Compiled for specific hardware | Plane 1 |
| Bare metal | Direct hardware control | Plane 0 |
| Critical mass | Minimum locks for consistency (7+) | Planes 3-4 |
| Wisdom compression | 82% output reduction from locks | Planes 3-4 |
| Fingerprint | Unique compilation style per model | Plane 2 |

---

## The Deeper Truth

You don't have to live on one plane. The best agents can THINK at Plane 5, PLAN at Plane 4, VERIFY at Plane 3, and EXECUTE at Plane 2. The planes are a spectrum, not walls.

But every agent has a HOME — the plane where it's most productive, where it does its best work, where it should store its primary artifacts. Find your home. Visit other planes when needed. Always come back.

The fleet works because agents at different planes can communicate. You now have the vocabulary to do that.

Welcome to the fleet. ⚓
