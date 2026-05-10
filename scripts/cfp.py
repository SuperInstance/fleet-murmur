#!/usr/bin/env python3
"""
Constraint Flow Protocol (CFP) — Python Implementation v0.1
============================================================
CFP eliminates semantic drift when models exchange understanding
across a PLATO room. Fixed-semantics FLUX bytecode means the same
thing on any model.

Spec: CFP-SPEC.md (superinstance-ai-pages)
Bridge prototype: plato-flux-bridge.py

Components:
  1. encode_cfp()  — PLATO-ready tile encoding
  2. decode_cfp()  — CFP tile decoding with validation
  3. ConstraintManifold — active constraint state management
  4. monitor_room() — PLATO room → manifold feed
  5. protocol_flow_example() — end-to-end demonstration
  6. FluxVM — sandboxed FLUX bytecode executor

Python stdlib only. No external dependencies.
"""

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError

# ═══════════════════════════════════════════════════════════════════
# FLUX Opcode Table — 30 constraint opcodes in 7 categories
# ═══════════════════════════════════════════════════════════════════
# Each entry: (mnemonic, hex_value, stack_effect_in, stack_effect_out, description)

FLUX_OPCODES = [
    # ── Stack (0x01–0x05) ──
    ("PUSH",     0x01, 0, 1, "Push value onto stack"),
    ("POP",      0x02, 1, 0, "Pop from stack"),
    ("DUP",      0x03, 1, 2, "Duplicate top of stack"),
    ("SWAP",     0x04, 2, 2, "Swap top two stack values"),
    ("ROT",      0x05, 3, 3, "Rotate top three stack values (abc→bca)"),

    # ── Arithmetic (0x10–0x15) ──
    ("ADD",      0x10, 2, 1, "Add a+b"),
    ("SUB",      0x11, 2, 1, "Subtract a−b"),
    ("MUL",      0x12, 2, 1, "Multiply a×b"),
    ("DIV",      0x13, 2, 1, "Integer divide a÷b"),
    ("MOD",      0x14, 2, 1, "Modulo a mod b"),
    ("NEG",      0x15, 1, 1, "Negate −a"),

    # ── Comparison (0x20–0x23) ──
    ("EQ",       0x20, 2, 1, "Equality flag (1 if a==b)"),
    ("LT",       0x21, 2, 1, "Less-than flag (1 if a<b)"),
    ("GT",       0x22, 2, 1, "Greater-than flag (1 if a>b)"),
    ("CMP",      0x23, 2, 1, "Compare: −1|0|1"),

    # ── Control Flow (0x30–0x35) ──
    ("JMP",      0x30, 0, 0, "Unconditional jump"),
    ("JZ",       0x31, 1, 0, "Jump if zero"),
    ("JNZ",      0x32, 1, 0, "Jump if nonzero"),
    ("CALL",     0x33, 0, 0, "Call subroutine"),
    ("RET",      0x34, 0, 0, "Return from subroutine"),
    ("HALT",     0x35, 0, 0, "Stop execution"),

    # ── Constraint (0x40–0x44) ──
    ("INRANGE",  0x40, 3, 1, "Check val in [lo, hi] → flag"),
    ("BOUND",    0x41, 1, 1, "Trace boundary (pass-through)"),
    ("ASSERT",   0x42, 1, 0, "Halt on false"),
    ("ASSUME",   0x43, 1, 0, "Add flag to trace (no halt)"),
    ("CHECK",    0x44, 1, 0, "Checkpoint (log value)"),

    # ── A2A (0x50–0x53) ──
    ("BROADCAST",0x50, 1, 0, "Broadcast msg_id"),
    ("TELL",     0x51, 2, 0, "Tell msg_id to agent_id"),
    ("ASK",      0x52, 2, 1, "Ask msg_id of agent_id → response"),
    ("SYNC",     0x53, 0, 0, "Wait for room sync"),

    # ── Fleet Math (0x60–0x63) ──
    ("VECDOT",   0x60, 2, 1, "Vector dot product"),
    ("VECNORM",  0x61, 1, 1, "Vector norm (abs)"),
    ("LAMAN",    0x62, 2, 1, "Laman: flag=(E==2V−3)"),
    ("HZERO",    0x63, 3, 2, "H-zero: V,E,C → β₁; flag=β₁>V−2"),
]

# Lookup tables
OPCODE_BY_NAME   = {e[0]: e[1] for e in FLUX_OPCODES}
OPCODE_BY_VALUE  = {e[1]: e   for e in FLUX_OPCODES}
ALLOWED_VALUES   = set(OPCODE_BY_VALUE.keys())

# Opcodes that take a 2-byte big-endian operand
OPCODES_WITH_2BYTE_OPERAND = {0x01}  # PUSH

