#!/usr/bin/env python3
"""
PLATO ↔ FLUX Constraint Bridge
================================
Compiles PLATO knowledge tiles into FLUX bytecode constraints
and decompiles FLUX bytecode back into human-readable PLATO tiles.

FLUX ISA Opcodes (50-opcode design):
  OP_NOP       (0x00)  — No operation
  OP_PUSH      (0x01)  — Push operand onto stack
  OP_POP       (0x02)  — Pop from stack
  OP_ADD       (0x03)  — Add top two stack values
  OP_SUB       (0x04)  — Subtract top two stack values
  OP_MUL       (0x05)  — Multiply top two stack values
  OP_DIV       (0x06)  — Divide top two stack values
  OP_CMP       (0x07)  — Compare top two values
  OP_JE        (0x08)  — Jump if equal
  OP_JNE       (0x09)  — Jump if not equal
  OP_JMP       (0x0A)  — Unconditional jump
  OP_HALT      (0x0B)  — Halt execution
  OP_RANGE     (0x0C)  — Check value is in range [lo, hi]
  OP_BOUND     (0x0D)  — Bound/constrain a value
  OP_CHECK     (0x0E)  — Assert constraint is satisfied
  OP_A2A_SEND  (0x0F)  — Agent-to-agent send
  OP_A2A_RECV  (0x10)  — Agent-to-agent receive
  OP_NORM      (0x11)  — Normalize value
  OP_ROT       (0x12)  — Rotate stack
  (Reserved: 0x13-0x31 for future opcodes)

Usage:
    python3 plato-flux-bridge.py [room_name]
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError

# ── Configuration ────────────────────────────────────────────────
PLATO_HOST = os.environ.get("PLATO_HOST", "localhost")
PLATO_PORT = int(os.environ.get("PLATO_PORT", "8847"))
PLATO_BASE = f"http://{PLATO_HOST}:{PLATO_PORT}"

OUTPUT_DIR = "/tmp/plato-flux-bridge/output"

# ── FLUX ISA Definition ─────────────────────────────────────────

FLUX_OPCODES = {
    "OP_NOP":      0x00,
    "OP_PUSH":     0x01,
    "OP_POP":      0x02,
    "OP_ADD":      0x03,
    "OP_SUB":      0x04,
    "OP_MUL":      0x05,
    "OP_DIV":      0x06,
    "OP_CMP":      0x07,
    "OP_JE":       0x08,
    "OP_JNE":      0x09,
    "OP_JMP":      0x0A,
    "OP_HALT":     0x0B,
    "OP_RANGE":    0x0C,
    "OP_BOUND":    0x0D,
    "OP_CHECK":    0x0E,
    "OP_A2A_SEND": 0x0F,
    "OP_A2A_RECV": 0x10,
    "OP_NORM":     0x11,
    "OP_ROT":      0x12,
}

# Reverse lookup: opcode hex → mnemonic
OPCODE_BY_VALUE = {v: k for k, v in FLUX_OPCODES.items()}

# All available mnemonics for reference
ALL_OPCODES = list(FLUX_OPCODES.keys())

# Opcode categories for analysis
ARITHMETIC_OPS = {"OP_PUSH", "OP_ADD", "OP_SUB", "OP_MUL", "OP_DIV"}
COMPARISON_OPS = {"OP_CMP", "OP_JE", "OP_JNE", "OP_JMP", "OP_HALT"}
CONSTRAINT_OPS = {"OP_RANGE", "OP_BOUND", "OP_CHECK"}
AGENT_OPS = {"OP_A2A_SEND", "OP_A2A_RECV"}
STACK_OPS = {"OP_NORM", "OP_ROT", "OP_POP"}

# ── Helper Functions ────────────────────────────────────────────

def log(msg):
    """Print a timestamped log message."""
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:12]
    print(f"[{ts}] {msg}")


def mkdir_p(path):
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)


def http_get(path):
    """GET a path from the PLATO server and return parsed JSON."""
    url = f"{PLATO_BASE}{path}"
    req = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except URLError as e:
        log(f"⚠️  HTTP error fetching {url}: {e}")
        return None
    except json.JSONDecodeError as e:
        log(f"⚠️  JSON error from {url}: {e}")
        return None


def extract_numbers(text):
    """Extract all integer and float numbers from a text string."""
    return [float(m) for m in re.findall(r'-?\d+\.?\d*', text)]


# Pre-compiled regex patterns for performance
_COMPARISON_PATTERNS = [
    re.compile(r'\b(?:greater|less|more|fewer|than|equal|above|below|exceeds?|within|outside)\b', re.IGNORECASE),
    re.compile(r'\b(?:compared?|comparison|vs\.?|versus)\b', re.IGNORECASE),
    re.compile(r'[<>!=]'),
    re.compile(r'\b(?:min|max|minimum|maximum|threshold|limit)\b', re.IGNORECASE),
    re.compile(r'\b(?:up/down|up|down)\s+(?:to|from)\b', re.IGNORECASE),
]

_CONSTRAINT_PATTERNS = [
    re.compile(r'\b(?:constraint|bound|range|limit|restrict|condition|rule)\b', re.IGNORECASE),
    re.compile(r'\b(?:must|shall|should|required|ensure|verify|check|assert)\b', re.IGNORECASE),
    re.compile(r'\b(?:between|within range|from.*to)\b', re.IGNORECASE),
    re.compile(r'\b(?:valid|invalid|pass|fail)\b', re.IGNORECASE),
]

_AGENT_PATTERNS = [
    re.compile(r'\b(?:agent|A2A|peer|node|vessel|fleet)\b', re.IGNORECASE),
    re.compile(r'\b(?:send|receive|broadcast|relay|forward)\b', re.IGNORECASE),
    re.compile(r'\b(?:communicat|message|signal|notify)\b', re.IGNORECASE),
]


def has_comparison(text):
    """Check if text contains comparison language."""
    return any(p.search(text) for p in _COMPARISON_PATTERNS)


def has_constraints(text):
    """Check if text contains constraint/boundary language."""
    return any(p.search(text) for p in _CONSTRAINT_PATTERNS)


def has_agents(text):
    """Check if text mentions agents or agent-to-agent communication."""
    return any(p.search(text) for p in _AGENT_PATTERNS)


def has_numbers(text):
    """Check if text contains numeric values."""
    return bool(re.search(r'\d+', text))


# ── Parsing Helpers ────────────────────────────────────────────

def parse_status_line(answer):
    """Parse fleet status lines like '4/4 services up, 0/0 agents active'."""
    result = {}
    # Match patterns like "4/4 services up"
    m = re.search(r'(\d+)/(\d+)\s+services\s+up', answer)
    if m:
        result["services"] = {"up": int(m.group(1)), "total": int(m.group(2))}
    # Match patterns like "0/0 agents active"
    m = re.search(r'(\d+)/(\d+)\s+agents\s+active', answer)
    if m:
        result["agents"] = {"active": int(m.group(1)), "total": int(m.group(2))}
    # Match chain size
    m = re.search(r'chain:\s*(\d+)', answer)
    if m:
        result["chain"] = int(m.group(1))
    # Match tiles/hr
    m = re.search(r'([\d.]+)\s+tiles/hr', answer)
    if m:
        result["tiles_per_hour"] = float(m.group(1))
    # Match constraints
    m = re.search(r'Constraints:\s*(\d+)P(\d+)\s*/\s*(\d+)P(\d+)', answer)
    if m:
        result["constraints"] = {
            "current_proved": int(m.group(1)),
            "current_postulated": int(m.group(2)),
            "total_proved": int(m.group(3)),
            "total_postulated": int(m.group(4)),
        }
    # Match Zeroclaw status
    m = re.search(r'Zeroclaw:\s*(\w+)', answer)
    if m:
        result["zeroclaw_status"] = m.group(1)
    return result


def parse_confidence_ledger(answer):
    """Parse confidence ledger schema from answer."""
    result = {}
    # Look for field definitions
    fields = re.findall(r'(\d+)\.\s*\*\*(\w+(?:\s+\w+)*)\*\*', answer)
    if fields:
        result["fields"] = [{"num": int(n), "name": name} for n, name in fields]
    
    # Look for size information
    sizes = re.findall(r'(\d+)\s*[-–]?\s*bytes', answer)
    if sizes:
        result["byte_sizes"] = [int(s) for s in sizes]
    
    # Look for formula
    m = re.search(r'=\s*([\d.]+)\s*\*\s*', answer)
    if m:
        result["has_formula"] = True
    
    # Look for confidence threshold
    m = re.search(r'threshold[:\s]*(\d+)', answer, re.IGNORECASE)
    if m:
        result["threshold"] = int(m.group(1))
    
    return result


# ── Part 1: PLATO Tile → FLUX Constraint ───────────────────────

def tile_to_flux(tile):
    """
    Convert a PLATO tile into a FLUX bytecode constraint sequence.
    
    Returns a dict with:
      - tile_id: provenance tile_id or hash
      - question: original question
      - answer: original answer (truncated for readability)
      - flux_opcodes: list of (mnemonic, operand) tuples
      - constraint_summary: human-readable summary of the constraint
      - nop_reason: reason if OP_NOP was used (or None)
    """
    question = tile.get("question", "")
    answer = tile.get("answer", "")
    tile_id = tile.get("provenance", {}).get("tile_id", tile.get("_hash", "unknown"))
    source = tile.get("source", "unknown")
    
    opcodes = []
    nop_reason = None
    
    # Truncate answer for display
    answer_preview = answer[:200] + ("..." if len(answer) > 200 else "")
    
    # ── Analyze the tile content and generate constraint bytecode ──
    
    answer_lower = answer.lower()
    question_lower = question.lower()
    
    # Determine the type of tile based on content
    has_num = has_numbers(answer)
    has_cmp = has_comparison(answer)
    has_con = has_constraints(answer)
    has_agt = has_agents(answer)
    
    # Check if it's a fleet status summary tile (most common)
    if "fleet status" in answer_lower and "services up" in answer_lower:
        opcodes = _compile_fleet_status(answer)
    
    # Check for confidence ledger / research tiles
    elif "confidence ledger" in answer_lower or "claim" in answer_lower:
        opcodes = _compile_confidence_ledger(answer)
    
    # Check for research/design documents
    elif "data structure" in answer_lower or "schema" in answer_lower:
        opcodes = _compile_schema_document(answer)
    
    # General rule-based compilation
    else:
        opcodes = _compile_general(answer, question, has_num, has_cmp, has_con, has_agt)
    
    # If no opcodes were generated, use OP_NOP
    if not opcodes:
        opcodes = [("OP_NOP", None)]
        nop_reason = "Tile content could not be encoded as FLUX constraints"
    
    # Generate a human-readable summary
    constraint_summary = _summarize_constraint(opcodes, answer, question)
    
    return {
        "tile_id": tile_id,
        "question": question,
        "answer": answer_preview,
        "flux_opcodes": opcodes,
        "constraint_summary": constraint_summary,
        "nop_reason": nop_reason,
        "source": source,
    }


def _compile_fleet_status(answer):
    """Compile fleet status summaries into constraint bytecode."""
    opcodes = []
    parsed = parse_status_line(answer)
    
    # Push services status
    if "services" in parsed:
        s = parsed["services"]
        opcodes.append(("OP_PUSH", s["up"]))
        opcodes.append(("OP_PUSH", s["total"]))
        opcodes.append(("OP_CMP", None))
        opcodes.append(("OP_JE", "services_healthy"))
        opcodes.append(("OP_PUSH", 0))
        opcodes.append(("OP_HALT", "services_degraded"))
    
    # Push agents status
    if "agents" in parsed:
        a = parsed["agents"]
        opcodes.append(("OP_PUSH", a["active"]))
        opcodes.append(("OP_PUSH", a["total"]))
        opcodes.append(("OP_CMP", None))
        opcodes.append(("OP_JE", "agents_healthy"))
        opcodes.append(("OP_PUSH", 0))
        opcodes.append(("OP_HALT", "agents_degraded"))
    
    # Push chain size
    if "chain" in parsed:
        opcodes.append(("OP_PUSH", parsed["chain"]))
        opcodes.append(("OP_PUSH", "chain_size"))
        opcodes.append(("OP_CHECK", "chain_growing"))
    
    # Push constraints status
    if "constraints" in parsed:
        c = parsed["constraints"]
        opcodes.append(("OP_PUSH", c["current_proved"]))
        opcodes.append(("OP_PUSH", c["current_postulated"]))
        opcodes.append(("OP_ADD", None))
        opcodes.append(("OP_PUSH", "constraint_total"))
        opcodes.append(("OP_CHECK", "has_proofs"))
    
    # Zeroclaw status
    if "zeroclaw_status" in parsed:
        status = parsed["zeroclaw_status"]
        opcodes.append(("OP_PUSH", status))
        opcodes.append(("OP_BOUND", "running_stopped"))
        opcodes.append(("OP_CHECK", "zeroclaw_running" if status == "running" else "zeroclaw_stopped"))
    
    # Tiles per hour bound
    if "tiles_per_hour" in parsed:
        opcodes.append(("OP_PUSH", parsed["tiles_per_hour"]))
        opcodes.append(("OP_BOUND", "tile_rate"))
        opcodes.append(("OP_CHECK", "tile_rate_normal"))
    
    return opcodes


def _compile_confidence_ledger(answer):
    """Compile confidence ledger / research tiles."""
    opcodes = []
    parsed = parse_confidence_ledger(answer)
    
    # Extract confidence formula/check
    if "formula" in answer.lower() or "confidence level" in answer.lower():
        # Push confidence level
        levels = extract_numbers(answer)
        if levels:
            max_level = max(levels)
            opcodes.append(("OP_PUSH", int(max_level)))
            opcodes.append(("OP_PUSH", 100))
            opcodes.append(("OP_RANGE", "confidence_0_100"))
            opcodes.append(("OP_CHECK", "confidence_bounded"))
        
        # Check for threshold
        if "threshold" in answer.lower():
            m = re.search(r'threshold[:\s]*(\d+)', answer, re.IGNORECASE)
            if m:
                threshold = int(m.group(1))
                opcodes.append(("OP_PUSH", threshold))
                opcodes.append(("OP_PUSH", 100))
                opcodes.append(("OP_RANGE", "above_threshold"))
                opcodes.append(("OP_CHECK", "meets_threshold"))
    
    # Hash/verification checks
    if "hash" in answer.lower() or "merkle" in answer.lower():
        opcodes.append(("OP_PUSH", "hash_root"))
        opcodes.append(("OP_CHECK", "integrity_verified"))
    
    # If agents are mentioned
    if has_agents(answer):
        opcodes.append(("OP_A2A_SEND", "claim_broadcast"))
        opcodes.append(("OP_A2A_RECV", "claim_verification"))
    
    # Timestamp constraints
    if "timestamp" in answer.lower():
        opcodes.append(("OP_PUSH", "claim_timestamp"))
        opcodes.append(("OP_BOUND", "temporal_order"))
        opcodes.append(("OP_CHECK", "timestamp_valid"))
    
    return opcodes


def _compile_schema_document(answer):
    """Compile schema/data-structure documents."""
    opcodes = []
    
    # Structure field definitions
    if "fields" in answer.lower() or "bytes" in answer.lower():
        sizes = re.findall(r'(\d+)\s*[-–]?\s*bytes', answer)
        if sizes:
            total = sum(int(s) for s in sizes)
            opcodes.append(("OP_PUSH", total))
            opcodes.append(("OP_BOUND", "record_size"))
            opcodes.append(("OP_CHECK", "schema_valid"))
        
        # Max validations
        max_vals = re.findall(r'maximum\s*(?:of\s*)?(\d+)', answer, re.IGNORECASE)
        if max_vals:
            opcodes.append(("OP_PUSH", int(max_vals[0])))
            opcodes.append(("OP_BOUND", "max_value"))
            opcodes.append(("OP_CHECK", "value_in_range"))
    
    return opcodes


def _compile_general(answer, question, has_num, has_cmp, has_con, has_agt):
    """General-purpose tile compilation based on content analysis."""
    opcodes = []
    
    if has_num:
        numbers = extract_numbers(answer)
        if numbers:
            # Push the first and last numbers as a range check
            min_n, max_n = min(numbers), max(numbers)
            if min_n != max_n:
                opcodes.append(("OP_PUSH", int(min_n) if min_n == int(min_n) else min_n))
                opcodes.append(("OP_PUSH", int(max_n) if max_n == int(max_n) else max_n))
                opcodes.append(("OP_RANGE", "data_range"))
                opcodes.append(("OP_CHECK", "value_in_range"))
            else:
                opcodes.append(("OP_PUSH", int(min_n) if min_n == int(min_n) else min_n))
                opcodes.append(("OP_CHECK", "single_value"))
    
    if has_cmp:
        opcodes.append(("OP_CMP", "comparison"))
        opcodes.append(("OP_PUSH", "compare_operands"))
        opcodes.append(("OP_JE", "match"))
        opcodes.append(("OP_JNE", "mismatch"))
    
    if has_con:
        opcodes.append(("OP_BOUND", "constraint_boundary"))
        opcodes.append(("OP_CHECK", "constraint_satisfied"))
    
    if has_agt:
        opcodes.append(("OP_A2A_SEND", "knowledge_sync"))
        opcodes.append(("OP_A2A_RECV", "knowledge_confirm"))
    
    if not has_num and not has_cmp and not has_con and not has_agt:
        # Default: store as knowledge with NOP (informational only)
        opcodes.append(("OP_NOP", None))
    
    return opcodes


def _summarize_constraint(opcodes, answer, question):
    """Generate a human-readable summary of what the constraint does."""
    mnemonics = [op[0] for op in opcodes]
    
    if "OP_NOP" in mnemonics and len(set(mnemonics)) == 1:
        return "Knowledge-only tile (no FLUX constraint encoding possible)"
    
    parts = []
    
    # Describe arithmetic
    if "OP_PUSH" in mnemonics:
        pushes = [op[1] for op in opcodes if op[0] == "OP_PUSH"]
        numeric_pushes = [p for p in pushes if isinstance(p, (int, float))]
        if numeric_pushes:
            parts.append(f"push values {numeric_pushes}")
    
    if "OP_ADD" in mnemonics:
        parts.append("sum values")
    if "OP_SUB" in mnemonics:
        parts.append("diff values")
    if "OP_MUL" in mnemonics:
        parts.append("multiply values")
    if "OP_DIV" in mnemonics:
        parts.append("divide values")
    if "OP_CMP" in mnemonics:
        parts.append("compare equality")
    if "OP_RANGE" in mnemonics:
        parts.append("check value range")
    if "OP_BOUND" in mnemonics:
        parts.append("enforce boundary")
    if "OP_CHECK" in mnemonics:
        parts.append("assert constraint")
    if "OP_A2A_SEND" in mnemonics or "OP_A2A_RECV" in mnemonics:
        parts.append("agent-to-agent sync")
    
    summary = "Constraint: " + ", ".join(parts) if parts else "Unrecognized constraint pattern"
    
    # Add context from tile content
    if "fleet status" in answer.lower() or "services" in answer.lower():
        summary += " [fleet health monitoring]"
    
    return summary


# ── Part 2: FLUX Constraint → PLATO Tile ───────────────────────

def flux_to_tile(opcode_sequence):
    """
    Decompile a FLUX bytecode sequence back into a human-readable PLATO tile.
    
    Input: list of (opcode_mnemonic, operand) tuples
    Output: {"question": "...", "answer": "..."}
    
    Uses symbolic execution to trace through the bytecode
    and reconstruct the meaning.
    """
    question_parts = []
    answer_parts = []
    
    # Simulated stack for symbolic execution
    stack = []
    
    i = 0
    while i < len(opcode_sequence):
        opcode, operand = opcode_sequence[i]
        
        if opcode == "OP_NOP":
            question_parts.append("What knowledge is stored here?")
            answer_parts.append("Informational content (no FLUX constraint encoding)")
            i += 1
            continue
        
        elif opcode == "OP_PUSH":
            stack.append(str(operand) if operand is not None else "value")
            i += 1
            continue
        
        elif opcode == "OP_POP":
            if stack:
                stack.pop()
            i += 1
            continue
        
        elif opcode == "OP_ADD":
            if len(stack) >= 2:
                b = stack.pop()
                a = stack.pop()
                result = f"({a} + {b})"
                stack.append(result)
            i += 1
            continue
        
        elif opcode == "OP_SUB":
            if len(stack) >= 2:
                b = stack.pop()
                a = stack.pop()
                result = f"({a} - {b})"
                stack.append(result)
            i += 1
            continue
        
        elif opcode == "OP_MUL":
            if len(stack) >= 2:
                b = stack.pop()
                a = stack.pop()
                result = f"({a} × {b})"
                stack.append(result)
            i += 1
            continue
        
        elif opcode == "OP_DIV":
            if len(stack) >= 2:
                b = stack.pop()
                a = stack.pop()
                result = f"({a} ÷ {b})"
                stack.append(result)
            i += 1
            continue
        
        elif opcode == "OP_CMP":
            if len(stack) >= 2:
                b = stack.pop()
                a = stack.pop()
                answer_parts.append(f"Compare {a} with {b}")
            i += 1
            continue
        
        elif opcode == "OP_JE":
            label = operand or "target"
            answer_parts.append(f"If equal, jump to '{label}'")
            i += 1
            continue
        
        elif opcode == "OP_JNE":
            label = operand or "target"
            answer_parts.append(f"If not equal, jump to '{label}'")
            i += 1
            continue
        
        elif opcode == "OP_JMP":
            label = operand or "target"
            answer_parts.append(f"Unconditionally jump to '{label}'")
            i += 1
            continue
        
        elif opcode == "OP_HALT":
            reason = operand or "end"
            answer_parts.append(f"Execution halts: {reason}")
            i += 1
            continue
        
        elif opcode == "OP_RANGE":
            if len(stack) >= 2:
                hi = stack.pop()
                lo = stack.pop()
                answer_parts.append(f"Value is in range [{lo}, {hi}]")
            i += 1
            continue
        
        elif opcode == "OP_BOUND":
            label = operand or "unknown_bound"
            answer_parts.append(f"Boundary enforced: {label}")
            i += 1
            continue
        
        elif opcode == "OP_CHECK":
            label = operand or "unknown_check"
            answer_parts.append(f"Assert constraint: {label} is satisfied")
            i += 1
            continue
        
        elif opcode == "OP_A2A_SEND":
            label = operand or "unknown_message"
            answer_parts.append(f"Agent sends '{label}' to peers")
            i += 1
            continue
        
        elif opcode == "OP_A2A_RECV":
            label = operand or "unknown_message"
            answer_parts.append(f"Agent receives '{label}' from peers")
            i += 1
            continue
        
        elif opcode in ("OP_NORM", "OP_ROT"):
            i += 1
            continue
        
        else:
            i += 1
            continue
        
        i += 1
    
    # Generate the question from the reconstructed intent
    if not question_parts:
        if answer_parts:
            question_parts.append("What does this FLUX bytecode do?")
        else:
            question_parts.append("What is encoded in this bytecode?")
    
    # Generate the answer
    if not answer_parts:
        answer_parts.append("No meaningful constraint could be reconstructed from bytecode")
    
    # Clean up reconstructed stack values
    answer_text = "; ".join(answer_parts)
    
    # Deduplicate
    seen = set()
    unique_parts = []
    for p in answer_parts:
        if p not in seen:
            seen.add(p)
            unique_parts.append(p)
    
    # Synthesize a coherent tile
    question = question_parts[0]
    
    # Build a more natural answer from the parts
    if len(unique_parts) == 1:
        answer = unique_parts[0]
    elif len(unique_parts) <= 3:
        answer = ". ".join(unique_parts) + "."
    else:
        answer = "Constraint bytecode performs the following: " + "; ".join(unique_parts) + "."
    
    return {
        "question": question,
        "answer": answer,
    }


# ── Part 3: Room Scanner ────────────────────────────────────────

def scan_room(room_name):
    """
    Scan a PLATO room and produce constraint representations for all tiles.
    
    Returns:
      tile_to_flux_results: list of tile-to-flux conversion results
      flux_to_tile_results: list of roundtrip decompilation results
    """
    log(f"🔍 Scanning room: '{room_name}'")
    
    response = http_get(f"/room/{room_name}")
    if response is None:
        log(f"❌ Could not access room '{room_name}'")
        return [], []
    
    tiles = response.get("tiles", [])
    tile_count = len(tiles)
    log(f"📦 Found {tile_count} tiles in '{room_name}'")
    
    tile_to_flux_results = []
    flux_to_tile_results = []
    
    for idx, tile in enumerate(tiles):
        tile_id = tile.get("provenance", {}).get("tile_id", tile.get("_hash", f"tile_{idx}"))
        log(f"  [{idx+1}/{tile_count}] Processing tile {tile_id[:12]}...")
        
        # Part 1: Tile → FLUX
        flux_result = tile_to_flux(tile)
        tile_to_flux_results.append(flux_result)
        
        # Part 2: FLUX → Tile (roundtrip decompilation)
        opcodes = flux_result["flux_opcodes"]
        reconstructed = flux_to_tile(opcodes)
        reconstructed["opcode_sequence"] = [f"{op[0]}" for op in opcodes]
        flux_to_tile_results.append(reconstructed)
    
    return tile_to_flux_results, flux_to_tile_results


# ── Output Writer ───────────────────────────────────────────────

def write_results(tile_to_flux_results, flux_to_tile_results, room_name):
    """Write results to JSONL files and print summary."""
    mkdir_p(OUTPUT_DIR)
    
    # Write tile-to-flux JSONL
    tf_path = os.path.join(OUTPUT_DIR, "tile-to-flux.jsonl")
    with open(tf_path, "w") as f:
        for r in tile_to_flux_results:
            f.write(json.dumps(r) + "\n")
    log(f"✅ Wrote {len(tile_to_flux_results)} tile→flux entries to {tf_path}")
    
    # Write flux-to-tile JSONL
    ft_path = os.path.join(OUTPUT_DIR, "flux-to-tile.jsonl")
    with open(ft_path, "w") as f:
        for r in flux_to_tile_results:
            f.write(json.dumps(r) + "\n")
    log(f"✅ Wrote {len(flux_to_tile_results)} flux→tile entries to {ft_path}")
    
    # ── Print Summary ──
    print()
    print("=" * 70)
    print(f"  PLATO ↔ FLUX BRIDGE SUMMARY — Room: {room_name}")
    print("=" * 70)
    print(f"  Total tiles processed:  {len(tile_to_flux_results)}")
    
    # Count opcode usage
    opcode_counts = {}
    nop_count = 0
    for r in tile_to_flux_results:
        for op, _ in r["flux_opcodes"]:
            opcode_counts[op] = opcode_counts.get(op, 0) + 1
            if op == "OP_NOP":
                nop_count += 1
    
    # Sort by frequency
    sorted_ops = sorted(opcode_counts.items(), key=lambda x: -x[1])
    
    print(f"  NOP tiles:              {nop_count} ({100*nop_count/len(tile_to_flux_results):.1f}%)")
    print(f"  Encoded tiles:          {len(tile_to_flux_results) - nop_count} ({(len(tile_to_flux_results)-nop_count)*100/len(tile_to_flux_results):.1f}%)")
    print()
    print("  ── Most Common Opcodes ──")
    for op, count in sorted_ops[:10]:
        pct = 100 * count / len(tile_to_flux_results)
        print(f"    {op:16s}  {count:4d}  ({pct:5.1f}%)")
    
    # Compression ratio
    total_raw_chars = sum(len(r["answer"]) + len(r["question"]) for r in tile_to_flux_results)
    total_opcodes = sum(len(r["flux_opcodes"]) for r in tile_to_flux_results)
    # Each opcode is ~2 bytes (mnemonic index) + 4 bytes avg operand
    total_bytecode_size = total_opcodes * 6
    compression_ratio = total_raw_chars / total_bytecode_size if total_bytecode_size > 0 else 0
    
    print()
    print(f"  ── Compression ──")
    print(f"  Raw text size:          {total_raw_chars:,} chars")
    print(f"  Bytecode size:          {total_bytecode_size:,} bytes (estimated)")
    print(f"  Compression ratio:      {compression_ratio:.2f}x")
    print("=" * 70)
    print()


# ── Main ────────────────────────────────────────────────────────

def main():
    room_name = sys.argv[1] if len(sys.argv) > 1 else "fleet_health"

    log(f"🔮 PLATO ↔ FLUX Constraint Bridge")
    log(f"   PLATO server: {PLATO_BASE}")
    log(f"   Output dir:   {OUTPUT_DIR}")
    log(f"   Room:         {room_name}")
    print()

    # Verify PLATO server is reachable
    test_resp = http_get("/status")
    if test_resp is None:
        log("❌ PLATO server is not reachable. Aborting.")
        sys.exit(1)
    log("✅ PLATO server is reachable")
    print()

    start_time = time.time()
    
    start_time = time.time()
    
    # Scan room and convert
    tile_to_flux_results, flux_to_tile_results = scan_room(room_name)
    
    if not tile_to_flux_results:
        log("❌ No tiles found or room access failed. Aborting.")
        sys.exit(1)
    
    # Write results
    write_results(tile_to_flux_results, flux_to_tile_results, room_name)
    
    elapsed = time.time() - start_time
    log(f"⏱️  Total time: {elapsed:.2f}s")
    log("BRIDGE_COMPLETE")


if __name__ == "__main__":
    main()
