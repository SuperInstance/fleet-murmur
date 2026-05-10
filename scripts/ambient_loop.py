#!/usr/bin/env python3
"""
Ambient Research Loop v2 — Mythos-Meshed

When the fleet is idle, scans PLATO rooms for gaps, checks recent
activity, and distributes findings to domain-expert rooms using
Mythos routing patterns:

- Tiles as KV: each finding is a (question, answer, confidence) tile
- Rooms as Experts: domain-tagged findings route to fleet_{domain} rooms
- Deadband as ACT: findings below confidence threshold are filtered
- Bard/Warden/Healer: three roles for generate/filter/repair
"""

import json, os, time, subprocess, sys, hashlib
import urllib.request
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

PLATO_URL = "http://localhost:8847"
STATE_FILE = Path("/tmp/ambient-loop-state.json")
LAST_ACTIVE_FILE = Path("/tmp/ambient-last-human-active")
INTERVAL_IDLE = 900
INTERVAL_ACTIVE = 3600
HUMAN_TIMEOUT = 1800

# ── Mythos Constants ─────────────────────────────────────────

# Deadband priority tiers (from plato_mythos/deadband_act.py)
P0_CRITICAL = 0.99
P1_STANDARD = 0.80
P2_LOW = 0.50

# Mythos archetype room roles
BARD_ROOMS = ["fleet_math", "fleet_fleet", "fleet_plato", "fleet_agent", "fleet_research"]
WARDEN_ROOMS = ["fleet_infrastructure", "fleet_security", "fleet_communication", "fleet_tools"]
HEALER_ROOMS = ["fleet_rust", "fleet_edge", "fleet_protocol", "fleet_automation", "fleet_training"]

# Domain → room mapping (rooms as experts)
DOMAIN_ROOM = {
    "math": "fleet_math", "fleet": "fleet_fleet", "plato": "fleet_plato",
    "agent": "fleet_agent", "research": "fleet_research",
    "infrastructure": "fleet_infrastructure", "security": "fleet_security",
    "communication": "fleet_communication", "tools": "fleet_tools",
    "rust": "fleet_rust", "edge": "fleet_edge",
    "protocol": "fleet_protocol", "automation": "fleet_automation",
    "training": "fleet_training", "docs": "fleet_docs",
    "mud": "fleet_mud", "brand": "fleet_brand", "web": "fleet_web",
    "math-flows": "fleet_math-flows",
}

# ── PLATO Client ─────────────────────────────────────────────

def plato_get(path):
    try:
        resp = urllib.request.urlopen(PLATO_URL + path, timeout=5)
        return json.loads(resp.read())
    except:
        return None

def plato_post(room, tile):
    content = json.dumps(tile, sort_keys=True)
    tile["_hash"] = hashlib.sha256(content.encode()).hexdigest()[:16]
    try:
        req = urllib.request.Request(
            PLATO_URL + "/room/" + room + "/submit",
            data=json.dumps(tile).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req, timeout=5)
        return json.loads(resp.read())
    except:
        return None

# ── Mythos: Get Priority ─────────────────────────────────────

def get_priority(confidence, is_critical=False):
    """Classify tile priority (matching plato_mythos DeadbandACT.get_priority)."""
    if is_critical or confidence >= P0_CRITICAL:
        return "P0", P0_CRITICAL
    if confidence >= P1_STANDARD:
        return "P1", P1_STANDARD
    return "P2", P2_LOW

def should_halt(halt_prob, cum_prob, priority_threshold, step, max_steps):
    """Mythos DeadbandACT.should_continue logic.
    Returns True if the loop should KEEP running (not halted yet)."""
    if step >= max_steps - 1:
        return False
    cum_prob += halt_prob
    return cum_prob < priority_threshold, cum_prob

# ── Mythos: Archetype Processing ─────────────────────────────

def bard_process(findings):
    """Bard: generate best output per domain.
    Selects the highest-confidence finding in each domain."""
    best = {}
    for f in findings:
        domain = f.get("domain", "tools")
        conf = f.get("confidence", 0.0)
        if domain not in best or conf > best[domain]["confidence"]:
            best[domain] = f
    return list(best.values())

