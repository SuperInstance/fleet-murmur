#!/usr/bin/env python3
"""
Ambient Research Loop — idle detection -> "12 things" briefing.

When the fleet is idle (no recent human interaction), scans PLATO rooms
for gaps, checks recent activity, and generates a "12 things" briefing
of what's worth knowing.

Runs as a lightweight loop every ~15 minutes when idle.
Silent when the human is active.
"""

import json, os, time, subprocess, sys, hashlib
import urllib.request
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

PLATO_URL = "http://localhost:8847"
STATE_FILE = Path("/tmp/ambient-loop-state.json")
LAST_ACTIVE_FILE = Path("/tmp/ambient-last-human-active")
BRIEFING_ROOM = "oracle1_briefing"
INTERVAL_IDLE = 900
INTERVAL_ACTIVE = 3600
HUMAN_TIMEOUT = 1800


def plato_get(path):
    try:
        resp = urllib.request.urlopen(PLATO_URL + path, timeout=5)
        return json.loads(resp.read())
    except Exception as e:
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
        return resp.read()
    except Exception as e:
        return None


def scan_plato_rooms():
    rooms = plato_get("/rooms")
    if not rooms:
        return []
    result = []
    for name, info in rooms.items():
        result.append({
            "name": name,
            "tiles": info.get("tile_count", 0),
            "created": info.get("created", ""),
        })
    return sorted(result, key=lambda r: -r["tiles"])


def scan_recent_commits():
    repos = [
        "constraint-theory-llvm", "flux-vm", "flux-compiler",
        "eisenstein-do178c", "keel", "holonomy-consensus",
        "fleet-coordinate", "fleet-spread", "fleet-murmur",
        "cocapn-ai-web", "flux-hardware", "eisenstein",
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
                findings.append(date + " " + repo + ": " + sha + " " + author + ": " + msg)
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


def scan_disk():
    try:
        result = subprocess.run(["df", "/"], capture_output=True, text=True, timeout=5)
        line = result.stdout.strip().split("\n")[-1]
        parts = line.split()
        return parts[4] + " used"
    except:
        return "unknown"


def generate_briefing(rooms, commits, services, disk, loop_count):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    things = []

    total_tiles = sum(r["tiles"] for r in rooms)
    total_rooms = len(rooms)
    top_rooms = [r for r in rooms if r["tiles"] > 0][:5]
    empty_rooms = [r for r in rooms if r["tiles"] == 0]

    things.append("PLATO: " + str(total_rooms) + " rooms, " + str(total_tiles) + " tiles")
    
    room_str = ", ".join(r["name"] + " (" + str(r["tiles"]) + ")" for r in top_rooms)
    things.append("Top rooms: " + room_str)
    
    if empty_rooms:
        empty_names = ", ".join(r["name"] for r in empty_rooms)
        things.append("Empty rooms: " + empty_names)

    by_repo = defaultdict(list)
    for c in commits:
        repo_part = c.split(":")[0] if ":" in c else "?"
        by_repo[repo_part].append(c)

    top_active = sorted(by_repo.items(), key=lambda x: -len(x[1]))[:5]
    if top_active:
        things.append("Active repos: " + ", ".join(r for r, _ in top_active))

    for l in commits[:3]:
        things.append("Commit: " + l[:90])

    down_services = [s for s, st in services.items() if st == "down"]
    if down_services:
        things.append("DOWN: " + ", ".join(down_services))
    else:
        up_count = sum(1 for s in services.values() if s == "up")
        things.append("Services: " + str(up_count) + "/" + str(len(services)) + " running")

    things.append("Disk: " + disk)

    things.append("Loop #" + str(loop_count) + " — next scan in ~15m")
    things.append("Generated: " + now)

    return "\n".join(str(i+1) + ". " + t for i, t in enumerate(things[:12]))


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


def run_loop():
    print("Ambient Research Loop starting (PID: " + str(os.getpid()) + ")")
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
                print("Loop #" + str(count) + ": Idle — scanning...")

                rooms = scan_plato_rooms()
                commits = scan_recent_commits()
                services = scan_services()
                disk = scan_disk()
                briefing = generate_briefing(rooms, commits, services, disk, count)

                tile = {
                    "question": "Ambient Briefing #" + str(count),
                    "answer": briefing,
                    "confidence": 0.8,
                    "source": "oracle1",
                    "tags": ["ambient", "briefing", "automated"]
                }
                result = plato_post(BRIEFING_ROOM, tile)

                if result:
                    state["last_briefing"] = time.time()
                    first_line = briefing.split("\n")[0] if briefing else ""
                    print("Loop #" + str(count) + ": Briefing posted — " + first_line)
                else:
                    print("Loop #" + str(count) + ": Failed to post briefing")

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
