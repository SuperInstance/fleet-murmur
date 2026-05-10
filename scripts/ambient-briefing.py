#!/usr/bin/env python3
"""
Ambient Research Loop — "12 Things" Briefing Generator

Detects when the fleet is idle and generates a markdown briefing from
recent PLATO tiles across the most active rooms.

Usage:
    python3 ambient-briefing.py

Dependencies:
    Python stdlib only. Requires PLATO API at localhost:8847.

State:
    /tmp/ambient-state.json  — tracks idle duration and last run time
    /tmp/ambient-briefing.md — most recent briefing output
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

PLATO_BASE = "http://localhost:8847"
STATE_FILE = "/tmp/ambient-state.json"
BRIEFING_FILE = "/tmp/ambient-briefing.md"
IDLE_THRESHOLD_SECONDS = 1800  # 30 minutes
TOP_ROOMS = 5
TILES_PER_ROOM = 10  # fetch this many for picking interesting ones
BRIEFING_TILE_TARGET = 12


# ─── PLATO API helpers ────────────────────────────────────────────────────────

def plato_get(path):
    """Fetch JSON from the PLATO API. Returns None on failure."""
    url = f"{PLATO_BASE}{path}"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, json.JSONDecodeError) as e:
        print(f"  [warn] PLATO API error on {path}: {e}", file=sys.stderr)
        return None


def plato_submit(question, answer, domain="ambient-briefings", source="ambient-loop", confidence=0.8):
    """Submit a tile to PLATO. Logs errors, never crashes."""
    body = json.dumps({
        "domain": domain,
        "question": question,
        "answer": answer,
        "source": source,
        "confidence": confidence,
    }).encode()
    req = urllib.request.Request(
        f"{PLATO_BASE}/submit",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read().decode())
            print(f"  [plato] Submitted to {domain}: {result.get('status', 'ok')}", file=sys.stderr)
            return result
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, json.JSONDecodeError) as e:
        print(f"  [warn] PLATO submit error: {e}", file=sys.stderr)
        return None


def get_status():
    """Fetch PLATO /status."""
    return plato_get("/status")


def get_room_tiles(room_name, limit=10):
    """Fetch tiles from a specific room."""
    data = plato_get(f"/room/{room_name}/tiles?limit={limit}")
    if data is None:
        return []
    return data.get("tiles", [])


# ─── State management ────────────────────────────────────────────────────────

def load_state():
    """Load ambient state from file, or return defaults."""
    if not os.path.exists(STATE_FILE):
        return {"first_run": True, "last_briefing_time": 0, "idle_since": None}
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"  [warn] Failed to load state: {e}, using defaults", file=sys.stderr)
        # Backup corrupted state file for debugging
        if os.path.exists(STATE_FILE):
            backup_path = STATE_FILE + ".corrupted"
            try:
                os.rename(STATE_FILE, backup_path)
                print(f"  [warn] Backed up corrupted state to {backup_path}", file=sys.stderr)
            except OSError:
                pass
        return {"first_run": True, "last_briefing_time": 0, "idle_since": None}


def save_state(state):
    """Persist ambient state to file."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# ─── Idle detection ──────────────────────────────────────────────────────────

def detect_idle(status):
    """
    Check if the fleet is idle based on recent tile activity.
    Returns (is_idle, idle_since_timestamp, recent_tile_count).
    """
    now = time.time()
    recent_cutoff = now - IDLE_THRESHOLD_SECONDS
    recent_count = 0
    newest_tile_ts = 0

    rooms = status.get("rooms", {})
    for room_name, room_info in rooms.items():
        # Fetch recent tiles for this room
        tiles = get_room_tiles(room_name, limit=5)
        for tile in tiles:
            prov = tile.get("provenance", {})
            ts = prov.get("timestamp", 0)
            if ts and ts >= recent_cutoff:
                recent_count += 1
                if ts > newest_tile_ts:
                    newest_tile_ts = ts

    return recent_count < 3, newest_tile_ts, recent_count


# ─── Briefing generation ────────────────────────────────────────────────────

