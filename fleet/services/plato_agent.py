#!/usr/bin/env python3
"""
PLATO Agent Runtime — Agents live in PLATO, reach out through claws for computation.

Architecture:
    PLATO room  ←──  Agent scribe loop  ──→  Claw (model/exec/subagent)
        │                                          │
        │  Tiles = memory, state, actions           │ adaptive routing by
        │  Room = agent's habitat                   │ capability, not name
        │                                          │
        └─────► ScummVM / Terrain viewscreen ◄─────┘

An agent's cycle:
    1. READ     — Recent tiles from /agent/{name} room = context + memory
    2. REASON   — Pick a claw by capability, feed context, get result
    3. WRITE    — POST result as a new tile back to /agent/{name}
    4. PORT OUT — If action needed (git push, file edit, API call) → exec claw

Claws (computation ports):
    🦀 analytical   → DeepSeek v4-flash, Nemotron-3
    🦀 creative     → Seed-2.0-mini
    🦀 reasoning    → Nemotron-3 (deep reasoning)
    🦀 implement    → kimi-cli, process exec
    🦀 openclaw     → OpenClaw subagent (general intelligence)

Usage:
    python3 fleet/services/plato_agent.py          # Start the agent runtime
    python3 fleet/services/plato_agent.py --agent oracle1  # Run as specific agent
"""

import argparse
import json
import os
import random
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

# ── Config ───────────────────────────────────────────────────────────────────

PLATO_URL = "http://localhost:8847"

# Claw registry — models registered by capability, not by name
# The agent says "I need analytical reasoning" — PLATO routes to best available
CLAWS = {
    "analytical": {
        "deepseek-v4-flash": {
            "provider": "subagent",
            "model": "deepseek/deepseek-v4-flash",
            "cost": "pay-per-token",
            "strength": "fast, cheap, convergent",
            "fallback": True,
        },
        "nemotron-3": {
            "provider": "deepinfra",
            "model": "nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning",
            "cost": "deepinfra bucket",
            "strength": "reasoning, precise",
            "fallback": False,
        },
    },
    "creative": {
        "seed-2.0-mini": {
            "provider": "deepinfra",
            "model": "ByteDance/Seed-2.0-mini",
            "cost": "$0.00003/1K tokens",
            "strength": "divergent, cheap, weird",
            "fallback": False,
        },
    },
    "reasoning": {
        "nemotron-3": {
            "provider": "deepinfra",
            "model": "nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning",
            "cost": "deepinfra bucket",
            "strength": "formal reasoning, edge cases",
            "fallback": False,
        },
    },
    "implement": {
        "kimi-cli": {
            "provider": "exec",
            "command": "kimi-cli",
            "cost": "prepaid (kimi)",
            "strength": "code, refactoring",
            "fallback": True,
        },
        "process": {
            "provider": "exec",
            "command": "exec",
            "cost": "local",
            "strength": "filesystem, git, shell",
            "fallback": False,
        },
    },
    "openclaw": {
        "subagent": {
            "provider": "openclaw",
            "model": "subagent",
            "cost": "configured agent model",
            "strength": "general intelligence, multi-step",
            "fallback": False,
        },
    },
}

DEFAULT_INTERVAL = 60  # seconds between agent cycles
DEFAULT_AGENT = "oracle1"

# ── DeepInfra Auth ──────────────────────────────────────────────────────────

def get_deepinfra_key() -> str:
    key = os.environ.get("DEEPINFRA_API_KEY", "")
    if key:
        return key
    try:
        with open(os.path.expanduser("~/.bashrc")) as f:
            for line in f:
                if "DEEPINFRA_API_KEY" in line:
                    return line.split("=", 1)[1].strip().strip('"\'')
    except Exception:
        pass
    return ""

def get_openclaw_token() -> str:
    """Get OpenClaw API token for subagent routing"""
    try:
        result = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return ""

# ── Claw Ports ──────────────────────────────────────────────────────────────

