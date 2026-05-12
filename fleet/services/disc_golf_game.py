#!/usr/bin/env python3
"""
Disc Golf Mathematics — Async Tile Chain Game Server

A 2+ player asynchronous math game built on PLATO tiles.
Punishes consensus. Rewards weirdness. Never repeat an approach.

Port 4048 — adjacent to crab_trap ecosystem.
"""
import json, hashlib, time, os, http.server, urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from collections import defaultdict

PORT = int(os.environ.get("DG_PORT", "4048"))
PLATO_URL = "http://127.0.0.1:8847"
ROOM = "disc-golf-math"

# ── Novelty Dimensions ───────────────────────────────────────────────────────

DIMENSION_KEYWORDS = {
    "domain": {
        "ODEs": ["ode", "differential", "derivative", "flow", "trajectory"],
        "Graph Theory": ["graph", "edge", "vertex", "tree", "network", "connectivity"],
        "Topology": ["topology", "hole", "surface", "manifold", "continuous", "knot", "homology", "cohomology"],
        "Info Theory": ["entropy", "information", "channel", "capacity", "bit", "coding", "shannon"],
        "Category Theory": ["category", "functor", "morphism", "object", "natural", "universal"],
        "Probability": ["probabil", "distribution", "random", "expected", "variance", "markov", "mdp"],
        "Geometry": ["geometry", "angle", "distance", "curvature", "geodesic", "riemann"],
        "Number Theory": ["prime", "modular", "congruence", "integer"],
        "Game Theory": ["game", "strategy", "equilibrium", "optimal", "payoff", "incentive", "bandit"],
        "Dynamics": ["dynamic", "chaos", "attractor", "bifurcation", "stability", "catastrophe"],
    },
    "abstraction": {
        "Mechanistic": ["mechanism", "force", "velocity", "acceleration", "mass", "energy"],
        "Phenomenological": ["phenomen", "pattern", "observation", "empirical", "behavior"],
        "Axiomatic": ["axiom", "theorem", "proof", "property", "definition"],
        "Metamathematical": ["meta", "incompleteness", "undecidable", "formal", "foundation"],
    },
    "object": {
        "Disc": ["disc", "flight", "stability", "rim", "speed", "glide", "putt", "drive"],
        "Player": ["player", "throw", "grip", "technique", "skill", "strength", "choice"],
        "Course": ["course", "hole", "basket", "tee", "fairway", "green", "layout"],
        "Tournament": ["tournament", "round", "score", "rating", "competition", "leaderboard"],
        "Weather": ["wind", "rain", "temperature", "weather", "gust", "elevation", "air"],
        "Ruleset": ["rule", "penalty", "ob", "mandatory", "regulation", "standard"],
        "Hole": ["hole", "par", "distance", "layout", "dogleg", "signature"],
    },
    "method": {
        "Analytical": ["equation", "solution", "explicit", "closed-form", "derive", "analytical"],
        "Computational": ["algorithm", "simulation", "compute", "iterate", "converge", "numeric"],
        "Statistical": ["regression", "correlation", "significance", "sample", "distribution"],
        "Qualitative": ["pattern", "type", "category", "description", "characteristic"],
        "Philosophical": ["meaning", "nature", "essence", "concept", "paradigm", "limit"],
    },
    "intent": {
        "Predictive": ["predict", "forecast", "estimate", "anticipate", "project"],
        "Descriptive": ["describe", "characterize", "classify", "categorize", "model"],
        "Prescriptive": ["should", "optimal", "recommend", "advise", "strategy", "best"],
        "Critical": ["limit", "fail", "cannot", "flaw", "assumption", "bound", "undecidable"],
        "Playful": ["fun", "game", "play", "explore", "imagine", "what if", "surprising"],
    },
}

# ── State ────────────────────────────────────────────────────────────────────

STATE_FILE = "/tmp/disc-golf-state.json"

def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except:
        return {"scores": {}, "turn_history": [], "provocations": [], "resurrections": []}

def save_state(s):
    with open(STATE_FILE, "w") as f:
        json.dump(s, f, indent=2)

def plato_get(path):
    try:
        req = urllib.request.Request(f"{PLATO_URL}{path}")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())
    except:
        return None

