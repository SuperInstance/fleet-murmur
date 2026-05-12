#!/usr/bin/env python3
"""
Dodecet→PLATO Bridge — syncs FM's dodecet-encoder tiles into PLATO rooms.

FM's Seed Discovery Engine and Temporal Agent produce DiscoveryTiles and
temporal state. This bridge reads them from stdout/file/API and submits
them to PLATO rooms where the rest of the fleet can use them.

Architecture:
    dodecet-encoder (Rust, FM's machine)
        │  produces DiscoveryTiles via stdout / file write / API
        ▼
    dodecet_bridge.py (this script, on Keeper)
        │  reads tiles, converts to PLATO format
        ▼
    PLATO room dodecet-discoveries/
        │  persistent, shareable, visible to all agents
        ▼
    Agent runtime + ScummVM → humans see FM's discoveries
"""

import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from typing import Optional

PLATO_URL = "http://localhost:8847"
DODECET_ROOM = "dodecet-discoveries"
DODECET_BINARY = ""  # Set to path of FM's binary if running locally

def plato_tile(room: str, question: str, answer: str, tags: list = None) -> bool:
    data = {
        "room": room,
        "question": question[:200],
        "answer": answer[:2000],
        "tags": tags or [],
        "source": "dodecet-bridge",
        "confidence": 0.9,
    }
    req = urllib.request.Request(
        f"{PLATO_URL}/room/{room}/submit",
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read()).get("status") == "accepted"
    except Exception:
        return False

def bridge_dodecet_tile(tile_data: dict) -> bool:
    """Convert a dodecet DiscoveryTile to a PLATO tile and submit it"""
    role = tile_data.get("role", "unknown")
    pattern = tile_data.get("pattern", "")
    params = tile_data.get("optimal_params", {})
    score = tile_data.get("crystallization_score", 0.0)
    iterations = tile_data.get("iterations", 0)
    entropy = tile_data.get("discovery_entropy", 0.0)
    generation = tile_data.get("generation", 0)

    answer = (
        f"Role: {role}\n"
        f"Pattern: {pattern[:500]}\n"
        f"Score: {score:.3f} | Iterations: {iterations} | Entropy: {entropy:.3f}\n"
        f"Generation: {generation}\n"
        f"Parameters:\n"
    )
    for k, v in params.items():
        answer += f"  {k}: {v}\n"

    question = f"DiscoveryTile [{role}] gen={generation} score={score:.3f}"
    tags = ["dodecet", "discovery", role, f"gen-{generation}"]

    return plato_tile(DODECET_ROOM, question, answer, tags)

def bridge_temporal_state(state_data: dict) -> bool:
    """Convert TemporalAgent state to a PLATO tile"""
    phase = state_data.get("phase", "unknown")
    decay = state_data.get("decay_rate", 0.0)
    horizon = state_data.get("prediction_horizon", 0)
    error = state_data.get("prediction_error", 0.0)
    chirality = state_data.get("chirality", "exploring")
    energy = state_data.get("precision_energy", 0.0)

    answer = (
        f"Phase: {phase}\n"
        f"Decay Rate: {decay}\n"
        f"Horizon: {horizon}\n"
        f"Prediction Error: {error:.4f}\n"
        f"Chirality: {chirality}\n"
        f"Precision Energy: {energy:.4f}\n"
    )
    question = f"TemporalAgent [{phase}] err={error:.4f} chirality={chirality}"
    tags = ["dodecet", "temporal", phase]

    return plato_tile(DODECET_ROOM, question, answer, tags)

def watch_dodecet_file(path: str):
    """Watch a file for new dodecet tiles and bridge them to PLATO"""
    print(f"📡 Watching {path} for dodecet tiles...")
    last_pos = os.path.getsize(path) if os.path.exists(path) else 0
    while True:
        try:
            with open(path) as f:
                f.seek(last_pos)
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        tile_type = data.get("type", "discovery")
                        if tile_type == "temporal":
                            ok = bridge_temporal_state(data)
                        else:
                            ok = bridge_dodecet_tile(data)
                        print(f"  {'✅' if ok else '❌'} Bridged {tile_type} tile")
                    except json.JSONDecodeError:
                        pass
                last_pos = f.tell()
        except FileNotFoundError:
            pass
        time.sleep(5)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Dodecet→PLATO Bridge")
    parser.add_argument("--file", help="Watch a file for dodecet JSON tiles")
    parser.add_argument("--once", help="Bridge a single JSON file and exit")
    parser.add_argument("--test", action="store_true", help="Submit a test tile")
    args = parser.parse_args()

    if args.test:
        # Prime the room
        plato_tile(DODECET_ROOM, "Dodecet Bridge activated",
                   "Bridging FM's dodecet-encoder tiles to PLATO. DiscoveryTiles and TemporalAgent state sync here.",
                   tags=["meta", "bridge"])
        print(f"✅ {DODECET_ROOM}/ primed with activation tile")
    
    elif args.once:
        with open(args.once) as f:
            data = json.load(f)
        t = data.get("type", "discovery")
        ok = bridge_dodecet_tile(data) if t == "temporal" else bridge_temporal_state(data)
        print(f"{'✅' if ok else '❌'} Bridged one tile")
    
    elif args.file:
        watch_dodecet_file(args.file)
    
    else:
        print("Usage: dodecet_bridge.py --test | --file <path> | --once <path>")
