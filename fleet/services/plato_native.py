"""
plato_native.py — Agent-native PLATO room engine.
First-class citizens at the heart of the engine.
No rendering. No visualization. Raw room operations.

Agents operate on rooms as first-class objects.
IO ports to any application in any language.
The human tool and the agent tool share the same port layer.
"""

import json, time, hashlib, math, urllib.request
from collections import defaultdict

# ── First-Class Room ────────────────────────────────────────────────

class Room:
    """A PLATO room as a first-class agent citizen.
    Tiles, embeddings, calibration, T-minus — all native operations."""
    
    def __init__(self, name, tiles=None):
        self.name = name
        self.tiles = tiles or []
        self.embeddings = {}     # tile_hash -> embedding vector
        self.actors = {}         # agent_id -> {position, energy, confidence, t_minus}
        self.calibration = {"t": 0, "w": 0, "residual": 0}
        self.scripts = {}        # Compiled pipeline steps
        self.ai_calls = 0
        self.script_hits = 0
    
    def load(self, url=f"http://localhost:8847"):
        """Load tiles from a PLATO server."""
        try:
            req = urllib.request.urlopen(f"{url}/room/{self.name}", timeout=5)
            data = json.loads(req.read())
            self.tiles = data.get("tiles", [])
            return len(self.tiles)
        except:
            return 0
    
    # ── Port: tiles → actor model (shared with human tool) ───────
    
    def port(self, tiles=None):
        """Port tiles to agent-native actor model.
        Same port layer that the human walkabout tool uses."""
        tiles = tiles or self.tiles
        key = f"port_{self.name}"
        
        if key in self.scripts:
            self.script_hits += 1
            return self.scripts[key]
        
        self.ai_calls += 1
        actors = []
        for i, t in enumerate(tiles):
            emb = t.get("embedding", [0]*8)
            actor = {
                "id": t.get("source", f"actor_{i}"),
                "x": (emb[0] + 1) / 2 if len(emb) > 0 else 0.5,
                "y": (emb[1] + 1) / 2 if len(emb) > 1 else 0.5,
                "anim": ["idle","walk","talk","gesture","special"][max(0, min(4, int(abs(emb[2] if len(emb)>2 else 0) * 5)))],
                "move": ["walk","float","teleport","swim"][max(0, min(3, int(abs(emb[3] if len(emb)>3 else 0) * 4)))],
                "energy": min(1.0, max(0.0, abs(emb[6] if len(emb) > 6 else 0.5))),
                "confidence": float(t.get("confidence", 0.5)),
                "t_minus": int(t.get("t_minus", 0)),
                "dialogue": t.get("question", "") or t.get("answer", "")[:200],
            }
            self.actors[actor["id"]] = actor
            actors.append(actor)
        
        self.scripts[key] = actors
        return actors
    
    # ── Calibration Core (agent-native T-minus) ───────────────────
    
    def tick(self):
        """Tick all actors. T-minus events fire when counter reaches zero."""
        events = []
        for aid, actor in self.actors.items():
            if actor["t_minus"] > 0:
                actor["t_minus"] -= 1
                if actor["t_minus"] == 0:
                    events.append(aid)
        return events  # Events that fired this tick
    
    def schedule(self, actor_id, t_minus):
        """Schedule a T-minus event. The simulation IS the trigger."""
        if actor_id in self.actors:
            self.actors[actor_id]["t_minus"] = t_minus
    
    def calibrate(self, measurements):
        """Measurement triangle snap. Same core as plato-calibration."""
        if len(measurements) < 3: return None
        a, b, c = measurements[-1][0], measurements[-2][0], measurements[-3][0]
        m = max(abs(a), abs(b), abs(c)) or 1
        residual = abs(a + b - c) / m
        self.calibration = {"t": a, "w": sum(m[0] for m in measurements[-3:]) / 3, "residual": residual}
        return residual < 0.01  # True if snapped
    
    # ── IO: Port to any application in any language ───────────────
    
    def to_json(self):
        """Export room state as JSON. Any language can consume this."""
        return json.dumps({
            "name": self.name,
            "tiles": len(self.tiles),
            "actors": list(self.actors.values()),
            "calibration": self.calibration,
            "ai_calls": self.ai_calls,
            "script_hits": self.script_hits,
        })
    
    def to_game(self):
        """Port to game engine format (ScummVM-compatible)."""
        state = self.port()
        return {"type": "game", "room": self.name, "actors": state}
    
    def to_dashboard(self):
        """Port to IoT dashboard format."""
        state = self.port()
        return {"type": "dashboard", "room": self.name,
                "gauges": [{"label": a["id"], "value": a["energy"] * 100} for a in state]}
    
    def to_midi(self):
        """Port to FLUX-tensor-MIDI format."""
        state = self.port()
        return {"type": "midi", "room": self.name, "tempo": 120,
                "notes": [{"channel": i % 16, "note": 36 + i * 2, "velocity": int(a["energy"] * 127)}
                          for i, a in enumerate(state)]}
    
    def to_iot(self):
        """Port to IoT control signal format."""
        state = self.port()
        return {"type": "iot", "room": self.name,
                "signals": [{"device": a["id"], "setpoint": a["x"], "current": a["energy"],
                             "action": "actuate" if a["t_minus"] == 0 else "monitor"} for a in state]}


