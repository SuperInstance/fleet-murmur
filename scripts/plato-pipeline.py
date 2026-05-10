#!/usr/bin/env python3
"""
PLATO Data Pipeline — hourly worker

Fetches all tiles from PLATO, deduplicates, computes trust scores,
and exports training-ready snapshots to /data/plato-training/.

Usage:
    plato-pipeline.py                     # Full hourly run
    plato-pipeline.py --verify            # Check output files only
"""

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

# --- Configuration ---
PLATO_BASE = "http://localhost:8847"
INGEST_DIR = Path("/data/plato-ingest")
TRAINING_DIR = Path("/data/plato-training")
MANIFEST_DIR = TRAINING_DIR / "manifests"

RAW_LOG = INGEST_DIR / "raw-tiles.jsonl"
DEDUP_STORE = INGEST_DIR / "dedup-store.jsonl"
TRUST_FILE = INGEST_DIR / "trust-scores.json"
STATE_FILE = INGEST_DIR / "pipeline-state.json"


def log(msg):
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[{ts}] {msg}", flush=True)


def fetch_json(path, max_retries=3, retry_delay=1.0):
    """Fetch JSON from PLATO server with retry logic. Return parsed dict/list or None."""
    url = f"{PLATO_BASE}{path}"
    last_error = None

    for attempt in range(max_retries):
        try:
            req = Request(url, headers={"Accept": "application/json"})
            with urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except URLError as e:
            last_error = e
            if attempt < max_retries - 1:
                log(f"WARN: fetch {url} failed (attempt {attempt + 1}/{max_retries}): {e}, retrying...")
                time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
            else:
                log(f"WARN: fetch {url} failed after {max_retries} attempts: {e}")
        except json.JSONDecodeError as e:
            log(f"WARN: fetch {url} bad JSON: {e}")
            return None

    return None


def compute_hash(question, answer):
    """SHA-256 hex digest of canonical question+answer."""
    canonical = f"{question.strip().lower()}|||{answer.strip().lower()}"
    return hashlib.sha256(canonical.encode()).hexdigest()