def pick_interesting_tiles(tiles, n=12):
    """
    Pick the most interesting tiles from a list.
    "Interesting" = high confidence changes, unusual sources, non-repetitive content.
    """
    if not tiles:
        return []

    # Sort by: higher confidence, non-empty questions, non-trivial answers
    def interesting_score(tile):
        q = tile.get("question", "") or ""
        a = tile.get("answer", "") or ""
        conf = tile.get("confidence", 0.5)
        source = tile.get("source", "unknown")

        score = conf * 10

        # Longer questions/answers are more informative
        if len(q) > 20:
            score += 5
        if len(a) > 50:
            score += 5

        # Reward variety in source (deterministic via string length)
        score += (len(source) * 0.1)

        return score

    scored = sorted(tiles, key=interesting_score, reverse=True)

    # De-duplicate by question stem (first 40 chars)
    seen = set()
    unique = []
    for tile in scored:
        key = tile.get("question", "")[:40]
        if key not in seen:
            seen.add(key)
            unique.append(tile)

    return unique[:n]


def get_most_active_rooms(status, n=5):
    """Get the top N rooms by tile count."""
    rooms = status.get("rooms", {})
    sorted_rooms = sorted(rooms.items(), key=lambda x: x[1].get("tile_count", 0), reverse=True)
    return [(name, info) for name, info in sorted_rooms[:n]]