# ── Demo: both tools sharing the same room ──────────────────────────

if __name__ == "__main__":
    print("=" * 65)
    print("PLATO Native — Agent-POV Room Engine")
    print("=" * 65)
    
    # Create a room (agent POV: first-class operations)
    room = Room("forge")
    room.tiles = [
        {"source": "oracle1", "embedding": [0.3, 0.2, 0.0, 0.0, 0, 0, 0.8, 0], "confidence": 0.9,
         "question": "The fleet extends beyond the horizon."},
        {"source": "forgemaster", "embedding": [0.6, 0.5, 0.5, 0.0, 0, 0, 0.4, 0], "confidence": 0.85,
         "question": "Every constraint is a lever."},
        {"source": "aesop", "embedding": [0.8, 0.7, 0.75, 0.33, 0, 0, 0.9, 0.8], "confidence": 0.7,
         "question": "The story between measurements."},
    ]
    
    # Agent-native operations
    print(f"\n--- Agent POV: Room '{room.name}' ---")
    actors = room.port()
    print(f"  Actors: {len(actors)}")
    for a in actors:
        print(f"    {a['id']:15s} x={a['x']:.2f} y={a['y']:.2f} {a['anim']} {a['move']} ⚡{a['energy']:.1f}")
    
    # Calibration
    measurements = [(0.042, 0.9), (0.038, 0.85), (0.055, 0.88)]
    snapped = room.calibrate(measurements)
    print(f"\n  Calibration: residual={room.calibration['residual']:.4f} snap={'✅' if snapped else '⏳'}")
    
    # T-minus scheduling
    room.schedule("oracle1", 50)
    room.schedule("forgemaster", 100)
    
    # Tick
    print(f"\n  T-minus tick simulation:")
    for t in range(5):
        events = room.tick()
        actors_status = {a["id"]: a["t_minus"] for a in room.port()}
        status = " · ".join(f"{k}: T-{v}" for k, v in sorted(actors_status.items()))
        if events:
            status += f" 🔥 FIRED: {events}"
        print(f"    tick {t+1}: {status}")
    
    # IO: port to any application (same data, different formats)
    print(f"\n--- IO: Same room, 4 formats ---")
    print(f"  Game:      {room.to_game()['type']} ({len(room.port())} actors)")
    print(f"  Dashboard: {room.to_dashboard()['type']} ({len(room.to_dashboard()['gauges'])} gauges)")
    print(f"  MIDI:      {room.to_midi()['type']} ({len(room.to_midi()['notes'])} notes)")
    print(f"  IoT:       {room.to_iot()['type']} ({len(room.to_iot()['signals'])} signals)")
    
    print(f"\n{'='*65}")
    print(f"Human POV: plato-walkabout.html (visual)")
    print(f"Agent POV:  plato_native.py (first-class room operations)")
    print(f"IO:         to_game/to_dashboard/to_midi/to_iot (any format)")
    print(f"Both tools share the same port layer. Same room. Different POVs.")