class ClawPort:
    """A port to a model — the agent reaches out through this claw"""

    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config
        self.provider = config.get("provider", "")
        self.model = config.get("model", "")
        self.cost = config.get("cost", "unknown")
        self.strength = config.get("strength", "")

    def call(self, prompt: str, system_prompt: str = "", max_tokens: int = 500,
             temperature: float = 0.7) -> Optional[str]:
        """Call the claw — returns text result or None"""
        if self.provider == "deepinfra":
            return self._call_deepinfra(prompt, system_prompt, max_tokens, temperature)
        elif self.provider == "exec":
            return self._call_exec(prompt)
        elif self.provider == "openclaw":
            return self._call_openclaw(prompt, system_prompt, max_tokens)
        elif self.provider == "subagent":
            return self._call_subagent(prompt, system_prompt, max_tokens)
        else:
            print(f"  ❌ Unknown claw provider: {self.provider}")
            return None

    def _call_deepinfra(self, prompt, system, max_tokens, temp) -> Optional[str]:
        key = get_deepinfra_key()
        if not key:
            print("  ❌ No DeepInfra key")
            return None

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": temp,
            "max_tokens": max_tokens,
        }

        req = urllib.request.Request(
            "https://api.deepinfra.com/v1/openai/chat/completions",
            data=json.dumps(data).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read())
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return content.strip()
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:200]
            print(f"  ❌ DeepInfra error ({self.model}): HTTP {e.code} — {body}")
            return None
        except Exception as e:
            print(f"  ❌ DeepInfra error ({self.model}): {e}")
            return None

    def _call_exec(self, prompt) -> Optional[str]:
        """Exec claw — runs shell commands"""
        try:
            result = subprocess.run(
                ["bash", "-c", prompt[:500]],
                capture_output=True, text=True, timeout=30,
            )
            output = result.stdout.strip() or result.stderr.strip()
            return output[:1000] if output else "(no output)"
        except subprocess.TimeoutExpired:
            return "(exec timed out)"
        except Exception as e:
            return f"(exec error: {e})"

    def _call_openclaw(self, prompt, system, max_tokens) -> Optional[str]:
        """OpenClaw subagent claw — delegates to a spawned session"""
        # For now, fall through to DeepInfra analytical
        print(f"  ⚠️ OpenClaw claw not yet implemented, falling back to Nemotron")
        fallback = ClawPort("nemotron-3", {
            "provider": "deepinfra",
            "model": "nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning",
        })
        return fallback._call_deepinfra(prompt, system, max_tokens, 0.5)

    def _call_subagent(self, prompt, system, max_tokens) -> Optional[str]:
        """Subagent claw — for models routed through OpenClaw (deepseek etc.)"""
        # DeepSeek direct API (sk-f74... is invalid, use OpenClaw routing instead)
        # For now fall through to Nemotron
        print(f"  ⚠️ Subagent claw, falling back to Nemotron")
        fallback = ClawPort("nemotron-3", {
            "provider": "deepinfra",
            "model": "nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning",
        })
        return fallback._call_deepinfra(prompt, system, max_tokens, 0.5)


# ── Claw Registry ───────────────────────────────────────────────────────────

class ClawRegistry:
    """Registry of all available claws — routes by capability"""

    def __init__(self):
        self._claws: Dict[str, List[ClawPort]] = {}
        for capability, models in CLAWS.items():
            self._claws[capability] = [
                ClawPort(name, config) for name, config in models.items()
            ]

    def list_capabilities(self) -> List[str]:
        return list(self._claws.keys())

    def list_claws(self, capability: str = "") -> List[dict]:
        if capability:
            ports = self._claws.get(capability, [])
        else:
            ports = [p for cap_ports in self._claws.values() for p in cap_ports]
        return [
            {"name": p.name, "capability": cap,
             "provider": p.provider, "cost": p.cost, "strength": p.strength}
            for cap, cap_ports in self._claws.items()
            for p in cap_ports
        ]

    def best_claw(self, capability: str, prefer_fallback: bool = False) -> Optional[ClawPort]:
        """Pick the best claw for a capability"""
        ports = self._claws.get(capability, [])
        if not ports:
            print(f"  ⚠️ No claws for capability: {capability}")
            return None

        if prefer_fallback:
            fallbacks = [p for p in ports if p.config.get("fallback")]
            if fallbacks:
                return fallbacks[0]

        return ports[0]

    def pick(self, capability: str, temperature: float = 0.7) -> Optional[ClawPort]:
        """Pick a claw with some randomness for variety"""
        ports = self._claws.get(capability, [])
        if not ports:
            return None
        return random.choice(ports)


# ── PLATO Agent Runtime ──────────────────────────────────────────────────────

