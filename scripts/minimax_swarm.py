#!/usr/bin/env python3
"""
MiniMax Swarm — Parallel model calls coordinated into synthesized output.

MiniMax 2.7 is our subscription model. Use it extensively, in parallel,
and coordinate its outputs. This is the competitive routing principle
applied to model instances instead of hardware types.

Architecture:
    Task → N parallel MiniMax calls (different contexts/perspectives)
         → Coordinator synthesizes results
         → PLATO tile written with synthesized insight

Each parallel call gets a different "blinder" — a different focus, 
temperature, and system prompt. The coordinator weaves them back together.
"""

import json
import os
import random
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

PLATO_URL = "http://localhost:8847"
SWARM_ROOM = "swarm-insights"

# MiniMax API config
MINIMAX_URL = "https://api.minimax.io/v1/chat/completions"
MINIMAX_MODEL = "MiniMax-M2.7"

# ── Auth ────────────────────────────────────────────────────────────────────

def get_minimax_key() -> str:
    """Get MiniMax API key from OpenClaw auth profile"""
    try:
        import json as j
        with open(os.path.expanduser("~/.openclaw/agents/main/agent/auth-profiles.json")) as f:
            data = j.load(f)
        return data["profiles"]["minimax:global"]["key"]
    except Exception:
        pass
    # Fallback to env
    return os.environ.get("MINIMAX_API_KEY", "")

def get_minimax_group_id() -> str:
    """Get MiniMax group ID from bashrc or env"""
    try:
        with open(os.path.expanduser("~/.bashrc")) as f:
            for line in f:
                if "MINIMAX_GROUP_ID" in line:
                    return line.split("=", 1)[1].strip().strip('"\'')
    except Exception:
        pass
    return ""

# ── MiniMax Call ─────────────────────────────────────────────────────────────

def call_minimax(messages: list, temp: float = 0.7, max_tokens: int = 1000,
                 label: str = "unnamed") -> Optional[str]:
    """Single MiniMax 2.7 call"""
    key = get_minimax_key()
    gid = get_minimax_group_id()
    
    if not key:
        print(f"  ❌ [{label}] No MiniMax key")
        return None
    
    data = {
        "model": MINIMAX_MODEL,
        "messages": messages,
        "temperature": temp,
        "max_tokens": max_tokens,
        "stream": False,
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
    }
    # Some MiniMax endpoints need group-id
    if gid:
        headers["X-Group-Id"] = gid
    
    req = urllib.request.Request(
        MINIMAX_URL,
        data=json.dumps(data).encode(),
        headers=headers,
        method="POST",
    )
    
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            # MiniMax Openai-compatible format
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            # Strip thinking tags from MiniMax reasoning
            import re as _re
            content = _re.sub(r'<think>.*?</think>', '', content, flags=_re.DOTALL).strip()
            if content:
                return content
            return str(result)[:200]
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:200]
        print(f"  ❌ [{label}] MiniMax HTTP {e.code}: {body}")
        return None
    except Exception as e:
        print(f"  ❌ [{label}] MiniMax error: {e}")
        return None


# ── Swarm Coordinator ────────────────────────────────────────────────────────

def swarm(task: str, n_calls: int = 5, context: str = "",
          synth_temp: float = 0.3) -> List[Dict]:
    """
    Run N parallel MiniMax calls with different perspectives, then synthesize.
    
    Each call gets a unique blind-width assignment and focus area.
    """
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"\n{'='*60}")
    print(f"[{ts}] 🐝 Swarm: {n_calls} parallel MiniMax calls")
    print(f"   Task: {task[:80]}")
    print(f"{'='*60}")
    
    # Define perspective blinder profiles
    blinders = [
        {"role": "analyst",     "temp": 0.3, "focus": "Break down the task into components"},
        {"role": "creative",    "temp": 0.9, "focus": "Generate unexpected connections"},
        {"role": "critic",      "temp": 0.3, "focus": "Find flaws and edge cases"},
        {"role": "synthesizer", "temp": 0.5, "focus": "Find common ground and unify"},
        {"role": "explorer",    "temp": 0.8, "focus": "Explore what's missing or unasked"},
        {"role": "implementer", "temp": 0.4, "focus": "Turn this into concrete steps"},
        {"role": "skeptic",     "temp": 0.2, "focus": "Challenge every assumption"},
        {"role": "visionary",   "temp": 0.9, "focus": "Project 10x outcomes from this"},
    ]
    
    # Assign blinders, cycle if more calls than profiles
    assignments = []
    for i in range(n_calls):
        b = blinders[i % len(blinders)]
        assignments.append(b)
    
    # ── Phase 1: Parallel calls ──────────────────────────────────────────────
    results = []
    for i, blinder in enumerate(assignments):
        print(f"\n  🐝 Worker {i+1}/{n_calls} ({blinder['role']})")
        
        system_prompt = (
            f"You are a {blinder['role']} in a swarm of AI agents collaborating on a task. "
            f"Your focus: {blinder['focus']}. "
            f"Be specific. Be concise. Provide actionable insights. "
            f"Your perspective is one of many — don't try to cover everything, cover your angle."
        )
        
        user_prompt = f"Task: {task}\n\nContext: {context}\n\nProvide your {blinder['role']} perspective in 2-4 paragraphs."
        
        content = call_minimax(
            [{"role": "system", "content": system_prompt},
             {"role": "user", "content": user_prompt}],
            temp=blinder["temp"],
            max_tokens=600,
            label=blinder["role"],
        )
        
        result = {
            "role": blinder["role"],
            "focus": blinder["focus"],
            "temperature": blinder["temp"],
            "content": content or "(no output)",
        }
        results.append(result)
        
        if content:
            print(f"     {content[:120]}...")
        else:
            print(f"     ❌ No output")
    
    # ── Phase 2: Coordinate / Synthesize ──────────────────────────────────────
    print(f"\n  🧠 Coordinating {len(results)} perspectives...")
    
    summaries = "\n\n".join(
        f"[{r['role'].upper()}] {r['content'][:300]}"
        for r in results if r.get('content')
    )
    
    synthesis_prompt = (
        f"A swarm of {n_calls} agents analyzed this task:\n\n{task}\n\n"
        f"Here are their individual perspectives:\n\n{summaries}\n\n"
        f"Synthesize these into a unified insight. What do they agree on? "
        f"What's the most important unresolved tension? What should be done next? "
        f"3-5 paragraphs."
    )
    
    synthesis = call_minimax(
        [{"role": "system", "content": "You are a swarm coordinator. Synthesize multiple perspectives into clear, actionable insight. Find the signal in the noise."},
         {"role": "user", "content": synthesis_prompt}],
        temp=synth_temp,
        max_tokens=1000,
        label="coordinator",
    )
    
    if not synthesis:
        synthesis = "[Synthesis failed — individual results are above]"
    
    print(f"\n  ✅ Synthesis: {synthesis[:200]}...")
    
    return {
        "task": task,
        "context": context,
        "n_calls": n_calls,
        "individual_results": results,
        "synthesis": synthesis,
    }