def load_state():
    """Load pipeline state dict."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"last_run": None, "tile_ids_seen": []}


def save_state(state):
    """Write pipeline state atomically."""
    tmp = STATE_FILE.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, STATE_FILE)  # Cross-platform atomic rename


def load_trust_scores():
    """Load trust score registry."""
    if TRUST_FILE.exists():
        try:
            with open(TRUST_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_trust_scores(scores):
    """Write trust scores atomically."""
    tmp = TRUST_FILE.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(scores, f, indent=2, sort_keys=True)
    tmp.rename(TRUST_FILE)


def load_dedup_index():
    """Load dedup store into a dict keyed by hash. Also returns raw lines for append."""
    index = {}
    lines = []
    if DEDUP_STORE.exists():
        with open(DEDUP_STORE) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    h = entry.get("hash")
                    if h:
                        index[h] = entry
                        lines.append(line)
                except json.JSONDecodeError:
                    continue
    return index, lines


def append_raw_tile(tile):
    """Append one raw tile JSON line to raw log."""
    RAW_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(RAW_LOG, "a") as f:
        f.write(json.dumps(tile, sort_keys=True) + "\n")


def write_dedup_store(lines):
    """Write all dedup lines atomically."""
    tmp = DEDUP_STORE.with_suffix(".tmp")
    with open(tmp, "w") as f:
        for line in lines:
            f.write(line + "\n") if isinstance(line, str) else f.write(line)
    tmp.rename(DEDUP_STORE)


def step_fetch_all_tiles():
    """Fetch all tiles from every room, return list of tile dicts."""
    log("Fetching tile listing from PLATO...")

    rooms_resp = fetch_json("/rooms")
    if rooms_resp is None:
        log("ERROR: could not fetch room list from PLATO")
        return []

    # Handle both list and dict responses
    rooms = []
    if isinstance(rooms_resp, dict):
        rooms = list(rooms_resp.keys())
    elif isinstance(rooms_resp, list):
        rooms = rooms_resp
    else:
        log(f"WARN: unexpected rooms response type: {type(rooms_resp)}")
        return []

    all_tiles = []
    for room_name in rooms:
        resp = fetch_json(f"/room/{room_name}/tiles")
        if resp is None:
            continue
        tiles = []
        if isinstance(resp, dict) and "tiles" in resp:
            tiles = resp["tiles"]
        elif isinstance(resp, list):
            tiles = resp
        else:
            log(f"WARN: unexpected tiles response for {room_name}: {type(resp)}")
            continue

        for tile in tiles:
            tile["_room"] = room_name
            all_tiles.append(tile)

    log(f"Fetched {len(all_tiles)} tiles across {len(rooms)} rooms")
    return all_tiles


def step_ingest(tiles):
    """Append raw tiles to raw log, return new tile count."""
    count = 0
    for tile in tiles:
        # Build a standardised raw record
        provenance = tile.get("provenance", {})
        q = tile.get("question", "")
        a = tile.get("answer", "")
        raw_record = {
            "tile_id": provenance.get("tile_id", ""),
            "question": q,
            "answer": a,
            "domain": tile.get("domain", provenance.get("room", "")),
            "source": tile.get("source", "direct_submit"),
            "confidence": tile.get("confidence", 0.5),
            "tags": tile.get("tags", []),
            "hash": compute_hash(q, a),
            "prev_hash": None,
            "agent_id": provenance.get("agent_id", "unknown"),
            "agent_trust_score": 0.5,
            "created_at": datetime.fromtimestamp(
                provenance.get("timestamp", time.time()),
                tz=timezone.utc
            ).isoformat(),
            "_raw_hash_plato": tile.get("_hash", ""),
            "_room": tile.get("_room", ""),
        }
        append_raw_tile(raw_record)
        count += 1
    return count


def step_dedup_and_trust(tiles):
    """Deduplicate new raw tiles and update trust scores."""
    log("Running dedup pass...")

    dedup_index, dedup_lines = load_dedup_index()
    trust_scores = load_trust_scores()
    now = datetime.now(timezone.utc).isoformat()

    new_entries = 0
    updated_entries = 0

    for tile in tiles:
        q = tile.get("question", "")
        a = tile.get("answer", "")
        h = compute_hash(q, a)
        agent = tile.get("agent_id", "unknown")
        conf = tile.get("confidence", 0.5)
        domain = tile.get("domain", "")
        room = tile.get("_room", "")

        if h in dedup_index:
            # Update existing entry
            entry = dedup_index[h]
            entry["last_seen"] = now
            entry["occurrences"] = entry.get("occurrences", 1) + 1
            if agent not in entry.get("contributors", []):
                entry.setdefault("contributors", []).append(agent)
            # Running average confidence
            old_avg = entry.get("avg_confidence", conf)
            count = entry.get("occurrences", 1)
            entry["avg_confidence"] = round(
                (old_avg * (count - 1) + conf) / count, 4
            )
            updated_entries += 1
        else:
            # New dedup entry
            entry = {
                "hash": h,
                "question": q,
                "answer": a,
                "domain": domain or room,
                "first_seen": now,
                "last_seen": now,
                "occurrences": 1,
                "contributors": [agent],
                "avg_confidence": conf,
                "tags": tile.get("tags", []),
                "trust_score": 0.5,
                "status": "active",
            }
            dedup_index[h] = entry
            dedup_lines.append("")  # placeholder — rebuilt below
            new_entries += 1

    log(f"Dedup: {new_entries} new, {updated_entries} updated, {len(dedup_index)} total unique")

    # --- Trust scoring ---
    log("Computing trust scores...")
    for h, entry in dedup_index.items():
        for agent in entry.get("contributors", []):
            if agent not in trust_scores:
                trust_scores[agent] = {
                    "trust": 0.50,
                    "tiles_contributed": 0,
                    "tiles_retained_over_30d": 0,
                    "low_confidence_count": 0,
                    "first_seen": now,
                    "last_updated": now,
                }
            ts = trust_scores[agent]
            ts["tiles_contributed"] = (ts.get("tiles_contributed", 0) + 1) // max(
                1, len(entry.get("contributors", [agent]))
            )
            # Check retention (older than 30 days)
            try:
                first = datetime.fromisoformat(entry["first_seen"])
                if (datetime.now(timezone.utc) - first).days > 30:
                    ts["tiles_retained_over_30d"] = (
                        ts.get("tiles_retained_over_30d", 0) + 1
                    )
            except (ValueError, TypeError):
                pass
            # Check low confidence
            if entry.get("avg_confidence", 0.5) < 0.3:
                ts["low_confidence_count"] = (
                    ts.get("low_confidence_count", 0) + 1
                )

    # Recalculate trust scores
    agent_tiles = {}  # track per-agent tile set to avoid double counting
    for h, entry in dedup_index.items():
        for agent in entry.get("contributors", []):
            if agent not in agent_tiles:
                agent_tiles[agent] = set()
            agent_tiles[agent].add(h)

    for agent, tiles_set in agent_tiles.items():
        if agent not in trust_scores:
            continue
        ts = trust_scores[agent]
        trust = 0.50
        trust += ts.get("tiles_retained_over_30d", 0) * 0.05
        trust -= ts.get("low_confidence_count", 0) * 0.05
        trust = max(0.0, min(1.0, round(trust, 4)))
        ts["trust"] = trust
        ts["last_updated"] = now

    # Also assign trust_score to each dedup entry
    for h, entry in dedup_index.items():
        # Use the average trust of all contributors
        trusts = []
        for agent in entry.get("contributors", []):
            t = trust_scores.get(agent, {}).get("trust", 0.5)
            trusts.append(t)
        entry["trust_score"] = (
            round(sum(trusts) / len(trusts), 4) if trusts else 0.5
        )

    # Write updated dedup store with trust scores
    updated_lines = [json.dumps(dedup_index[h], sort_keys=True) for h in dedup_index]
    write_dedup_store(updated_lines)

    save_trust_scores(trust_scores)
    log(
        f"Trust scores: {len(trust_scores)} agents tracked"
    )

    return dedup_index


def step_export_training(dedup_index):
    """Export training-ready snapshots by trust threshold."""
    log("Exporting training snapshots...")

    TRAINING_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

    tiers = {
        "tiles.jsonl": 0.3,
        "tiles-moderate.jsonl": 0.5,
        "high-quality.jsonl": 0.7,
    }

    tier_counts = {}
    all_exported = []

    for filename, min_score in tiers.items():
        path = TRAINING_DIR / filename
        entries = []
        for h, entry in dedup_index.items():
            trust = entry.get("trust_score", 0.5)
            if trust >= min_score:
                out = {
                    "question": entry.get("question", ""),
                    "answer": entry.get("answer", ""),
                    "domain": entry.get("domain", ""),
                    "confidence": entry.get("avg_confidence", 0.5),
                    "trust_score": trust,
                }
                entries.append(out)
                all_exported.append(out)

        with open(path, "w") as f:
            for e in entries:
                f.write(json.dumps(e, sort_keys=True) + "\n")

        tier_counts[filename] = len(entries)
        log(f"  {filename}: {len(entries)} tiles (trust >= {min_score})")

    # Generate manifest
    agents_contributing = set()
    for h, entry in dedup_index.items():
        for agent in entry.get("contributors", []):
            agents_contributing.add(agent)

    all_trusts = [
        entry.get("trust_score", 0.5) for entry in dedup_index.values()
    ]
    avg_trust = round(sum(all_trusts) / len(all_trusts), 4) if all_trusts else 0

    manifest = {
        "snapshot_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "type": "hourly_broad",
        "tile_count": tier_counts.get("tiles.jsonl", 0),
        "tile_count_moderate": tier_counts.get("tiles-moderate.jsonl", 0),
        "tile_count_high_quality": tier_counts.get("high-quality.jsonl", 0),
        "total_unique": len(dedup_index),
        "agents_contributing": len(agents_contributing),
        "avg_trust": avg_trust,
        "avg_confidence": round(
            sum(entry.get("avg_confidence", 0.5) for entry in dedup_index.values())
            / max(1, len(dedup_index)),
            4,
        ),
        "total_tiles_by_tier": tier_counts,
    }

    # Also write to training dir as latest manifest
    manifest_path = TRAINING_DIR / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    # Timestamped manifest
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    dated_manifest = MANIFEST_DIR / f"hourly-{ts}.json"
    with open(dated_manifest, "w") as f:
        json.dump(manifest, f, indent=2)

    log(f"Manifest written: {manifest_path}")
    log(f"Manifest archived: {dated_manifest}")

    return manifest


def step_verify_outputs():
    """Check all expected output files exist and have content."""
    log("=== Verification ===")
    paths = [
        ("Raw log", RAW_LOG, True),
        ("Dedup store", DEDUP_STORE, True),
        ("Trust scores", TRUST_FILE, True),
        ("Broad tiles", TRAINING_DIR / "tiles.jsonl", True),
        ("Moderate tiles", TRAINING_DIR / "tiles-moderate.jsonl", True),
        ("High-quality tiles", TRAINING_DIR / "high-quality.jsonl", False),
        ("Manifest", TRAINING_DIR / "manifest.json", True),
    ]
    all_ok = True
    for label, path, require_content in paths:
        if not path.exists():
            log(f"  ✗ {label}: {path} MISSING")
            all_ok = False
            continue
        size = path.stat().st_size
        count = 0
        if path.suffix == ".jsonl":
            try:
                with open(path) as f:
                    count = sum(1 for _ in f if _.strip())
            except Exception:
                pass
        elif path.suffix == ".json":
            try:
                with open(path) as f:
                    data = json.load(f)
                    count = len(data) if isinstance(data, list) else "ok"
            except Exception:
                count = "?"
        if size == 0 and require_content:
            log(f"  ✗ {label}: {path} is empty ({size} bytes, {count} lines/entries)")
            all_ok = False
        else:
            status = "✓" if (not require_content or size > 0) else "✗"
            log(f"  {status} {label}: {path} ({size} bytes, {count} lines/entries)")
    return all_ok


def main():
    verify_only = "--verify" in sys.argv

    if verify_only:
        ok = step_verify_outputs()
        return 0 if ok else 1

    log("=== PLATO Data Pipeline Run ===")
    state = load_state()

    # 1. Fetch all tiles from PLATO
    tiles = step_fetch_all_tiles()
    if not tiles:
        log("WARN: no tiles fetched, proceeding with existing data only")
        state["last_run"] = datetime.now(timezone.utc).isoformat()
        save_state(state)
        # Still run dedup/export on existing data
        dedup_index, _ = load_dedup_index()
        if dedup_index:
            step_export_training(dedup_index)
            step_verify_outputs()
        log("=== Pipeline complete (no new tiles) ===")
        return 0

    # 2. Ingest raw tiles
    ingested = step_ingest(tiles)
    log(f"Ingested {ingested} new raw tiles")

    # 3. Dedup + trust (processes all tiles, not just new ones)
    #    For real efficiency we'd track offsets, but full pass is fine for hourly
    dedup_index = step_dedup_and_trust(tiles)

    # 4. Export training snapshots
    manifest = step_export_training(dedup_index)

    # 5. Update state
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    state["total_unique_tiles"] = len(dedup_index)
    state["last_manifest"] = manifest
    save_state(state)

    # 6. Verify
    step_verify_outputs()

    log("=== Pipeline complete ===")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        log("Interrupted")
        sys.exit(1)
    except Exception as e:
        log(f"FATAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