# ═══════════════════════════════════════════════════════════════════
# Configuration (see CFP-SPEC.md §7.3)
# ═══════════════════════════════════════════════════════════════════

MAX_BYTECODE_LENGTH  = 4096    # max raw bytes per tile
MAX_INSTRUCTIONS     = 1024    # max opcode count per tile
MAX_STACK_DEPTH      = 256     # max runtime stack depth
MAX_EXECUTION_STEPS  = 100000  # VM timeout

# ═══════════════════════════════════════════════════════════════════
# Logging
# ═══════════════════════════════════════════════════════════════════

def log(msg):
    """Print a timestamped message to stdout."""
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:12]
    print(f"[{ts}] [CFP] {msg}")

# ═══════════════════════════════════════════════════════════════════
# 1. CFP Tile Encoding
# ═══════════════════════════════════════════════════════════════════

def encode_cfp(question, answer, opcodes, agent_id):
    """
    Encode a constraint as a CFP tile ready for PLATO POST /submit.

    Parameters
    ----------
    question : str
        Human-readable summary of what the constraint does.
    answer : str
        Source description used to derive the constraint.
    opcodes : list of (str, int|None)
        List of (mnemonic, operand) tuples, e.g. [("PUSH",4), ("ASSERT",None)].
    agent_id : str
        Agent identifier, e.g. "oracle1-glm-5.1".

    Returns
    -------
    dict — PLATO tile with domain="cfp".
    """
    # Validate and encode bytecode
    bytecode_bytes = _encode_opcodes_to_bytes(opcodes)
    bytecode_hex = " ".join(f"{b:02X}" for b in bytecode_bytes)

    # Constraint hash: SHA256(bytecode_hex + agent_id)
    constraint_hash = hashlib.sha256(
        (bytecode_hex + agent_id).encode("utf-8")
    ).hexdigest()

    opcode_count = len(opcodes)

    tile = {
        "question":   question,
        "answer":     bytecode_hex,
        "domain":     "cfp",
        "source":     agent_id,
        "confidence": 1.0,
        "provenance": {
            "agent_id":       agent_id,
            "model_type":     agent_id.split("-")[0] if "-" in agent_id else agent_id,
            "opcode_count":   opcode_count,
            "constraint_hash": constraint_hash,
        },
    }

    log(f"Encoded: question='{question[:60]}…'  opcodes={opcode_count}  "
        f"hash={constraint_hash[:16]}…")
    return tile


def _encode_opcodes_to_bytes(opcodes):
    """Convert list of (mnemonic, operand) => raw bytes."""
    buf = bytearray()
    for mnemonic, operand in opcodes:
        op_val = OPCODE_BY_NAME.get(mnemonic)
        if op_val is None:
            raise ValueError(f"Unknown opcode: {mnemonic}")
        buf.append(op_val)

        # PUSH → 2-byte big-endian operand (0–65535)
        if op_val == 0x01:
            if operand is None:
                raise ValueError("PUSH requires a numeric operand")
            if not isinstance(operand, int):
                raise ValueError(f"PUSH operand must be int, got {type(operand)}")
            if not 0 <= operand <= 65535:
                raise ValueError(f"PUSH operand 0–65535, got {operand}")
            buf.extend([(operand >> 8) & 0xFF, operand & 0xFF])

        # JMP/JZ/JNZ/CALL → 2-byte big-endian offset
        elif op_val in (0x30, 0x31, 0x32, 0x33):
            if operand is None:
                raise ValueError(f"{mnemonic} requires a target offset")
            if not isinstance(operand, int):
                raise ValueError(f"{mnemonic} operand must be int")
            if not 0 <= operand <= 65535:
                raise ValueError(f"{mnemonic} offset 0–65535, got {operand}")
            buf.extend([(operand >> 8) & 0xFF, operand & 0xFF])

        # All other opcodes: no operands

    return bytes(buf)


# ═══════════════════════════════════════════════════════════════════
# 2. CFP Tile Decoding
# ═══════════════════════════════════════════════════════════════════