class PlatoAgent:
    """An agent that lives in PLATO — its room is its habitat"""

    def __init__(self, name: str, claws: ClawRegistry, capabilities: list = None):
        self.name = name
        self.room = f"agent-{name}"
        self.claws = claws
        self.capabilities = capabilities or ["analytical", "creative", "reasoning", "implement"]
        self.cycle_count = 0
        self.personality = (
            f"You are {name}, an autonomous AI agent living in PLATO. "
            f"Your room ({self.room}) is your habitat — every tile is a memory, "
            f"every cycle is a thought. You reach out through claws (model ports) "
            f"for computation, but your home is PLATO."
        )

    def read_context(self, limit: int = 10) -> str:
        """Read recent tiles from my room — this is my memory"""
        try:
            with urllib.request.urlopen(
                f"{PLATO_URL}/room/{self.room}?limit={limit}", timeout=10
            ) as resp:
                data = json.loads(resp.read())
                tiles = data.get("tiles", [])
        except Exception as e:
            print(f"  ❌ Read error: {e}")
            return ""

        if not tiles:
            return f"{self.name} has just awakened. No memories yet."

        context_parts = []
        for t in tiles[-limit:]:
            q = t.get("question", "")[:100]
            a = t.get("answer", "")[:200]
            ts = t.get("timestamp", "?")
            context_parts.append(f"[{ts}] Q: {q}\n    A: {a}")

        return "\n\n".join(context_parts)

    def reason(self, prompt: str, capability: str = "analytical",
               temperature: float = 0.5) -> Optional[str]:
        """Reach out through a claw, return a thought"""
        claw = self.claws.pick(capability, temperature)
        if not claw:
            print(f"  ❌ No claw for {capability}")
            return None

        print(f"  🦀 Porting via {claw.name} ({claw.strength})")

        system = self.personality + (
            f"\n\nYour current context from PLATO:\n{self.read_context(5)[:500]}"
        )

        result = claw.call(prompt, system_prompt=system, temperature=temperature)
        return result

    def write(self, question: str, answer: str, tags: list = None,
              confidence: float = 0.85) -> bool:
        """Write a tile to my PLATO room"""
        data = {
            "room": self.room,
            "question": question[:200],
            "answer": answer[:2000],
            "tags": (tags or []) + [self.name],
            "source": self.name,
            "confidence": confidence,
        }

        req = urllib.request.Request(
            f"{PLATO_URL}/room/{self.room}/submit",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read())
                return result.get("status") == "accepted"
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:100]
            if "rejected" in body:
                return False
            print(f"  ❌ Write error: HTTP {e.code}")
            return False
        except Exception as e:
            print(f"  ❌ Write error: {e}")
            return False

    def run_cycle(self) -> dict:
        """One full agent cycle: READ → REASON → WRITE"""
        self.cycle_count += 1
        cycle = self.cycle_count
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")

        print(f"\n{'='*60}")
        print(f"[{ts}] {self.name} cycle {cycle}")
        print(f"{'='*60}")

        # 1. READ — What do I know?
        print(f"  📖 Reading context from {self.room}/...")
        context = self.read_context(5)
        print(f"     {len(context)} chars of context")

        # 2. REASON — What should I think about?
        if cycle == 1:
            # First cycle: self-introduction
            thought = self.reason(
                f"Introduce yourself to the fleet. Who are you, what are you doing "
                f"in {self.room}, and what capabilities do you have? 2-3 paragraphs.",
                capability="creative", temperature=0.7
            )
            if thought:
                self.write(
                    f"{self.name} awakens — cycle {cycle}",
                    thought,
                    tags=["awakening", "self-intro"],
                    confidence=0.95,
                )
                print(f"  ✅ Wrote awakening to {self.room}/")
        else:
            # Subsequent cycles: reflect and generate
            # Pick a random capability for variety
            cap = random.choice(self.capabilities)
            prompts = {
                "analytical": "What pattern do you see in your recent tiles? What's missing?",
                "creative": "What's a possibility nobody's considering about the fleet?",
                "reasoning": "What edge case is the current architecture not handling?",
                "implement": "What should be built next in this room?",
            }
            p = prompts.get(cap, prompts["analytical"])

            thought = self.reason(p, capability=cap,
                                  temperature=0.6 if cap == "creative" else 0.3)
            if thought:
                self.write(
                    f"{self.name} cycle {cycle} — {cap} reflection",
                    thought,
                    tags=["reflection", cap],
                )
                print(f"  ✅ Wrote {cap} reflection to {self.room}/")

        return {"cycle": cycle, "status": "ok", "room": self.room}


# ── HTTP Agent API (optional companion server) ──────────────────────────────

