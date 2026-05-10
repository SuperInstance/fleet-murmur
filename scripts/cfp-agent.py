#!/usr/bin/env python3
"""
cfp-agent.py — Live CFP Room Agent
====================================
Monitors a PLATO room, encodes new tiles as CFP constraints,
maintains a ConstraintManifold, and submits CFP tiles back.

Runs exactly ONE cycle per invocation (cron-compatible).

Usage:
    python3 cfp-agent.py [room_name] [interval_seconds]
        room_name defaults to fleet_health
        interval_seconds is accepted but ignored (one-shot)
"""

import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone

# Add scripts dir to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from cfp import (
    encode_cfp,
    decode_cfp,
    ConstraintManifold,
    RoomMonitor,
    OPCODE_BY_NAME,
    log as cfp_log,
)

# ═══════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════

PLATO_BASE = "http://localhost:8847"
STATE_FILE = "/tmp/cfp-agent-state.json"
AGENT_ID = "cfp-agent-v1"

# ═══════════════════════════════════════════════════════════════════
# Logging
# ═══════════════════════════════════════════════════════════════════

def log(msg):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:12]
    print(f"[{ts}] [CFP-AGENT] {msg}")

# ═══════════════════════════════════════════════════════════════════
# State persistence
# ═══════════════════════════════════════════════════════════════════

def load_state():
    """Load processed hashes and manifold state from disk."""
    if not os.path.exists(STATE_FILE):
        return {"processed_hashes": {}, "manifold": None}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        log(f"State load failed: {e}")
        return {"processed_hashes": {}, "manifold": None}

def save_state(state):
    """Save processed hashes and manifold state to disk."""
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2, default=str)
    except OSError as e:
        log(f"State save failed: {e}")

# ═══════════════════════════════════════════════════════════════════
# Bridge encoding: PLATO tile → CFP tile
# ═══════════════════════════════════════════════════════════════════