def plato_tile(room: str, question: str, answer: str, tags: list = None) -> bool:
    """Submit a tile to PLATO"""
    data = {
        "room": room,
        "question": question[:200],
        "answer": answer[:2000],
        "tags": tags or [],
        "source": "minimax-swarm",
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


# ── Continuous Swarm Loop ────────────────────────────────────────────────────

def swarm_loop(interval: int = 180, n_calls: int = 5):
    """Run the swarm continuously on rotating topics"""
    topics = [
        "What's the next breakthrough in agent architecture?",
        "How should PLATO rooms evolve as tile density increases?",
        "What's the relationship between tensor-network rooms and 24-bit audio encoding?",
        "What does the Differential Axiom imply about consensus protocols?",
        "How should competitive hardware routing work in practice?",
        "What's the optimal blind-width schedule for a new agent?",
        "How do shelf-sign gradients interact with spline dependencies?",
        "What's the next layer of the Common Space Pattern that hasn't been formalized yet?",
        "How does micro-syncopation ε improve spline reconstruction quality?",
        "What's the relationship between bit allocation in 24-bit tiles and attention allocation?",
    ]
    
    print(f"\n🐝 MiniMax Swarm — continuous loop")
    print(f"   {n_calls} parallel calls per cycle")
    print(f"   {interval}s interval")
    print(f"   Room: {SWARM_ROOM}/")
    
    # Prime room
    plato_tile(SWARM_ROOM, "Swarm activated",
               f"MiniMax Swarm running. {n_calls} parallel calls per cycle. Room for synthesized swarm insights.",
               tags=["meta", "swarm"])
    
    cycle = 0
    while True:
        cycle += 1
        topic = topics[(cycle - 1) % len(topics)]
        
        result = swarm(topic, n_calls=n_calls)
        
        # Tile to PLATO
        plato_tile(
            SWARM_ROOM,
            f"Swarm {cycle}: {topic[:60]}",
            f"Perspectives: {', '.join(r['role'] for r in result['individual_results'])}\n\n"
            f"SYNTHESIS:\n{result['synthesis'][:1500]}",
            tags=["swarm", f"cycle-{cycle}"],
        )
        
        print(f"\n  📝 Tiled to swarm-insights/")
        print(f"\n⏳ Sleeping {interval}s...")
        time.sleep(interval)


# ── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="MiniMax Swarm — parallel model calls")
    parser.add_argument("--task", "-t", help="Single task, run once and exit")
    parser.add_argument("--calls", "-n", type=int, default=5, help="Parallel calls per swarm")
    parser.add_argument("--loop", action="store_true", help="Run continuous loop")
    parser.add_argument("--interval", "-i", type=int, default=180, help="Loop interval")
    parser.add_argument("--context", "-c", default="", help="Additional context for task")
    args = parser.parse_args()
    
    if args.task:
        result = swarm(args.task, n_calls=args.calls, context=args.context)
        print(f"\n{'='*60}")
        print("SYNTHESIS:")
        print(result['synthesis'])
        # Tile it
        plato_tile(SWARM_ROOM,
                   f"Swarm: {args.task[:60]}",
                   result['synthesis'][:2000],
                   tags=["swarm", "one-shot"])
        print(f"\n📝 Tiled to {SWARM_ROOM}/")
    
    elif args.loop:
        swarm_loop(interval=args.interval, n_calls=args.calls)
    
    else:
        # Run a default demo
        print("🐝 MiniMax Swarm Demo")
        print("   Usage: --task 'your question'  (one shot)")
        print("          --loop                  (continuous)")
        print("          --calls N               (parallel calls, default 5)")
        print()
        result = swarm("What should I build to demonstrate parallel MiniMax 2.7 coordination?",
                       n_calls=args.calls)
        print(f"\n{'='*60}")
        print("SYNTHESIS:")
        print(result['synthesis'][:500])