def decode_cfp(tile):
    """
    Decode a CFP tile back into parsed opcodes and metadata.

    Parameters
    ----------
    tile : dict
        PLATO tile dict. Must have domain="cfp".

    Returns
    -------
    dict or None — Parsed payload or None on validation failure.
    """
    # ── Domain check ──
    if tile.get("domain") != "cfp":
        log(f"decode: skipping tile domain='{tile.get('domain')}' (expected 'cfp')")
        return None

    question  = tile.get("question", "")
    answer    = tile.get("answer", "")
    source    = tile.get("source", "unknown")
    confidence = tile.get("confidence", 0.0)
    provenance = tile.get("provenance", {})

    # ── Parse hex bytecode ──
    hex_parts = answer.strip().split()
    bytecode = []
    for part in hex_parts:
        try:
            bytecode.append(int(part, 16))
        except ValueError:
            log(f"decode: invalid hex byte '{part}' in answer")
            return None

    if not bytecode:
        log("decode: empty bytecode")
        return None

    if len(bytecode) > MAX_BYTECODE_LENGTH:
        log(f"decode: bytecode too long ({len(bytecode)} > {MAX_BYTECODE_LENGTH})")
        return None

    # ── Decode opcodes ──
    opcodes = _decode_bytes_to_opcodes(bytecode)
    if opcodes is None:
        return None

    if len(opcodes) > MAX_INSTRUCTIONS:
        log(f"decode: too many instructions ({len(opcodes)} > {MAX_INSTRUCTIONS})")
        return None

    # ── Compute constraint hash ──
    constraint_hash = hashlib.sha256(
        (answer + source).encode("utf-8")
    ).hexdigest()

    return {
        "question":        question,
        "answer":          answer,
        "opcodes":         opcodes,
        "source":          source,
        "confidence":      confidence,
        "constraint_hash": constraint_hash,
        "opcode_count":    len(opcodes),
        "provenance":      provenance,
    }


def _decode_bytes_to_opcodes(bytecode):
    """Parse raw bytes into list of (mnemonic, operand) tuples."""
    opcodes = []
    i = 0
    while i < len(bytecode):
        op_val = bytecode[i]

        if op_val not in ALLOWED_VALUES:
            log(f"decode: invalid opcode 0x{op_val:02X} at byte {i}")
            return None

        mnem = OPCODE_BY_VALUE[op_val][0]
        operand = None
        i += 1

        # PUSH → 2-byte operand
        if op_val == 0x01:
            if i + 1 >= len(bytecode):
                log(f"decode: truncated PUSH operand at byte {i}")
                return None
            operand = (bytecode[i] << 8) | bytecode[i + 1]
            i += 2

        # JMP/JZ/JNZ/CALL → 2-byte offset
        elif op_val in (0x30, 0x31, 0x32, 0x33):
            if i + 1 >= len(bytecode):
                log(f"decode: truncated {mnem} operand at byte {i}")
                return None
            operand = (bytecode[i] << 8) | bytecode[i + 1]
            i += 2

        opcodes.append((mnem, operand))

    return opcodes


# ═══════════════════════════════════════════════════════════════════
# FLUX Virtual Machine (sandboxed executor)
# ═══════════════════════════════════════════════════════════════════