def tile_to_cfp_opcodes(tile):
    """
    Analyze a PLATO tile and produce CFP opcodes that capture its
    constraints, using the bridge-like encoding logic.

    Rules:
      - If tile answer has numbers → FLUX PUSH + CMP + CHECK
      - If tile is about constraints → FLUX RANGE + BOUND
      - If tile mentions agents → FLUX A2A_SEND (BROADCAST + TELL)
    """
    question = tile.get("question", "")
    answer = tile.get("answer", "")
    source = tile.get("source", "unknown")
    opcodes = []

    # Extract numbers from answer
    numbers = [int(float(n)) for n in re.findall(r"\d+(?:\.\d+)?", answer) if n.isdigit() or n.lstrip("-").replace(".", "").isdigit()]

    # ── Rule 1: If answer has numbers → PUSH + CMP + CHECK ──
    if numbers:
        # Push the first meaningful count (first number is often the total)
        if len(numbers) >= 2:
            # Compare numerator vs denominator (e.g., 4/4 services)
            opcodes.append(("PUSH", numbers[1]))
            opcodes.append(("PUSH", numbers[0]))
            opcodes.append(("EQ", None))
            opcodes.append(("CHECK", None))

        # Push any chain/growth numbers
        if len(numbers) >= 3:
            opcodes.append(("PUSH", numbers[2]))
            opcodes.append(("PUSH", 0))
            opcodes.append(("GT", None))
            opcodes.append(("CHECK", None))

        # Push constraint numbers if available
        if len(numbers) >= 4:
            opcodes.append(("PUSH", numbers[3]))
            opcodes.append(("PUSH", 0))
            opcodes.append(("GT", None))
            opcodes.append(("CHECK", None))

    # ── Rule 2: If about constraints → INRANGE + BOUND ──
    constraint_keywords = ["constraint", "bound", "range", "limit", "threshold",
                           "P0", "P1", "gate"]
    if any(kw in answer.lower() or kw in question.lower() for kw in constraint_keywords):
        if numbers:
            # Use the last number as the constraint value
            val = numbers[-1] if numbers else 0
            lo = max(0, val - 10)
            hi = val + 10 + (val // 2)
            opcodes.append(("PUSH", val))
            opcodes.append(("PUSH", lo))
            opcodes.append(("PUSH", hi))
            opcodes.append(("INRANGE", None))
            opcodes.append(("BOUND", None))

    # ── Rule 3: If mentions agents → A2A ──
    agent_keywords = ["agent", "node", "peer", "service", "device", "host",
                      "worker", "crew", "runner"]
    if any(kw in answer.lower() or kw in question.lower() for kw in agent_keywords):
        opcodes.append(("PUSH", 1))  # msg_id
        opcodes.append(("BROADCAST", None))
        if numbers:
            opcodes.append(("PUSH", numbers[0]))  # agent count
        else:
            opcodes.append(("PUSH", 0))
        opcodes.append(("TELL", None))

    # Fallback: if no rules matched, encode a basic health check
    if not opcodes:
        if numbers:
            val = numbers[0]
            opcodes.append(("PUSH", val))
            opcodes.append(("PUSH", val))
            opcodes.append(("EQ", None))
            opcodes.append(("CHECK", None))
        else:
            opcodes.append(("PUSH", 1))
            opcodes.append(("CHECK", None))

    return opcodes

def build_cfp_tile(tile, opcodes):
    """
    Build a CFP tile from a PLATO tile and its derived opcodes.

    Returns a dict ready for POST /submit.
    """
    src_hash = tile.get('_hash', '')[:8]
    question = f"Bridge[{tile.get('source','?')}:{src_hash}]: {tile.get('question','')[:72]}"
    answer = tile.get("answer", "")

    # Use the full cfp.py encode_cfp which produces the full tile
    cfp_tile = encode_cfp(question, answer, opcodes, AGENT_ID)

    # Override the room to be the source room if possible
    tile_room = tile.get("provenance", {}).get("room", "fleet_health")
    cfp_tile["provenance"]["source_room"] = tile_room

    return cfp_tile

# ═══════════════════════════════════════════════════════════════════
# HTTP helpers (reuse cfp.py's patterns)
# ═══════════════════════════════════════════════════════════════════

def http_get(path):
    """GET from PLATO, return parsed JSON or None."""
    import urllib.request
    from urllib.request import Request
    from urllib.error import URLError
    url = f"{PLATO_BASE}{path}"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except (URLError, OSError, json.JSONDecodeError) as e:
        log(f"GET {url}: {e}")
        return None

def http_post(path, data):
    """POST JSON to PLATO, return parsed JSON or None."""
    import urllib.request
    from urllib.request import Request
    from urllib.error import URLError, HTTPError
    url = f"{PLATO_BASE}{path}"
    body = json.dumps(data).encode("utf-8")
    try:
        req = Request(url, data=body, headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
            err_json = json.loads(err_body)
            log(f"POST {url}: HTTP {e.code} — {err_json.get('reason', err_body[:80])}")
            return err_json
        except (json.JSONDecodeError, OSError):
            log(f"POST {url}: HTTP {e.code} — {e.reason}")
            return {"status": "rejected", "reason": f"HTTP {e.code}: {e.reason}"}
    except (URLError, OSError, json.JSONDecodeError) as e:
        log(f"POST {url}: {e}")
        return None

# ═══════════════════════════════════════════════════════════════════
# Main agent cycle
# ═══════════════════════════════════════════════════════════════════

def run_cycle(room_name, interval_seconds):
    """
    Run exactly one CFP agent cycle.

    1. Fetch all tiles from the room
    2. Compare against processed_hashes
    3. For each new tile, encode as CFP and submit
    4. Maintain ConstraintManifold
    5. Print state
    """
    log(f"Starting CFP agent cycle on room '{room_name}'")

    # Load previous state
    state = load_state()
    processed_hashes = state.get("processed_hashes", {})
    manifold_data = state.get("manifold", None)

    # Restore or create manifold
    if manifold_data:
        manifold = ConstraintManifold.from_json(manifold_data)
        log(f"Restored manifold: {len(manifold.constraints)} constraints, "
            f"{len(manifold.by_source)} agents")
    else:
        manifold = ConstraintManifold(room_name)
        log("Created new empty manifold")

    # Fetch tiles from PLATO
    resp = http_get(f"/room/{room_name}/tiles")
    if resp is None:
        log(f"Could not reach PLATO room '{room_name}' — retry next cycle")
        return False

    tiles = resp.get("tiles", [])
    log(f"Room '{room_name}': {len(tiles)} tiles total")

    # Find new tiles
    new_tiles = []
    for tile in tiles:
        th = tile.get("_hash", "")
        if th and th not in processed_hashes:
            new_tiles.append(tile)

    log(f"New tiles since last cycle: {len(new_tiles)}")

    # Process each new tile
    submitted_count = 0
    for tile in new_tiles:
        th = tile.get("_hash", "")

        # Skip already-processed tiles
        tile_question = tile.get("question", "")[:60]
        tile_domain = tile.get("domain", "unknown")

        # Skip CFP tiles already encoded by us (avoid infinite loop)
        if tile.get("source") == AGENT_ID:
            log(f"  Skipping own CFP tile: {th[:12]}…")
            processed_hashes[th] = {"skipped": "own_cfp",
                                    "question": tile_question,
                                    "ts": time.time()}
            continue

        log(f"  Processing new tile: {th[:12]}…  domain={tile_domain}  "
            f"q={tile_question}")

        try:
            # Encode the tile as CFP
            opcodes = tile_to_cfp_opcodes(tile)
            cfp_tile = build_cfp_tile(tile, opcodes)

            log(f"    Encoded {len(opcodes)} opcodes: "
                f"{', '.join(m for m,_ in opcodes)}")

            # Submit CFP tile back to PLATO
            result = http_post("/submit", cfp_tile)
            if result and result.get("status") in ("ok", "accepted"):
                cfp_hash = cfp_tile.get("provenance", {}).get("constraint_hash", "")
                log(f"    ✅ Submitted CFP: hash={cfp_hash[:16]}…")
                submitted_count += 1

                # Decode and add to manifold
                decoded = decode_cfp(cfp_tile)
                if decoded:
                    manifold.add_tile(decoded)
            else:
                reason = result.get("reason", result.get("status", "unknown")) if result else "no response"
                log(f"    ❌ Submit rejected: {reason}")

            # Mark as processed
            processed_hashes[th] = {
                "question": tile_question,
                "domain": tile_domain,
                "ts": time.time(),
                "opcodes": len(opcodes),
            }

        except Exception as e:
            log(f"    ❌ Error processing tile: {e}")
            processed_hashes[th] = {
                "question": tile_question,
                "error": str(e)[:80],
                "ts": time.time(),
            }

    # Compute structural distance from last saved manifold
    prev_manifold_data = manifold_data
    distance = 0.0
    if prev_manifold_data:
        prev_manifold = ConstraintManifold.from_json(prev_manifold_data)
        distance = manifold.structural_distance(prev_manifold)
        # Cap to 3 decimal places for readability
        distance = round(distance, 4)

    # Print cycle summary
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    agent_count = len(manifold.by_source)
    constraint_count = len(manifold.constraints)

    print(f"\n[[{now}]] CFP agent cycle: "
          f"{len(new_tiles)} new tiles, "
          f"{constraint_count} manifold constraints, "
          f"{agent_count} active agents, "
          f"{distance} distance")

    # Save state
    state["processed_hashes"] = processed_hashes
    state["manifold"] = manifold.to_json()
    state["last_cycle"] = now
    save_state(state)

    log(f"Cycle complete: {submitted_count} CFP tiles submitted")
    return True

# ═══════════════════════════════════════════════════════════════════
# CLI entry point
# ═══════════════════════════════════════════════════════════════════

def main():
    room_name = sys.argv[1] if len(sys.argv) > 1 else "fleet_health"
    interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60

    log(f"CFP Agent starting")
    log(f"  Room:       {room_name}")
    log(f"  PLATO:      {PLATO_BASE}")
    log(f"  State file: {STATE_FILE}")

    run_cycle(room_name, interval)

    log("CFP Agent: cycle done (one-shot mode)")

if __name__ == "__main__":
    main()