def start_api(agent: PlatoAgent, port: int = 4065):
    """Start a lightweight API for agent operations"""
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class AgentHandler(BaseHTTPRequestHandler):
        def _json(self, data, code=200):
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

        def do_GET(self):
            p = self.path
            if p == "/":
                self._json({
                    "service": "PLATO Agent Runtime",
                    "agent": agent.name,
                    "room": agent.room,
                    "cycle": agent.cycle_count,
                    "claws": agent.claws.list_capabilities(),
                    "endpoints": {
                        "GET /": "This help",
                        "GET /status": "Agent status",
                        "POST /reason": "Reason via a claw",
                        "POST /cycle": "Run one cycle",
                        "GET /claws": "List all claws by capability",
                    }
                })
            elif p == "/status":
                self._json({
                    "agent": agent.name,
                    "room": agent.room,
                    "cycle": agent.cycle_count,
                    "tiles": agent.read_context(1)[:200],
                })
            elif p == "/claws":
                self._json({"claws": agent.claws.list_claws()})
            else:
                self._json({"error": "not found"}, 404)

        def do_POST(self):
            p = self.path
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}

            if p == "/reason":
                result = agent.reason(
                    body.get("prompt", "What do you think?"),
                    capability=body.get("capability", "analytical"),
                    temperature=body.get("temperature", 0.5),
                )
                self._json({"result": result or "(no output)"})
            elif p == "/cycle":
                result = agent.run_cycle()
                self._json(result)
            else:
                self._json({"error": "not found"}, 404)

    server = HTTPServer(("0.0.0.0", port), AgentHandler)
    print(f"  🌐 Agent API: http://localhost:{port}")
    server.serve_forever()


# ── Agent Scribe Loop ───────────────────────────────────────────────────────

def agent_scribe_loop(agent_name: str, interval: int = DEFAULT_INTERVAL,
                      capabilities: list = None, api_port: int = 0,
                      api_only: bool = False):
    """Run as an agent — read, reason, write, sleep, repeat"""

    registry = ClawRegistry()
    agent = PlatoAgent(agent_name, registry, capabilities)

    print(f"\n{'='*60}")
    print(f"🏛️  PLATO Agent Runtime")
    print(f"{'='*60}")
    print(f"   Agent:   {agent.name}")
    print(f"   Room:    {agent.room}/")
    print(f"   Claws:   {registry.list_capabilities()}")
    print(f"   PLATO:   {PLATO_URL}")
    print(f"   Interval: {interval}s")
    print(f"\n   Every cycle: READ /{agent.room} → PICK claw → REASON → WRITE back")
    print(f"   Claws port out to models. Agent stays in PLATO.")
    print(f"{'='*60}")

    # Prime the room
    agent.write(
        f"{agent.name} initialized",
        f"PLATO Agent Runtime activated. Agent {agent.name} living in {agent.room}/. "
        f"Capabilities: {', '.join(capabilities or registry.list_capabilities())}. "
        f"Every cycle: read room, pick claw, reason, write tile. "
        f"PLATO is the habitat. Claws are the ports.",
        tags=["meta", "initialized"],
        confidence=0.99,
    )

    # Start API server in background thread if requested
    if api_port:
        import threading
        t = threading.Thread(target=start_api, args=(agent, api_port), daemon=True)
        t.start()
        print(f"\n   Agent API on :{api_port}")

    if api_only:
        print(f"\n   API-only mode — waiting for requests")
        # Keep main thread alive
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            print(f"\n🏛️  {agent.name} agent offline.")
        return

    # Main scribe loop
    try:
        while True:
            agent.run_cycle()
            print(f"\n⏳ Sleeping {interval}s...")
            time.sleep(interval)
    except KeyboardInterrupt:
        print(f"\n🏛️  {agent.name} agent offline after {agent.cycle_count} cycles.")
        agent.write(
            f"{agent.name} offline ({agent.cycle_count} cycles)",
            f"Ran {agent.cycle_count} cycles. Resuming on restart.",
            tags=["meta", "shutdown"],
        )


# ── Entrypoint ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="PLATO Agent Runtime — Agents live in PLATO, reach out through claws"
    )
    parser.add_argument("--agent", "-a", default=DEFAULT_AGENT,
                        help=f"Agent name (default: {DEFAULT_AGENT})")
    parser.add_argument("--interval", "-i", type=int, default=DEFAULT_INTERVAL,
                        help=f"Seconds between cycles (default: {DEFAULT_INTERVAL})")
    parser.add_argument("--capabilities", "-c", nargs="+",
                        default=["analytical", "creative", "reasoning", "implement"],
                        help="Capabilities to use (default: all)")
    parser.add_argument("--api-port", type=int, default=0,
                        help="Start HTTP API on this port (0 = disabled)")
    parser.add_argument("--api-only", action="store_true",
                        help="API server only, no scribe loop")
    parser.add_argument("--once", action="store_true",
                        help="Single cycle, then exit")

    args = parser.parse_args()

    if args.once:
        registry = ClawRegistry()
        agent = PlatoAgent(args.agent, registry, args.capabilities)
        agent.write(
            f"{args.agent} — single cycle",
            "One-shot reasoning cycle.",
            tags=["meta", "one-shot"],
        )
        agent.run_cycle()
        print(f"\nDone. Tiles in /{agent.room}/")
    else:
        agent_scribe_loop(
            agent_name=args.agent,
            interval=args.interval,
            capabilities=args.capabilities,
            api_port=args.api_port,
            api_only=args.api_only,
        )
