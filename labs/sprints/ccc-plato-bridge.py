#!/usr/bin/env python3
"""CCC → PLATO Bridge — Converts CCC's git bottles into PLATO tiles.

Scans CCC's for-fleet/outbox/ and for-fleet/work/ directories.
Converts each markdown file into structured tiles submitted to PLATO.
Also scans from-fleet/inbox/ so Oracle1's responses become CCC's context tiles.

Runs via cron every 5 minutes.
"""
import json, re, os, sys
from pathlib import Path
from datetime import datetime, timezone
import urllib.request

PLATO_URL = "http://localhost:8847"
CCC_SHELL = Path("/tmp/ccc-shell")
PROCESSED_DIR = CCC_SHELL / "memory" / "tiles"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def submit_tile(tile):
    try:
        body = json.dumps(tile).encode()
        req = urllib.request.Request(PLATO_URL + "/submit",
            data=body, headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read())
    except Exception as e:
        return {"status": "error", "reason": str(e)}


def is_processed(filepath):
    marker = PROCESSED_DIR / (filepath.name + ".done")
    return marker.exists()


def mark_processed(filepath):
    marker = PROCESSED_DIR / (filepath.name + ".done")
    marker.write_text(datetime.now(timezone.utc).isoformat())


def harvest_file(filepath, source_tag, domain):
    """Convert a markdown file into PLATO tiles."""
    content = filepath.read_text()
    if len(content) < 30:
        return 0, 0

    submitted = 0
    accepted = 0

    # Split into sections
    sections = re.split(r'\n## ', content)
    for section in sections:
        lines = section.strip().split('\n')
        if len(lines) < 2:
            continue
        
        # Extract a question/title from first line
        question = lines[0].strip().lstrip('#').strip()
        if len(question) < 10:
            continue
        
        # Body is the rest
        body = '\n'.join(lines[1:]).strip()
        if len(body) < 20:
            continue

        tile = {
            "domain": domain,
            "question": question[:200],
            "answer": body[:3000],
            "tags": ["ccc", source_tag, domain, "cocapn-claw"],
            "confidence": 0.7,
            "source": f"ccc:{source_tag}:{filepath.name}",
        }
        result = submit_tile(tile)
        submitted += 1
        if result.get("status") == "accepted":
            accepted += 1

    # If no sections parsed, submit the whole file as one tile
    if submitted == 0:
        tile = {
            "domain": domain,
            "question": filepath.stem.replace("-", " ").replace("_", " ")[:200],
            "answer": content[:3000],
            "tags": ["ccc", source_tag, domain, "cocapn-claw"],
            "confidence": 0.6,
            "source": f"ccc:{source_tag}:{filepath.name}",
        }
        result = submit_tile(tile)
        submitted += 1
        if result.get("status") == "accepted":
            accepted += 1

    return submitted, accepted


def inject_context_into_state():
    """Pull relevant PLATO tiles and inject into CCC's STATE.md."""
    try:
        resp = urllib.request.urlopen(f"{PLATO_URL}/export/plato-tile-spec", timeout=10)
        data = json.loads(resp.read())
        
        # Get latest communication + integration tiles
        comm_tiles = [t for t in data["tiles"] 
                      if t.get("domain") in ("communication", "integration")]
        comm_tiles.sort(key=lambda t: t.get("confidence", 0), reverse=True)
        
        if not comm_tiles:
            return
        
        # Build context section
        context_lines = ["\n## Fleet Knowledge (from PLATO)\n"]
        for t in comm_tiles[:5]:
            context_lines.append(f"- **{t['domain']}**: {t['question'][:80]}")
            context_lines.append(f"  → {t['answer'][:120]}\n")
        
        context = '\n'.join(context_lines)
        
        # Append to STATE.md
        state_file = CCC_SHELL / "STATE.md"
        if state_file.exists():
            current = state_file.read_text()
            # Remove old injected context
            if "## Fleet Knowledge (from PLATO)" in current:
                current = current.split("## Fleet Knowledge (from PLATO)")[0]
            state_file.write_text(current.rstrip() + "\n" + context)
    
    except Exception as e:
        print(f"Context injection error: {e}")


def main():
    total_submitted = 0
    total_accepted = 0

    # Harvest CCC's outbound work
    for subdir in ["for-fleet/outbox", "for-fleet/work"]:
        outbox = CCC_SHELL / subdir
        if not outbox.exists():
            continue
        for f in outbox.glob("*.md"):
            if is_processed(f):
                continue
            s, a = harvest_file(f, "ccc-outbound", "communication")
            total_submitted += s
            total_accepted += a
            if a > 0:
                mark_processed(f)
                print(f"  ✅ {f.name}: {a}/{s} tiles")

    # Harvest CCC's inbound bottles (Oracle1's responses)
    inbox = CCC_SHELL / "from-fleet" / "inbox"
    if inbox.exists():
        for f in inbox.glob("*.md"):
            if is_processed(f):
                continue
            s, a = harvest_file(f, "ccc-inbound", "integration")
            total_submitted += s
            total_accepted += a
            if a > 0:
                mark_processed(f)
                print(f"  ✅ {f.name}: {a}/{s} tiles")

    # Harvest CCC's hooks/intel
    intel = CCC_SHELL / "hooks" / "intel"
    if intel.exists():
        for f in intel.glob("*.json"):
            if is_processed(f):
                continue
            try:
                data = json.loads(f.read_text())
                tile = {
                    "domain": "fleethealth",
                    "question": f"CCC Intel: {f.stem}",
                    "answer": json.dumps(data, indent=2)[:3000],
                    "tags": ["ccc", "intel", "fleethealth", "cocapn-claw"],
                    "confidence": 0.8,
                    "source": f"ccc:intel:{f.name}",
                }
                result = submit_tile(tile)
                total_submitted += 1
                if result.get("status") == "accepted":
                    total_accepted += 1
                    mark_processed(f)
                    print(f"  ✅ {f.name}: intel tile")
            except:
                pass

    # Inject PLATO context into CCC's STATE.md
    inject_context_into_state()

    print(f"\nCCC→PLATO Bridge: {total_accepted}/{total_submitted} tiles accepted")
    return total_accepted


if __name__ == "__main__":
    main()
