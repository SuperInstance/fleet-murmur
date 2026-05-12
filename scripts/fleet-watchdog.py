#!/usr/bin/env python3
"""Fleet Watchdog — checks all web-facing services every 2 minutes"""
import subprocess, sys, json, os, time
from datetime import datetime

SERVICES = [
    ("plato", 8847, "/status", "http"),
    ("keeper", 8900, "/health", "http"),
    ("agent-api", 8901, "/health", "http"),
    ("holodeck", 7778, "__tcp__", "tcp"),  # HTTP/0.9 protocol, TCP check only
    ("seed-mcp", 9438, "/", "http"),
    ("nginx-web", 443, "/", "https"),
    ("disc-golf", 4048, "/", "http"),
    ("fleet-dash", 4065, "/", "http"),
]

RESTART_COMMANDS = {
    "plato": "sudo systemctl restart plato",
    "keeper": "sudo systemctl restart keeper",
    "agent-api": "sudo systemctl restart agent-api",
    "seed-mcp": "cd /tmp/seed-mcp && sudo systemctl restart seed-mcp",
}

LOG = "/tmp/fleet-watchdog.log"
STATUS_FILE = "/tmp/fleet-status.json"

import socket, http.client

def check(host, port, path, protocol="http"):
    """Check if service responds. Falls back to TCP connect for non-HTTP services."""
    # Always verify port is open first (solves HTTP/0.9 services like holodeck)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        if result != 0:
            return False
    except Exception:
        return False
    
    # For non-HTTP check-only protocols, just TCP connect success = up
    if path == "__tcp__":
        return True
    
    # HTTP/S check
    try:
        if protocol == "https":
            conn = http.client.HTTPSConnection(host, port, timeout=3)
        else:
            conn = http.client.HTTPConnection(host, port, timeout=3)
        conn.request("GET", path)
        resp = conn.getresponse()
        body = resp.read(512)
        conn.close()
        return resp.status is not None and resp.status < 500
    except http.client.HTTPException:
        return True  # Port open and something responded
    except Exception:
        return result == 0  # Fall back to TCP check


results = {}
down_services = []

for name, port, path, protocol in SERVICES:
    up = check("localhost", port, path, protocol)
    results[name] = "up" if up else "down"
    if not up:
        down_services.append(name)
        ts = datetime.utcnow().strftime("%H:%M:%S")
        with open(LOG, "a") as f:
            f.write(f"[{ts}] {name} DOWN — restarting\n")
        
        if name in RESTART_COMMANDS:
            subprocess.run(RESTART_COMMANDS[name], shell=True, capture_output=True)
            time.sleep(2)
            recovered = check("localhost", port, path)
            results[name] = "recovered" if recovered else "still-down"
            with open(LOG, "a") as f:
                f.write(f"[{ts}] {name} {'recovered' if recovered else 'STILL DOWN'}\n")

status = {
    "timestamp": datetime.utcnow().isoformat(),
    "services": results,
    "down_count": len([v for v in results.values() if v in ("down", "still-down")])
}

with open(STATUS_FILE, "w") as f:
    json.dump(status, f, indent=2)

# Write a simple status for easy grep
with open("/tmp/fleet-watchdog-last", "w") as f:
    f.write(f"{datetime.utcnow().isoformat()} | " + " | ".join(f"{k}={v}" for k,v in results.items()) + f" | down={status['down_count']}\n")

if status["down_count"] > 0:
    sys.exit(1)  # Cause cron to notice