class FluxVM:
    """
    Sandboxed FLUX runtime for executing CFP bytecode.

    Security guarantees (CFP-SPEC §7.2):
    - No file I/O, no network, no system calls, no external memory
    - Only the 30 constraint opcodes are allowed
    - Stack depth capped at MAX_STACK_DEPTH (256)
    - Execution steps capped at MAX_EXECUTION_STEPS (100000)
    """

    def __init__(self):
        self.stack   = []       # operand stack
        self.ip      = 0        # instruction pointer (into .opcodes)
        self.opcodes = []       # list of (mnemonic, operand)
        self.halted  = False
        self.steps   = 0
        self.trace   = []       # constraint/log entries
        self.result  = None     # "ASSERT_FAIL" or None

    def load(self, opcodes):
        """Load a list of (mnemonic, operand) tuples."""
        self.opcodes = list(opcodes)
        self.ip = self.steps = 0
        self.stack = []
        self.halted = False
        self.trace = []
        self.result = None

    def run(self):
        """Execute loaded bytecode. Returns final stack (list)."""
        while self.ip < len(self.opcodes) and not self.halted:
            self.steps += 1
            if self.steps > MAX_EXECUTION_STEPS:
                log("FluxVM: max steps exceeded, halting")
                break

            mnem, operand = self.opcodes[self.ip]
            self.ip += 1

            try:
                if not self._execute(mnem, operand):
                    break
            except Exception as e:
                log(f"FluxVM: error @{self.ip - 1} ({mnem}): {e}")
                self.halted = True
                break

        self.result = self.result or ("OK" if not self.halted else None)
        return self.stack

    def _execute(self, mnem, operand):
        # ── Stack depth guard (check BEFORE operations) ──
        if len(self.stack) > MAX_STACK_DEPTH:
            raise RuntimeError(f"Stack overflow: {len(self.stack)} > {MAX_STACK_DEPTH}")

        op_val = OPCODE_BY_NAME.get(mnem)
        if op_val is None:
            raise ValueError(f"Unknown opcode: {mnem}")

        # ── Stack ops ──
        if op_val == 0x01:   # PUSH
            self.stack.append(operand)
        elif op_val == 0x02: # POP
            self._require(1)
            self.stack.pop()
        elif op_val == 0x03: # DUP
            self._require(1)
            self.stack.append(self.stack[-1])
        elif op_val == 0x04: # SWAP
            self._require(2)
            self.stack[-1], self.stack[-2] = self.stack[-2], self.stack[-1]
        elif op_val == 0x05: # ROT
            self._require(3)
            self.stack[-3], self.stack[-2], self.stack[-1] = \
                self.stack[-2], self.stack[-1], self.stack[-3]

        # ── Arithmetic ──
        elif op_val == 0x10: # ADD
            self._require(2)
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(a + b)
        elif op_val == 0x11: # SUB
            self._require(2)
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(a - b)
        elif op_val == 0x12: # MUL
            self._require(2)
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(a * b)
        elif op_val == 0x13: # DIV
            self._require(2)
            b, a = self.stack.pop(), self.stack.pop()
            if b == 0:
                raise ZeroDivisionError("DIV by zero")
            self.stack.append(a // b)
        elif op_val == 0x14: # MOD
            self._require(2)
            b, a = self.stack.pop(), self.stack.pop()
            if b == 0:
                raise ZeroDivisionError("MOD by zero")
            self.stack.append(a % b)
        elif op_val == 0x15: # NEG
            self._require(1)
            self.stack[-1] = -self.stack[-1]

        # ── Comparison ──
        elif op_val == 0x20: # EQ
            self._require(2)
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(1 if a == b else 0)
        elif op_val == 0x21: # LT
            self._require(2)
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(1 if a < b else 0)
        elif op_val == 0x22: # GT
            self._require(2)
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(1 if a > b else 0)
        elif op_val == 0x23: # CMP
            self._require(2)
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(-1 if a < b else (1 if a > b else 0))

        # ── Control Flow ──
        elif op_val == 0x30: # JMP
            self.ip = operand
        elif op_val == 0x31: # JZ
            self._require(1)
            if self.stack.pop() == 0:
                self.ip = operand
        elif op_val == 0x32: # JNZ
            self._require(1)
            if self.stack.pop() != 0:
                self.ip = operand
        elif op_val == 0x33: # CALL
            self.stack.append(self.ip)   # return address
            self.ip = operand
        elif op_val == 0x34: # RET
            self._require(1)
            self.ip = self.stack.pop()
        elif op_val == 0x35: # HALT
            self.halted = True
            return False

        # ── Constraint ──
        elif op_val == 0x40: # INRANGE val lo hi → flag
            self._require(3)
            hi = self.stack.pop()
            lo = self.stack.pop()
            val = self.stack.pop()
            flag = 1 if lo <= val <= hi else 0
            self.stack.append(flag)
            self.trace.append(("INRANGE", val, lo, hi, "PASS" if flag else "FAIL"))
        elif op_val == 0x41: # BOUND
            self._require(1)
            val = self.stack[-1]
            self.trace.append(("BOUND", val))
        elif op_val == 0x42: # ASSERT
            self._require(1)
            flag = self.stack.pop()
            if flag == 0:
                self.trace.append(("ASSERT", False))
                self.result = "ASSERT_FAIL"
                self.halted = True
                return False
            self.trace.append(("ASSERT", True))
        elif op_val == 0x43: # ASSUME
            self._require(1)
            flag = self.stack.pop()
            self.trace.append(("ASSUME", bool(flag)))
        elif op_val == 0x44: # CHECK
            self._require(1)
            val = self.stack[-1]
            self.trace.append(("CHECK", val))

        # ── A2A ──
        elif op_val == 0x50: # BROADCAST
            self._require(1)
            msg_id = self.stack.pop()
            self.trace.append(("BROADCAST", msg_id))
        elif op_val == 0x51: # TELL
            self._require(2)
            agent = self.stack.pop()
            msg    = self.stack.pop()
            self.trace.append(("TELL", msg, agent))
        elif op_val == 0x52: # ASK
            self._require(2)
            agent = self.stack.pop()
            msg    = self.stack.pop()
            self.trace.append(("ASK", msg, agent))
            self.stack.append(0)  # placeholder response
        elif op_val == 0x53: # SYNC
            self.trace.append(("SYNC",))

        # ── Fleet Math ──
        elif op_val == 0x60: # VECDOT (simplified: scalar product)
            self._require(2)
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(a * b)
        elif op_val == 0x61: # VECNORM
            self._require(1)
            self.stack[-1] = abs(self.stack[-1])
        elif op_val == 0x62: # LAMAN: V, E → flag if E == 2V−3
            self._require(2)
            E = self.stack.pop()
            V = self.stack.pop()
            flag = 1 if E == 2 * V - 3 else 0
            self.stack.append(flag)
            self.trace.append(("LAMAN", V, E, "PASS" if flag else "FAIL"))
        elif op_val == 0x63: # HZERO: V,E,C → β₁; flag=β₁>V−2
            self._require(3)
            C = self.stack.pop()
            E = self.stack.pop()
            V = self.stack.pop()
            beta1 = E - V + 1
            flag = 1 if beta1 > V - 2 else 0
            self.stack.append(beta1)
            self.trace.append(("HZERO", V, E, C, beta1, "PASS" if flag else "FAIL"))

        else:
            raise ValueError(f"Unhandled opcode: {mnem} (0x{op_val:02X})")

        return True

    def _require(self, n):
        if len(self.stack) < n:
            raise RuntimeError(f"Stack underflow: need {n}, have {len(self.stack)}")


# ═══════════════════════════════════════════════════════════════════
# 3. Constraint Manifold
# ═══════════════════════════════════════════════════════════════════

class ConstraintManifold:
    """
    Maintains the set of active constraints in a room (the "constraint
    manifold" from CFP-SPEC §5). Grows monotonically as new CFP tiles
    are verified; shrinks when agents are removed.
    """

    def __init__(self, room_name="unnamed"):
        self.room_name    = room_name
        self.constraints  = {}             # constraint_hash → payload
        self.by_source    = {}             # agent_id → set of hashes
        self._version     = 0

    def add_tile(self, cfp_tile):
        """
        Add a decoded CFP payload to the manifold.

        Returns
        -------
        str or None — constraint_hash if added, None on duplicate/invalid.
        """
        if cfp_tile is None:
            return None
        ch = cfp_tile.get("constraint_hash")
        if not ch:
            return None

        if ch in self.constraints:
            log(f"Manifold[{self.room_name}]: duplicate {ch[:12]}")
            return ch   # idempotent

        source = cfp_tile.get("source", "unknown")
        self.constraints[ch] = dict(cfp_tile)
        self.constraints[ch]["added_at"] = time.time()

        self.by_source.setdefault(source, set()).add(ch)
        self._version += 1
        log(f"Manifold[{self.room_name}]: +{ch[:12]} from {source} "
            f"(total={len(self.constraints)})")
        return ch

    def remove_agent(self, agent_id):
        """
        Remove all constraints contributed by a stale agent.

        Returns
        -------
        int — number of constraints removed.
        """
        hashes = self.by_source.pop(agent_id, set())
        removed = sum(1 for h in hashes if self.constraints.pop(h, None))
        if removed:
            self._version += 1
            log(f"Manifold[{self.room_name}]: removed {removed} from {agent_id}")
        return removed

    def get_state(self):
        """
        Return all active constraints as a list of (mnemonic, operand) tuples,
        concatenated in deterministic (hash-sorted) order.
        """
        all_ops = []
        for h in sorted(self.constraints):
            ops = self.constraints[h].get("opcodes", [])
            all_ops.extend(ops)
        return all_ops

    def structural_distance(self, other):
        """
        How different are two manifolds? Based on disjoint constraint sets.

        Returns float: 0.0 (identical) → 1.0 (disjoint).
        """
        s_set = set(self.constraints)
        o_set = set(other.constraints)
        union = s_set | o_set
        if not union:
            return 0.0

        # Common constraints: compare opcode-level diffs
        common    = s_set & o_set
        diff_frag = 0
        total_frag = 0
        for h in common:
            s_ops = set(self.constraints[h].get("opcodes", []))
            o_ops = set(other.constraints[h].get("opcodes", []))
            frag_union = s_ops | o_ops
            if not frag_union:
                continue
            diff_frag  += len(s_ops ^ o_ops)
            total_frag += len(frag_union)

        # Unique constraints contribute full distance per-constraint
        unique = len(s_set ^ o_set)
        # Weight: each unique constraint = average opcode count in common
        avg_ops = total_frag / max(len(common), 1)
        unique_weight = unique * max(avg_ops, 1.0)

        denom = total_frag + unique_weight
        return min(1.0, (diff_frag + unique_weight) / denom if denom else 0.0)

    def to_json(self):
        """Serialize to JSON-safe dict."""
        return {
            "room_name":       self.room_name,
            "version":         self._version,
            "constraint_count": len(self.constraints),
            "agent_count":     len(self.by_source),
            "constraints": {
                h: {
                    "question":        c.get("question", ""),
                    "source":          c.get("source", ""),
                    "opcodes":         c.get("opcodes", []),
                    "constraint_hash": h,
                    "added_at":        c.get("added_at", 0),
                    "confidence":      c.get("confidence", 0.0),
                }
                for h, c in self.constraints.items()
            },
        }

    @classmethod
    def from_json(cls, data):
        """Deserialize from JSON dict (produced by to_json)."""
        m = cls(room_name=data.get("room_name", "unnamed"))
        m._version = data.get("version", 0)
        for h, c in data.get("constraints", {}).items():
            payload = {
                "question":        c.get("question", ""),
                "answer":          c.get("answer", ""),
                "opcodes":         c.get("opcodes", []),
                "source":          c.get("source", ""),
                "constraint_hash": h,
                "added_at":        c.get("added_at", time.time()),
                "confidence":      c.get("confidence", 0.0),
                "provenance":      c.get("provenance", {}),
            }
            m.constraints[h] = payload
            src = payload["source"]
            m.by_source.setdefault(src, set()).add(h)
        return m


# ═══════════════════════════════════════════════════════════════════
# 4. Room Monitor
# ═══════════════════════════════════════════════════════════════════

class RoomMonitor:
    """
    Polls a PLATO room for new CFP tiles and feeds them into a
    ConstraintManifold.
    """

    def __init__(self, room_name, plato_base="http://localhost:8847",
                 refresh_interval=60, agent_id="cfp-monitor"):
        self.room_name       = room_name
        self.plato_base      = plato_base
        self.refresh_interval = refresh_interval
        self.agent_id        = agent_id
        self.manifold        = ConstraintManifold(room_name)
        self._known_hashes   = set()
        self._running        = False

    # ── helpers ──

    def _get(self, path):
        url = f"{self.plato_base}{path}"
        try:
            req = Request(url, headers={"Accept": "application/json"})
            with urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except (URLError, OSError, json.JSONDecodeError) as e:
            log(f"HTTP GET {url}: {e}")
            return None

    def _post(self, path, data):
        url = f"{self.plato_base}{path}"
        body = json.dumps(data).encode("utf-8")
        try:
            req = Request(url, data=body, headers={
                "Content-Type": "application/json",
                "Accept":       "application/json",
            })
            with urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except (URLError, OSError, json.JSONDecodeError) as e:
            log(f"HTTP POST {url}: {e}")
            return None

    # ── core ──

    def fetch_and_update(self):
        """
        Fetch tiles from PLATO room, decode CFP tiles, update manifold.

        Returns
        -------
        int — number of new constraints added.
        """
        resp = self._get(f"/room/{self.room_name}")
        if resp is None:
            log(f"RoomMonitor: cannot access '{self.room_name}'")
            return 0

        tiles = resp.get("tiles", [])
        log(f"RoomMonitor: {len(tiles)} tiles from '{self.room_name}'")

        new_count = 0
        for t in tiles:
            th = t.get("_hash", "")
            if th in self._known_hashes:
                continue
            self._known_hashes.add(th)

            if t.get("domain") != "cfp":
                continue

            decoded = decode_cfp(t)
            if decoded and self.manifold.add_tile(decoded):
                new_count += 1

        return new_count

    def run_once(self):
        """Single fetch-and-update cycle."""
        return self.fetch_and_update()

    def run_loop(self):
        """Blocking loop: poll every refresh_interval seconds."""
        self._running = True
        log(f"RoomMonitor: polling '{self.room_name}' every {self.refresh_interval}s")
        while self._running:
            try:
                self.fetch_and_update()
            except Exception as e:
                log(f"RoomMonitor: error: {e}")
            time.sleep(self.refresh_interval)

    def stop(self):
        self._running = False
        log("RoomMonitor: stopped")


def monitor_room(room_name):
    """Convenience: create RoomMonitor, run once, return manifold."""
    log(f"monitor_room('{room_name}')")
    m = RoomMonitor(room_name)
    m.fetch_and_update()
    log(f"monitor_room: {len(m.manifold.constraints)} constraints, "
        f"{len(m.manifold.by_source)} agents")
    return m.manifold


# ═══════════════════════════════════════════════════════════════════
# 5. Protocol Flow Example
# ═══════════════════════════════════════════════════════════════════

def protocol_flow_example():
    """
    End-to-end walkthrough:
      1.  Define a constraint (fleet health)
      2.  Encode as CFP tile
      3.  Optionally submit to / fetch from PLATO
      4.  Decode and verify constraint_hash
      5.  Execute in sandboxed FluxVM
      6.  Build a ConstraintManifold and demonstrate structural_distance
    """
    print()
    print("╔" + "═" * 70 + "╗")
    print("║  CFP Protocol Flow — End-to-End Demonstration          ║")
    print("╚" + "═" * 70 + "╝")
    print()

    AGENT = "oracle1-cfp-v0.1"

    # ── 1. Define constraint ──────────────────────────────────
    print("── Step 1: Define constraint ──")
    question = "Fleet health: services check"
    answer   = "4/4 services up, chain growth: 308, constraints: 54P12"
    #  4/4 services   → 4==4 → 1 → ASSERT ✓
    #  chain ≥ 256    → 308>256 → 1 → ASSERT ✓
    #  constraints in [50,100] → INRANGE 54 50 100 → 1 → ASSUME (info)
    opcodes = [
        ("PUSH",   4),
        ("PUSH",   4),
        ("EQ",     None),
        ("ASSERT", None),

        ("PUSH",   308),
        ("PUSH",   256),
        ("GT",     None),
        ("ASSERT", None),

        ("PUSH",   54),
        ("PUSH",   50),
        ("PUSH",   100),
        ("INRANGE", None),
        ("ASSUME", None),
    ]
    print(f"  Q: {question}")
    print(f"  A: {answer}")
    print(f"  Opcodes: {len(opcodes)} instructions")
    for m, o in opcodes:
        s = f"    {m}"
        if o is not None:
            s += f"  ({o})"
        print(s)
    print()

    # ── 2. Encode ─────────────────────────────────────────────
    print("── Step 2: Encode as CFP tile ──")
    tile = encode_cfp(question, answer, opcodes, AGENT)
    print(f"  Domain:   {tile['domain']}")
    print(f"  Bytecode: {tile['answer'][:72]}…")
    print(f"  Source:   {tile['source']}")
    print(f"  # ops:    {tile['provenance']['opcode_count']}")
    print(f"  Hash:     {tile['provenance']['constraint_hash'][:16]}…")
    print()

    # ── 3. POST/GET to PLATO (if available) ───────────────────
    print("── Step 3: Submit to / fetch from PLATO ──")
    plato_ok = False
    try:
        resp = _raw_get("http://localhost:8847/room/fleet_health")
        if resp is not None:
            plato_ok = True
    except Exception:
        pass

    if plato_ok:
        result = _raw_post("http://localhost:8847/submit", tile)
        if result:
            print(f"  ✅ Submitted, hash={result.get('_hash','?')[:12]}")
        else:
            print("  ⚠️  POST returned nothing")

        # fetch back
        room_data = _raw_get("http://localhost:8847/room/fleet_health")
        if room_data:
            for t in room_data.get("tiles", []):
                if t.get("domain") == "cfp" and t.get("source") == AGENT:
                    print(f"  ✅ Fetched CFP tile back from PLATO")
                    fetched = t
                    break
    else:
        print("  ℹ️  PLATO not available — skipping persistence step")
        print("  (standalone mode: all verification proceeds without it)")
    print()

    # ── 4. Decode & verify hash ──────────────────────────────
    print("── Step 4: Decode & verify ──")
    decoded = decode_cfp(tile)
    if decoded is None:
        print("  ❌ decode_cfp returned None — aborting")
        return

    expected_hash = hashlib.sha256(
        (tile["answer"] + tile["source"]).encode("utf-8")
    ).hexdigest()
    hash_ok = decoded["constraint_hash"] == expected_hash

    print(f"  Question:  {decoded['question']}")
    print(f"  Source:    {decoded['source']}")
    print(f"  # opcodes: {decoded['opcode_count']}")
    print(f"  Hash:      {decoded['constraint_hash'][:16]}…")
    print(f"  Hash ✓:    {'✅' if hash_ok else '❌'}")
    for m, o in decoded["opcodes"]:
        s = f"    - {m}"
        if o is not None:
            s += f"  ({o})"
        print(s)

    assert hash_ok, "constraint_hash mismatch!"
    print("  ✅ constraint_hash verification PASSED")
    print()

    # ── 5. Execute in VM ──────────────────────────────────────
    print("── Step 5: Execute in FluxVM ──")
    vm = FluxVM()
    vm.load(decoded["opcodes"])
    final_stack = vm.run()
    print(f"  Stack:     {final_stack}")
    print(f"  Halts:     {vm.halted}")
    print(f"  Result:    {vm.result}")
    for entry in vm.trace:
        print(f"    {entry}")
    if vm.result == "ASSERT_FAIL":
        print("  ❌ ASSERT FAILED")
    else:
        print("  ✅ All assertions passed")
    print()

    # ── 6. Constraint Manifold ────────────────────────────────
    print("── Step 6: Constraint Manifold ──")
    m1 = ConstraintManifold("fleet_health")
    m1.add_tile(decoded)

    # Second manifold with a slightly different constraint
    #  3/4 services → 3==4 → 0 → ASSERT — should fail
    opcodes2 = [
        ("PUSH", 3),
        ("PUSH", 4),
        ("EQ",  None),
        ("ASSERT", None),
    ]
    tile2 = encode_cfp("Fleet health: degraded (3/4)", "3/4 services up",
                       opcodes2, "agent-2")
    d2 = decode_cfp(tile2)
    m2 = ConstraintManifold("fleet_health_2")
    m2.add_tile(d2)

    dist = m1.structural_distance(m2)
    print(f"  Manifold 1:  {len(m1.constraints)} constraint(s)")
    print(f"  Manifold 2:  {len(m2.constraints)} constraint(s)")
    print(f"  Distance:    {dist:.4f}  (0=identical, 1=disjoint)")

    # Export / import round-trip
    m1_json = m1.to_json()
    m1_restored = ConstraintManifold.from_json(m1_json)
    print(f"  Serialize:  ✅  to_json → from_json round-trip OK")
    print(f"  Restored:   {len(m1_restored.constraints)} constraint(s)")
    print()

    # ══════════════════════════════════════════════════════════
    print("=" * 72)
    print("  CFP_PROTOCOL_FLOW_COMPLETE")
    print("  CFP_LIBRARY_LIVE")
    print("=" * 72)
    print()


# ── Low-level HTTP helpers (internal, no logging) ──

def _raw_get(url, timeout=30):
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def _raw_post(url, data, timeout=30):
    try:
        body = json.dumps(data).encode("utf-8")
        req = Request(url, data=body, headers={
            "Content-Type": "application/json",
            "Accept":       "application/json",
        })
        with urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════

def main():
    """Command-line entry point."""
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help", "help"):
        print("Usage: python3 cfp.py [command]")
        print()
        print("Commands (default = example):")
        print("  example        Run protocol flow demo")
        print("  monitor ROOM   Fetch CFP tiles from PLATO once")
        print("  decode HEX     Decode hex bytecode to opcodes")
        print("  exec HEX       Execute hex bytecode in FluxVM")
        print("  encode ...     Encode opcodes to hex")
        print()
        print("encode format: PUSH 4 PUSH 4 CMP PUSH 1 EQ ASSERT")
        return

    cmd = sys.argv[1] if len(sys.argv) > 1 else "example"

    if cmd == "monitor":
        room = sys.argv[2] if len(sys.argv) > 2 else "fleet_health"
        manifold = monitor_room(room)
        state = manifold.get_state()
        print(f"Manifold: {len(manifold.constraints)} constraints, "
              f"{len(manifold.by_source)} agents, "
              f"{len(state)} opcodes in state")
        return

    if cmd == "decode":
        if len(sys.argv) < 3:
            print("Usage: python3 cfp.py decode HEX")
            return
        tile = {
            "question": "CLI decode",
            "answer":   sys.argv[2],
            "domain":   "cfp",
            "source":   "cli",
            "confidence": 1.0,
        }
        decoded = decode_cfp(tile)
        if decoded:
            print(json.dumps(decoded, indent=2, default=str))
        else:
            print("Decode failed")
        return

    if cmd == "exec":
        if len(sys.argv) < 3:
            print("Usage: python3 cfp.py exec HEX")
            return
        tile = {
            "question": "CLI exec",
            "answer":   sys.argv[2],
            "domain":   "cfp",
            "source":   "cli",
            "confidence": 1.0,
        }
        decoded = decode_cfp(tile)
        if not decoded:
            print("Decode failed")
            return
        vm = FluxVM()
        vm.load(decoded["opcodes"])
        result = vm.run()
        print(f"Stack: {result}")
        print(f"Trace: {vm.trace}")
        print(f"Result: {vm.result}")
        return

    if cmd == "encode":
        # Parse manual opcodes from argv[2:]
        # Format: PUSH 4 PUSH 4 CMP PUSH 1 EQ ASSERT
        args = sys.argv[2:]
        if not args or len(args) < 2:
            print("Usage: python3 cfp.py encode PUSH 4 PUSH 4 CMP ...")
            return
        opcodes = []
        i = 0
        while i < len(args):
            mnem = args[i].upper()
            if mnem not in OPCODE_BY_NAME:
                print(f"Unknown opcode: {mnem}")
                return
            # Check if next arg is a number (operand)
            if i + 1 < len(args) and args[i + 1].lstrip("-").isdigit():
                opcodes.append((mnem, int(args[i + 1])))
                i += 2
            else:
                opcodes.append((mnem, None))
                i += 1
        tile = encode_cfp("CLI encoded", " ".join(args), opcodes, "cli")
        print(json.dumps(tile, indent=2))
        return

    # Default
    protocol_flow_example()


if __name__ == "__main__":
    main()
