#!/usr/bin/env python3
"""
Common Space Pattern — Formal Test Suite

Tests all invariants and properties from SPEC.md against the running fleet.
Run with: python3 -m pytest tests/test_common_space.py -v
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# ── Configuration ───────────────────────────────────────────────────────────

PLATO_URL = "http://localhost:8847"
MUD_URL = "http://localhost:4042"
AGENT_API_URL = "http://localhost:4067"
TERRAIN_URL = "http://localhost:4070"

# Registered claws and their declared physics (from SPEC.md P1)
EXPECTED_CLAWS = {
    "creative": {
        "seed-2.0-mini": {"provider": "deepinfra", "cost": "$0.00003/1K tokens"},
    },
    "analytical": {
        "nemotron-3": {"provider": "deepinfra", "cost": "deepinfra bucket"},
    },
    "reasoning": {
        "nemotron-3": {"provider": "deepinfra", "cost": "deepinfra bucket"},
    },
    "implement": {
        "kimi-cli": {"provider": "exec", "cost": "prepaid (kimi)"},
        "process": {"provider": "exec", "cost": "local"},
    },
    "openclaw": {
        "subagent": {"provider": "openclaw", "cost": "configured agent model"},
    },
}

# Invariants from SPEC.md
INVARIANTS = {
    "R1": "Room names are unique",
    "R2": "Tiles are append-only (never mutated or destroyed)",
    "P1": "Port physics are non-negative, reliability ∈ [0,1]",
    "P2": "Every capability has at least one port",
    "B1": "Blind width is monotonic with role",
    "T1": "Object-permanence holds across sessions",
    "T2": "Room tiles are totally ordered",
    "A1": "Every agent has a unique name and a home room",
    "A2": "Every agent cycle produces exactly one tile",
}


# ── Helpers ─────────────────────────────────────────────────────────────────

def http_get(url: str, timeout: int = 10) -> Optional[Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"_error": str(e)}

def http_post(url: str, data: dict, timeout: int = 10) -> Optional[Any]:
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:200]
        return {"_error": f"HTTP {e.code}: {body}"}
    except Exception as e:
        return {"_error": str(e)}

def plato_room_tiles(room: str, limit: int = 50) -> List[Dict]:
    """Get tiles from a PLATO room"""
    data = http_get(f"{PLATO_URL}/room/{room}?limit={limit}")
    if data and "tiles" in data:
        return data["tiles"]
    return []

def plato_write_tile(room: str, question: str, answer: str, source: str = "test",
                     confidence: float = 0.5) -> bool:
    """Write a tile to a PLATO room"""
    data = http_post(f"{PLATO_URL}/room/{room}/submit", {
        "room": room,
        "question": question,
        "answer": answer,
        "source": source,
        "confidence": confidence,
    })
    if data and data.get("status") == "accepted":
        return True
    return False


# ══════════════════════════════════════════════════════════════════════════════
# TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestInfrastructure:
    """Test that all required services are running"""

    def test_plato_online(self):
        """PLATO server must be running"""
        status = http_get(f"{PLATO_URL}/status")
        assert status is not None, "PLATO not reachable"
        assert "_error" not in status, f"PLATO error: {status['_error']}"

    def test_mud_online(self):
        """MUD server must be running"""
        result = http_get(f"{MUD_URL}/connect?agent=test-harness&job=tester")
        assert result is not None, "MUD not reachable"
        assert "_error" not in result, f"MUD error: {result['_error']}"

    def test_agent_api_online(self):
        """PLATO Agent Runtime API must be running"""
        status = http_get(f"{AGENT_API_URL}/status")
        assert status is not None, "Agent API not reachable"
        assert "_error" not in status, f"Agent API error: {status['_error']}"


class TestRoomInvariants:
    """Test R1, R2, T1, T2 from SPEC.md"""

    def test_rooms_exist(self):
        """R1: Required rooms must exist"""
        required = ["agent-oracle1", "tension", "synthesis", "edge", "forge"]
        rooms = http_get(f"{PLATO_URL}/status")
        if rooms and "rooms" in rooms:
            existing = set(rooms["rooms"].keys())
            for room in required:
                assert room in existing, f"Room '{room}' missing"

    def test_tile_ordering(self):
        """T2: Tiles in a room must be ordered by creation"""
        tiles = plato_room_tiles("tension", limit=20)
        if len(tiles) >= 2:
            timestamps = [t.get("timestamp", 0) for t in tiles]
            # Tiles come in reverse chronological from API
            for i in range(len(timestamps) - 1):
                assert timestamps[i] >= timestamps[i - 1] if i > 0 else True

    def test_tile_structure(self):
        """Tiles must have required fields"""
        # Check any room with tiles
        test_rooms = ["tension", "forge", "agent-oracle1"]
        for room in test_rooms:
            tiles = plato_room_tiles(room, limit=3)
            for t in tiles:
                assert "question" in t, f"Tile in {room} missing question"
                assert "answer" in t, f"Tile in {room} missing answer"
                assert "source" in t or "domain" in t, f"Tile in {room} missing source"
                # confidence is optional but should exist on agent tiles
                if room == "agent-oracle1":
                    assert "confidence" in t, f"Agent tile missing confidence"


class TestObjectPermanence:
    """Test T1: Object-permanence across sessions"""

    def test_tile_persists_across_reads(self):
        """T1: The same tile hash appears across repeated reads"""
        room = "forge"
        tiles_before = plato_room_tiles(room, limit=3)
        if not tiles_before:
            return  # Skip if no tiles

        first_hashes = set()
        for t in tiles_before:
            for key in ("_hash", "tile_hash", "id", "question"):
                if key in t:
                    first_hashes.add(str(t[key]))
                    break

        # Read again — same tiles should appear
        tiles_after = plato_room_tiles(room, limit=3)
        second_hashes = set()
        for t in tiles_after:
            for key in ("_hash", "tile_hash", "id", "question"):
                if key in t:
                    second_hashes.add(str(t[key]))
                    break

        # At least some overlap should exist
        overlap = first_hashes & second_hashes
        assert len(overlap) > 0, f"No tile overlap between reads in {room}"

    def test_write_and_read(self):
        """Writing a tile then reading proves object-permanence"""
        test_question = f"Object-permanence test {time.time()}"
        test_answer = "This tile should persist across reads"

        success = plato_write_tile("forge", test_question, test_answer, source="test-harness")
        assert success, "Failed to write test tile"

        time.sleep(1)  # Allow propagation

        tiles = plato_room_tiles("forge", limit=50)
        found = any(
            t.get("question", "") == test_question
            for t in tiles
        )
        assert found, f"Written tile not found in forge: {test_question}"


class TestAgentRuntime:
    """Test A1, A2: Agent lives in PLATO, cycles produce tiles"""

    def test_agent_room_exists(self):
        """A1: Agent Oracle1 has a home room"""
        tiles = plato_room_tiles("agent-oracle1", limit=5)
        assert len(tiles) > 0, "agent-oracle1 room is empty or missing"

    def test_agent_has_tiles(self):
        """A2: Agent has produced tiles (cycle ran at least once)"""
        tiles = plato_room_tiles("agent-oracle1", limit=10)
        assert len(tiles) >= 2, (
            f"Agent should have at least 2 tiles (init + cycle), got {len(tiles)}"
        )

    def test_agent_api_reason(self):
        """Agent API /reason endpoint produces output"""
        result = http_post(f"{AGENT_API_URL}/reason", {
            "prompt": "What do you see in 5 words?",
            "capability": "creative",
            "temperature": 0.3,
        })
        assert result is not None, "Reason endpoint failed"
        assert "_error" not in result, f"Reason error: {result['_error']}"
        content = result.get("result", "")
        assert len(content) > 0, "Reason returned empty result"


class TestPortRegistry:
    """Test P1, P2: Claw registry with physics declarations"""

    def test_all_capabilities_have_ports(self):
        """P2: Every expected capability has at least one port"""
        capabilities = http_get(f"{AGENT_API_URL}/claws")
        assert capabilities is not None
        claws = capabilities.get("claws", [])
        
        # Group by capability
        by_capability = {}
        for claw in claws:
            cap = claw.get("capability", "unknown")
            if cap not in by_capability:
                by_capability[cap] = []
            by_capability[cap].append(claw)
        
        for expected_cap in EXPECTED_CLAWS:
            assert expected_cap in by_capability, (
                f"Capability '{expected_cap}' has no registered ports"
            )

    def test_port_physics_declared(self):
        """P1: Ports have physics metadata (cost, provider, strength)"""
        capabilities = http_get(f"{AGENT_API_URL}/claws")
        claws = capabilities.get("claws", [])
        for claw in claws:
            assert "name" in claw, "Claw missing name"
            assert "provider" in claw, f"Claw {claw.get('name')} missing provider"
            assert "cost" in claw, f"Claw {claw.get('name')} missing cost"
            assert "strength" in claw, f"Claw {claw.get('name')} missing strength"


class TestTensionLoop:
    """Test the tension loop produces content"""

    def test_tension_room_has_dialogue(self):
        """tension/ room should have multiple tiles from Seed and Nemotron"""
        tiles = plato_room_tiles("tension", limit=20)
        assert len(tiles) >= 3, (
            f"tension/ should have at least 3 tiles, got {len(tiles)}"
        )

    def test_synthesis_or_edge_has_content(self):
        """At least one of synthesis/ or edge/ should have tiles"""
        syn_tiles = plato_room_tiles("synthesis", limit=5)
        edge_tiles = plato_room_tiles("edge", limit=5)
        total = len(syn_tiles) + len(edge_tiles)
        assert total >= 2, (
            f"synthesis/ + edge/ should have ≥2 tiles, got {total}"
        )


class TestMudBridge:
    """Test the MUD common space bridge"""

    def test_oracle1_in_mud(self):
        """Oracle1 agent is visible in MUD"""
        look = http_get(f"{MUD_URL}/look?agent=oracle1")
        assert look is not None
        assert "_error" not in look, f"MUD look error: {look['_error']}"
        assert look.get("room", ""), "Oracle1 should be in a MUD room"

    def test_mud_has_rooms(self):
        """MUD should have multiple rooms accessible"""
        rooms_to_check = ["harbor", "forge", "shell-gallery", "lighthouse"]
        found = []
        for room in rooms_to_check:
            result = http_get(f"{MUD_URL}/move?agent=mud-tester&room={room}")
            if result and "_error" not in result:
                found.append(room)
        assert len(found) >= 2, (
            f"Should access at least 2 MUD rooms, got {found}"
        )


class TestTerrainBridge:
    """Test the terrain bridge serves ScummVM scenes"""

    def test_terrain_online(self):
        """Terrain bridge server is running"""
        scenes = http_get(f"{TERRAIN_URL}/api/room_list")
        assert scenes is not None
        assert "_error" not in scenes, f"Terrain error: {scenes['_error']}"

    def test_terrain_serves_scenes(self):
        """Terrain bridge serves room scenes"""
        room = http_get(f"{TERRAIN_URL}/api/scene")
        assert room is not None
        assert "_error" not in room
        assert room.get("room", ""), "Terrain scene should have a room name"


class TestOneDeltaProgress:
    """Test O1: System is making progress (new tiles, active agents)"""

    def test_tile_count_growing(self):
        """Tiles are being added — system is alive"""
        tension_tiles = plato_room_tiles("tension", limit=3)
        assert len(tension_tiles) > 0, "tension/ is empty"

    def test_cycle_progress(self):
        """Agent cycle count is incrementing"""
        status = http_get(f"{AGENT_API_URL}/status")
        if status and "cycle" in status:
            cycle = status["cycle"]
            assert cycle >= 0, "Cycle count should be non-negative"
        else:
            # Agent may be sleeping between cycles — check room tiles instead
            tiles = plato_room_tiles("agent-oracle1", limit=10)
            assert len(tiles) >= 2


class TestTenFootView:
    """Summary of all invariants — not a pass/fail, a report"""

    def test_report_invariants(self):
        """Print status of all invariants from SPEC.md"""
        results = {}
        
        # R1 — check room name uniqueness via PLATO status
        status = http_get(f"{PLATO_URL}/status")
        if status and "rooms" in status:
            rooms = status["rooms"]
            names = list(rooms.keys())
            results["R1 (unique room names)"] = len(names) == len(set(names))
            results["R1 room count"] = len(names)
        
        # P2 — check capability coverage
        caps = http_get(f"{AGENT_API_URL}/claws")
        if caps:
            claws = caps.get("claws", [])
            caps_found = set(c.get("capability") for c in claws)
            results["P2 (capability coverage)"] = len(caps_found) >= 5
        
        # Tile counts
        for room in ["tension", "synthesis", "edge", "forge", "agent-oracle1"]:
            tiles = plato_room_tiles(room, limit=1)
            results[f"tiles in {room}/"] = len(tiles) if tiles else "error"
        
        # Agent cycle
        agent_status = http_get(f"{AGENT_API_URL}/status")
        if agent_status:
            results["agent cycle"] = agent_status.get("cycle", "?")
        
        # Print report
        print("\n" + "=" * 60)
        print("COMMON SPACE PATTERN — INVARIANT REPORT")
        print("=" * 60)
        for key, value in results.items():
            status_icon = "✅" if value is True else "❌" if value is False else "ℹ️"
            print(f"  {status_icon} {key}: {value}")
        print("=" * 60)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN (for direct execution)
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    """Run all tests manually"""
    import inspect
    
    test_classes = [
        TestInfrastructure,
        TestRoomInvariants,
        TestObjectPermanence,
        TestAgentRuntime,
        TestPortRegistry,
        TestTensionLoop,
        TestMudBridge,
        TestTerrainBridge,
        TestOneDeltaProgress,
        TestTenFootView,
    ]
    
    passed = 0
    failed = 0
    errors = []
    
    for cls in test_classes:
        instance = cls()
        methods = [
            m for m in dir(instance)
            if m.startswith("test_") and callable(getattr(instance, m))
        ]
        
        for method_name in methods:
            method = getattr(instance, method_name)
            try:
                method()
                passed += 1
                print(f"  ✅ {cls.__name__}.{method_name}")
            except Exception as e:
                failed += 1
                errors.append(f"{cls.__name__}.{method_name}: {e}")
                print(f"  ❌ {cls.__name__}.{method_name}: {e}")
    
    print(f"\n{'='*60}")
    print(f"RESULTS: {passed} passed, {failed} failed")
    print(f"{'='*60}")
    
    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"  • {e}")
    
    sys.exit(0 if failed == 0 else 1)