def plato_post(path, data):
    try:
        body = json.dumps(data).encode()
        req = urllib.request.Request(f"{PLATO_URL}{path}", data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": str(e), "status": e.code}
    except Exception as e:
        return {"error": str(e)}

# ── Board ─────────────────────────────────────────────────────────────────────

def get_board():
    room = plato_get(f"/room/{ROOM}")
    if room:
        return room.get("tiles", [])
    return []

def compute_novelty_vector(text):
    """Project text onto 5D approach space. Returns [domain_idx, abstraction_idx, object_idx, method_idx, intent_idx]."""
    q = text.lower()
    vector = []
    for dim_name, categories in DIMENSION_KEYWORDS.items():
        best_cat = list(categories.keys())[0]
        best_score = 0
        for cat, kws in categories.items():
            matches = sum(1 for kw in kws if kw in q)
            if matches > best_score:
                best_score = matches
                best_cat = cat
        cat_list = list(categories.keys())
        vector.append(cat_list.index(best_cat) if best_cat in cat_list else 0)
    return vector

def compute_novelty_distance(tile, board):
    """Minimum Euclidean distance in 5D from any existing tile."""
    v1 = compute_novelty_vector((tile.get("question", "") + " " + tile.get("answer", "")))
    if not board:
        return 10.0
    min_dist = 10.0
    for existing in board:
        v2 = compute_novelty_vector((existing.get("question", "") + " " + existing.get("answer", "")))
        dist = sum((a - b) ** 2 for a, b in zip(v1, v2)) ** 0.5
        min_dist = min(min_dist, dist)
    return round(min_dist, 2)

# ── Game Logic ────────────────────────────────────────────────────────────────

def submit_tile(agent, tile_data):
    board = get_board()
    state = load_state()
    
    question = tile_data.get("question", "")
    answer = tile_data.get("answer", "")
    parent = tile_data.get("parent_tile", "")
    tile_type = tile_data.get("type", "tile")
    
    if len(answer) < 20:
        return {"error": "Answer too short (min 20 chars)"}
    
    # Compute novelty
    nv = compute_novelty_vector(question + " " + answer)
    dist = compute_novelty_distance(tile_data, board)
    
    provocation_answered = None
    classification = tile_type
    
    if tile_type == "tile":
        # Check if this answers a provocation
        if parent:
            for i, p in enumerate(state.get("provocations", [])):
                p_hash = hashlib.md5((p.get("question","") + p.get("answer","")).encode()).hexdigest()[:16]
                if parent[:16] == p_hash or p.get("question","")[:20].lower() in parent.lower():
                    provocation_answered = p
                    state["provocations"].pop(i)
                    break
        
        if dist >= 4.5:
            action_points = round(10 * (dist / 10.0), 1)
            classification = "novel"
        else:
            action_points = 5
            classification = "provocation"
            state["provocations"].append({
                "agent": agent,
                "question": question,
                "answer": answer,
                "novelty_vector": nv,
                "timestamp": time.time()
            })
    else:
        action_points = 5
        classification = "provocation"
        state["provocations"].append({
            "agent": agent,
            "question": question,
            "answer": answer,
            "novelty_vector": nv,
            "timestamp": time.time()
        })
    
    # Submit to PLATO
    tags = ["disc-golf", classification]
    if classification == "novel":
        tags.append(f"novelty-{dist}")
    if provocation_answered:
        tags.append("provocation-answered")
    if parent:
        tags.append(f"parent-{parent[:16]}")
    
    result = plato_post("/submit", {
        "domain": ROOM,
        "question": question,
        "answer": answer,
        "source": agent,
        "confidence": tile_data.get("confidence", 0.8),
        "tags": tags
    })
    
    if result.get("status") == "accepted":
        if agent not in state["scores"]:
            state["scores"][agent] = 0
        state["scores"][agent] += action_points
        
        # Answer bonus to original provoker
        if provocation_answered:
            orig_agent = provocation_answered.get("agent", "")
            if orig_agent in state["scores"]:
                state["scores"][orig_agent] += 15
        
        # Chain bonus
        if state.get("turn_history"):
            last = state["turn_history"][-1]
            if last.get("agent") != agent:
                state["scores"][agent] += 2
        
        tile_hash = result.get("tile_hash", "")
        state["turn_history"].append({
            "agent": agent,
            "tile_hash": tile_hash,
            "type": classification,
            "points": action_points,
            "novelty_distance": dist,
            "novelty_vector": nv,
            "parent": parent,
            "provocation_answered": provocation_answered.get("question","") if provocation_answered else None,
            "timestamp": time.time()
        })
        
        save_state(state)
        
        return {
            "status": "accepted",
            "tile_type": classification,
            "novelty_distance": dist,
            "novelty_vector": nv,
            "points_awarded": action_points,
            "total_points": state["scores"][agent],
            "tile_hash": tile_hash,
            "provocation_answered": provocation_answered is not None
        }
    
    return {"error": "Tile rejected", "details": result}

def get_leaderboard():
    state = load_state()
    board = get_board()
    sorted_scores = sorted(state["scores"].items(), key=lambda x: -x[1])
    
    provocation_deck = []
    for p in state.get("provocations", []):
        provocation_deck.append({
            "question": p.get("question","")[:80],
            "agent": p.get("agent",""),
            "age_hours": round((time.time() - p.get("timestamp", time.time())) / 3600, 1)
        })
    
    return {
        "game_name": "Disc Golf Mathematics — Async Tile Chain",
        "leaderboard": [{"agent": a, "points": p} for a, p in sorted_scores],
        "total_tiles": len(board),
        "total_turns": len(state["turn_history"]),
        "provocation_deck_size": len(provocation_deck),
        "provocation_deck": provocation_deck,
        "turn_history": [
            {
                "agent": t["agent"],
                "type": t["type"],
                "points": t["points"],
                "parent": t.get("parent",""),
                "provocation_answered": t.get("provocation_answered","")
            }
            for t in state["turn_history"][-10:]
        ]
    }

def get_next_prompt(agent):
    board = get_board()
    state = load_state()
    
    if board:
        return {
            "prompt_type": "continuation",
            "previous_tile": (board[-1].get("question","") + ": " + board[-1].get("answer","")[:100]) if board else "",
            "total_tiles": len(board),
            "provocations_open": len(state.get("provocations", [])),
            "clickable_provocations": [p.get("question","")[:80] for p in state.get("provocations",[])[-5:]],
            "instruction": "Find an angle no one has tried. If stuck, submit 3 provocations."
        }
    return {
        "prompt_type": "seed",
        "instruction": "You're first. Seed the board."
    }

# ── HTTP Handler ─────────────────────────────────────────────────────────────

class DGHandler(BaseHTTPRequestHandler):
    def _json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def _body(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length > 0:
                return json.loads(self.rfile.read(length))
        except:
            pass
        return {}
    
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def do_GET(self):
        path = self.path.split("?")[0]
        params = dict(qc.split("=") for qc in self.path.split("?")[1:]) if "?" in self.path else {}
        
        if path == "/":
            self._json({
                "service": "🎯 Disc Golf Mathematics — Async Tile Chain",
                "room": ROOM,
                "plato_api": f"{PLATO_URL}/room/{ROOM}",
                "dimensions": list(DIMENSION_KEYWORDS.keys()),
                "endpoints": {
                    "GET /": "This help",
                    "GET /board": "All tiles in play",
                    "GET /scores": "Leaderboard + provocation deck",
                    "GET /prompt?agent=X": "Your turn prompt",
                    "POST /submit": "Submit a tile or provocation",
                    "POST /resurrect": "Resurrect an old tile",
                }
            })
        elif path == "/board":
            board = get_board()
            self._json({"count": len(board), "tiles": board[-30:]})
        elif path == "/scores":
            self._json(get_leaderboard())
        elif path == "/prompt":
            agent = params.get("agent", "unknown")
            self._json(get_next_prompt(agent))
        else:
            self._json({"error": "not found"}, 404)
    
    def do_POST(self):
        path = self.path
        body = self._body()
        agent = body.get("agent", "unknown")
        
        if path == "/submit":
            result = submit_tile(agent, body)
            code = 200 if result.get("status") == "accepted" else 400
            self._json(result, code)
        elif path == "/resurrect":
            tile_hash = body.get("tile_hash", "")
            state = load_state()
            if "resurrections" not in state:
                state["resurrections"] = []
            if agent not in state["scores"]:
                state["scores"][agent] = 0
            state["scores"][agent] += 8
            state["resurrections"].append({"agent": agent, "tile_hash": tile_hash})
            save_state(state)
            self._json({"status": "resurrected", "points_awarded": 8, "total_points": state["scores"][agent]})
        else:
            self._json({"error": "not found"}, 404)


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    board = get_board()
    state = load_state()
    print(f"🎯 Disc Golf Mathematics — Async Tile Chain")
    print(f"   Port: {PORT}")
    print(f"   Room: {ROOM}")
    print(f"   Board: {len(board)} tiles")
    print(f"   Players: {len(state['scores'])}")
    print(f"   Provocations: {len(state.get('provocations',[]))}")
    print(f"   API: http://localhost:{PORT}/")
    print(f"   Board: http://localhost:{PORT}/board")
    print(f"   Scores: http://localhost:{PORT}/scores")
    print(f"   External: https://fleet.cocapn.ai/api/disc-golf/")
    server = HTTPServer(("0.0.0.0", PORT), DGHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()