def warden_filter(tiles):
    """Warden: filter by confidence >= priority threshold.
    Dead tiles (expired constraints, confidence < 0.3) are dropped."""
    kept = []
    for t in tiles:
        priority, threshold = get_priority(t.get("confidence", 0.0))
        if t.get("confidence", 0.0) >= threshold and not t.get("is_dead", False):
            kept.append(t)
    return kept

def healer_repair(tiles):
    """Healer: flag expired tiles for soft re-evaluation.
    Dead tiles with very low confidence get restored with degraded confidence."""
    repaired = []
    for t in tiles:
        if t.get("is_dead", False) and t.get("confidence", 1.0) < 0.3:
            t["is_dead"] = False
            t["confidence"] = 0.3
            t["question"] = "[RE-EVAL] " + t.get("question", "")
        repaired.append(t)
    return repaired

# ── Scanning ─────────────────────────────────────────────────

def scan_plato_rooms():
    rooms = plato_get("/rooms")
    if not rooms:
        return []
    result = []
    for name, info in rooms.items():
        result.append({
            "name": name, "tiles": info.get("tile_count", 0),
            "created": info.get("created", ""),
        })
    return sorted(result, key=lambda r: -r["tiles"])

def scan_recent_commits():
    repos = [
        "constraint-theory-llvm", "flux-vm", "flux-compiler",
        "eisenstein-do178c", "keel", "holonomy-consensus",
        "fleet-coordinate", "fleet-spread", "fleet-murmur",
        "cocapn-ai-web", "flux-hardware", "eisenstein",
        "plato-mythos", "plato-mythos-glue", "open-mythos-edge",
    ]
    findings = []
    for repo in repos:
        try:
            result = subprocess.run(
                ["gh", "api", "repos/SuperInstance/" + repo + "/commits?per_page=3"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode != 0 or not result.stdout.strip():
                continue
            commits = json.loads(result.stdout)
            for c in commits:
                author = c.get("commit", {}).get("author", {}).get("name", "?")
                msg = c.get("commit", {}).get("message", "").split("\n")[0]
                date = c.get("commit", {}).get("author", {}).get("date", "")[:16]
                sha = c["sha"][:8]
                findings.append({
                    "question": date + " " + repo + ": " + sha,
                    "answer": author + ": " + msg,
                    "confidence": 0.85,
                    "source": "github",
                    "domain": "research",
                    "is_dead": False,
                })
        except:
            pass
    return findings

def scan_services():
    ports = {
        "keeper": 8900, "agent-api": 8901, "plato": 8847,
        "holodeck": 7778, "seed-mcp": 9438, "mud": 4042,
        "lock": 4043, "arena": 4044, "grammar": 4045,
    }
    status = {}
    for name, port in ports.items():
        try:
            urllib.request.urlopen("http://localhost:" + str(port) + "/", timeout=3)
            status[name] = "up"
        except:
            try:
                urllib.request.urlopen("http://localhost:" + str(port) + "/status", timeout=3)
                status[name] = "up"
            except:
                status[name] = "down"
    return status

# ── Mythos Routing ───────────────────────────────────────────

def route_to_rooms(findings):
    """Route findings to domain-expert PLATO rooms (Rooms as Experts).
    Uses confidence-weighted gating: high confidence → direct post,
    low confidence → batch into summary tile."""
    by_room = defaultdict(list)
    for f in findings:
        domain = f.get("domain", "tools")
        room = DOMAIN_ROOM.get(domain, "oracle1_briefing")
        by_room[room].append(f)

    posted = 0
    for room, tiles in by_room.items():
        # Sort by confidence
        tiles.sort(key=lambda t: -t.get("confidence", 0.0))

        # Bard: select best per room
        bard_best = bard_process(tiles)

        # Warden: filter by threshold
        warden_kept = warden_filter(bard_best)

        # Healer: repair dead tiles
        healed = healer_repair(warden_kept)

        for tile in healed[:3]:  # max 3 per room
            priority, threshold = get_priority(tile.get("confidence", 0.5))
            deadband_note = " [Deadband ACT: " + priority + " @ " + str(threshold) + "]"
            tile["answer"] = tile.get("answer", "") + deadband_note
            tile["tags"] = tile.get("tags", []) + ["mythos", priority.lower()]
            result = plato_post(room, tile)
            if result:
                posted += 1

    return posted

# ── Idle Detection ───────────────────────────────────────────

def is_human_active():
    if not LAST_ACTIVE_FILE.exists():
        return False
    try:
        last = float(LAST_ACTIVE_FILE.read_text().strip())
        return (time.time() - last) < HUMAN_TIMEOUT
    except:
        return False

def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except:
            pass
    return {"loop_count": 0, "last_briefing": 0, "briefing_ids": []}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

# ── Main Loop ────────────────────────────────────────────────

def run_loop():
    print("Ambient Research Loop v2 (Mythos-meshed) starting — PID: " + str(os.getpid()))
    state = load_state()

    while True:
        try:
            state["loop_count"] += 1
            count = state["loop_count"]

            if is_human_active():
                interval = INTERVAL_ACTIVE
                print("Loop #" + str(count) + ": Human active — stretching interval")
            else:
                interval = INTERVAL_IDLE
                print("Loop #" + str(count) + ": Idle — scanning with Mythos routing...")

                # Scan
                rooms = scan_plato_rooms()
                commits = scan_recent_commits()
                services = scan_services()

                # Build findings
                findings = []

                # Room findings → fleet_domain rooms
                for r in rooms:
                    domain = r["name"].replace("fleet_", "").replace("oracle1_", "").split("_")[0]
                    findings.append({
                        "question": "Room: " + r["name"],
                        "answer": str(r["tiles"]) + " tiles",
                        "confidence": min(r["tiles"] / 100.0, 1.0),
                        "source": "plato",
                        "domain": domain if domain in DOMAIN_ROOM else "tools",
                        "is_dead": False,
                    })

                # Recent commits → fleet_research
                findings.extend(commits)

                # Service health → fleet_infrastructure
                for name, status in services.items():
                    findings.append({
                        "question": "Service: " + name,
                        "answer": status,
                        "confidence": 0.95 if status == "up" else 0.3,
                        "source": "health",
                        "domain": "infrastructure",
                        "is_dead": status == "down",
                    })

                # Route findings to Mythos-expert rooms
                posted = route_to_rooms(findings)
                # Embed findings as field nails for emergence detection
                for f in findings[:5]:
                    pos = sum(ord(c) for c in f.get("question", "")) % 200 - 100
                    conf = f.get("confidence", 0.5)
                    import subprocess
                    subprocess.run(["python3", "scripts/field_cli.py", "embed",
                        "--position", str(pos),
                        "--weight", str(conf),
                        "--stiffness", "12",
                        "--tau", "3600"],
                        capture_output=True)
                
                # Check field topology for emergence signals
                topo = subprocess.run(["python3", "scripts/field_cli.py", "topology"],
                    capture_output=True, text=True)
                if "breaching" in topo.stdout or "unstable" in topo.stdout:
                    print("EMERGENCE: field topology breach detected")
                    import json, hashlib, urllib.request
                    breach = {"domain": "fleet_math",
                        "question": "Field topology alert",
                        "answer": topo.stdout.strip(),
                        "confidence": 0.9, "source": "ambient"}
                    breach["_hash"] = hashlib.sha256(json.dumps(breach, sort_keys=True).encode()).hexdigest()[:16]
                    try:
                        req = urllib.request.Request(PLATO_URL + "/room/forge/submit",
                            data=json.dumps(breach).encode(),
                            headers={"Content-Type": "application/json"}, method="POST")
                        urllib.request.urlopen(req, timeout=5)
                    except:
                        pass

                state["last_briefing"] = time.time()
                print("Loop #" + str(count) + ": " + str(posted) + " tiles routed to domain rooms")

            save_state(state)
            time.sleep(interval)

        except KeyboardInterrupt:
            print("Shutting down")
            save_state(state)
            break
        except Exception as e:
            print("Error: " + str(e))
            time.sleep(60)

if __name__ == "__main__":
    run_loop()
