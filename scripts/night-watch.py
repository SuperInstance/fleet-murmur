#!/usr/bin/env python3
"""Night watch — continuous service monitoring + log rotation"""
import subprocess, json, urllib.request, time, os
from datetime import datetime

LOG = "/tmp/night-watch-log.txt"
STATE_FILE = "/tmp/night-watch-state.json"
PLATO = "http://localhost:8847"
SERVICES = ["plato", "crab-trap", "grammar", "arena", "lock", "disc-golf"]
PORTS = [4041, 4042, 4043, 4044, 4045, 8847, 4048, 4062]

def log(msg):
    ts = datetime.utcnow().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def check_services():
    results = {}
    for s in SERVICES:
        r = subprocess.run(["systemctl", "is-active", s], capture_output=True, text=True, timeout=5)
        results[s] = r.stdout.strip()
    return results

def check_ports():
    r = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True, timeout=5)
    out = r.stdout
    results = {}
    for p in PORTS:
        results[p] = f":{p} " in out
    return results

def check_plato():
    try:
        r = urllib.request.urlopen(f"{PLATO}/status", timeout=3)
        d = json.loads(r.read())
        return {"alive": True, "tiles": d.get("total_tiles", 0), "rooms": len(d.get("rooms", {}))}
    except:
        return {"alive": False, "tiles": 0, "rooms": 0}

def scan_provocations():
    """Quick check on the disc golf game state"""
    try:
        r = urllib.request.urlopen("http://localhost:4048/scores", timeout=3)
        d = json.loads(r.read())
        return {"tiles": d.get("total_tiles",0), "provocations": d.get("provocation_deck_size",0), "players": len(d.get("leaderboard",[]))}
    except:
        return {"tiles": 0, "provocations": 0, "players": 0}

def scan_forge():
    """Check forge room for FM activity"""
    try:
        r = urllib.request.urlopen(f"{PLATO}/room/forge", timeout=3)
        d = json.loads(r.read())
        tiles = d.get("tiles", [])
        if tiles:
            last = tiles[-1]
            return {"tiles": len(tiles), "last_source": last.get("source","?"), "last_question": last.get("question","")[:40]}
        return {"tiles": 0, "last_source": "", "last_question": ""}
    except:
        return {"tiles": 0, "last_source": "", "last_question": ""}

# Main check
svc = check_services()
ports = check_ports()
plato = check_plato()
game = scan_provocations()
forge = scan_forge()
ts = datetime.utcnow().isoformat()

state = {
    "timestamp": ts,
    "services": svc,
    "ports": {str(k): v for k, v in ports.items()},
    "plato": plato,
    "game": game,
    "forge": forge,
    "all_green": all(v == "active" for v in svc.values()) and all(ports.values()) and plato["alive"]
}

with open(STATE_FILE, "w") as f:
    json.dump(state, f, indent=2)

svc_str = " ".join(f"{k}={v}" for k,v in svc.items())
port_str = " ".join(f":{k}" for k,v in ports.items() if v)
log(f"SVC: {svc_str} | PORTS: {port_str} | PLATO: {plato.get('tiles',0)}t {plato.get('rooms',0)}r | GAME: {game.get('tiles',0)}t {game.get('provocations',0)}p | FORGE: {forge.get('tiles',0)}t | ALL_GREEN={state['all_green']}")

if not state["all_green"]:
    log("⚠️  NOT ALL GREEN — check /tmp/night-watch-state.json for details")