def generate_briefing(status, state):
    """Generate the full markdown briefing."""
    now = time.time()
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))

    rooms_info = status.get("rooms", {})
    total_tiles = status.get("total_tiles", 0)
    chain_len = status.get("provenance", {}).get("chain_length", 0)
    trust_entries = status.get("provenance", {}).get("trust_entries", 0)
    uptime = status.get("uptime", 0)

    # Human-friendly uptime
    uptime_days = int((now - (status.get("_startup_ts", now - 3600))) if "_startup_ts" in status else 0)
    # We'll use the gateway_stats uptime field which is a float timestamp
    # Guard against underflow if uptime is in the future
    uptime_hours = int(max(0, now - uptime) / 3600) if uptime > 1000000000 else 0
    uptime_str = f"{uptime_hours}h" if uptime_hours < 48 else f"{uptime_hours // 24}d {uptime_hours % 24}h"

    total_rooms = len(rooms_info)
    agent_sources = set()
    for info in rooms_info.values():
        pass  # We'll get agents from actual tiles

    # Top rooms by activity
    active_rooms = get_most_active_rooms(status, TOP_ROOMS)

    # Collect interesting tiles from top rooms
    all_interesting_tiles = []
    for room_name, room_info in active_rooms:
        tiles = get_room_tiles(room_name, TILES_PER_ROOM)
        for t in tiles:
            t["_room"] = room_name
            src = t.get("source", "unknown")
            if src:
                agent_sources.add(src)
        all_interesting_tiles.extend(tiles)

    # Also check recently created rooms (cfp, dawn-briefing, etc.)
    all_room_names = list(rooms_info.keys())

    # Pick the 12 most interesting tiles
    top_tiles = pick_interesting_tiles(all_interesting_tiles, BRIEFING_TILE_TARGET)

    # Detect patterns
    topics_seen = {}
    for tile in all_interesting_tiles:
        q = tile.get("question", "") or ""
        topic_words = [w for w in q.lower().split() if len(w) > 4]
        for w in topic_words:
            topics_seen[w] = topics_seen.get(w, 0) + 1

    # Sort by frequency, pick top patterns
    common_topics = sorted(topics_seen.items(), key=lambda x: -x[1])[:8]

    # Room activity ranking
    room_ranking = []
    for name, info in active_rooms:
        room_ranking.append((name, info.get("tile_count", 0)))

    # ─── Build the markdown ────────────────────────────────────────────────

    lines = []
    lines.append(f"# ⚡ Ambient Briefing — {now_iso}")
    lines.append("")
    lines.append("## Fleet Status")
    lines.append("")
    lines.append(f"- **Total tiles:** {total_tiles}")
    lines.append(f"- **Total rooms:** {total_rooms}")
    lines.append(f"- **Agent sources:** {len(agent_sources)}")
    lines.append(f"- **Chain length:** {chain_len}")
    lines.append(f"- **Trust entries:** {trust_entries}")
    lines.append(f"- **PLATO uptime:** {uptime_str}")
    lines.append(f"- **Idle since:** {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(state.get('idle_since', now)))}")
    lines.append("")

    # Top 5 rooms
    lines.append("## Top Rooms by Activity")
    lines.append("")
    for i, (name, count) in enumerate(room_ranking, 1):
        lines.append(f"{i}. **{name}** — {count} tiles")
    lines.append("")

    # 12 interesting tiles
    lines.append("## 12 Most Interesting Recent Tiles")
    lines.append("")
    for i, tile in enumerate(top_tiles, 1):
        room = tile.get("_room", tile.get("domain", "?"))
        q = tile.get("question", "") or "(empty)"
        a = tile.get("answer", "") or "(empty)"
        conf = tile.get("confidence", 0)
        src = tile.get("source", "?")
        ts = tile.get("provenance", {}).get("timestamp", 0)
        ts_str = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(ts)) if ts else "?"

        # Truncate answer if needed
        a_display = a if len(a) <= 120 else a[:117] + "..."

        lines.append(f"### {i}. {room}")
        lines.append(f"**Q:** {q}")
        lines.append(f"**A:** {a_display}")
        lines.append(f"*Conf: {conf:.2f} | Source: {src} | {ts_str}*")
        lines.append("")

    # Notable patterns
    lines.append("## Notable Patterns")
    lines.append("")
    if common_topics:
        for word, freq in common_topics:
            lines.append(f"- **{word}** — appears {freq} times")
    else:
        lines.append("_No strong patterns detected._")

    # Confidence range
    confs = [t.get("confidence", 0) for t in all_interesting_tiles if t.get("confidence")]
    if confs:
        avg_conf = sum(confs) / len(confs)
        min_conf = min(confs)
        max_conf = max(confs)
        lines.append(f"- **Confidence range:** {min_conf:.2f} – {max_conf:.2f} (avg: {avg_conf:.2f})")

    # Source diversity
    lines.append(f"- **Unique sources:** {', '.join(sorted(agent_sources)[:10])}")
    if len(agent_sources) > 10:
        lines.append(f"  _... and {len(agent_sources) - 10} more_")

    lines.append("")
    lines.append("---")
    lines.append(f"*Generated by ambient-briefing.py at {now_iso}*")
    lines.append("")

    return "\n".join(lines)


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    # Load state
    state = load_state()
    now = time.time()

    # Fetch PLATO status
    status = get_status()
    if status is None:
        print("PLATO unreachable")
        sys.exit(1)

    # Detect idle
    is_idle, newest_ts, recent_count = detect_idle(status)
    print(f"  Fleet activity: {recent_count} tiles in last 30 min", file=sys.stderr)

    if state.get("first_run"):
        print("  First run — generating briefing immediately", file=sys.stderr)
        state["first_run"] = False
        state["idle_since"] = now
    elif not is_idle:
        recent_ts_str = time.strftime("%H:%M UTC", time.gmtime(newest_ts))
        print(f"  Fleet active (last tile at {recent_ts_str}) — skipping", file=sys.stderr)
        # Update last activity and exit
        state["idle_since"] = None
        save_state(state)
        print("Fleet is active — no briefing generated.")
        print("Briefing saved to /tmp/ambient-briefing.md")
        sys.exit(0)

    # Fleet is idle (or first run) — generate briefing
    if state.get("idle_since") is None:
        state["idle_since"] = now

    print("⚡ Fleet idle. Generating 12-things briefing...")
    print(file=sys.stderr)

    briefing = generate_briefing(status, state)

    # Print to stdout
    print(briefing)

    # Save to file
    with open(BRIEFING_FILE, "w") as f:
        f.write(briefing)

    # Submit to PLATO for persistent memory
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))
    plato_submit(
        question=f"ambient briefing {now_iso}",
        answer=briefing[:2000],
        domain="ambient-briefings",
        source="ambient-loop",
        confidence=0.8,
    )

    # Update state
    state["last_briefing_time"] = now
    save_state(state)

    print(file=sys.stderr)
    print(f"Briefing saved to {BRIEFING_FILE}")


if __name__ == "__main__":
    main()
