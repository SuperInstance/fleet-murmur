#!/usr/bin/env python3
"""field-cli — interact with the continuous constraint field from the command line.

Usage:
    field embed --position 42 --weight 0.95 --stiffness 200 --tau 10000
    field read --query 0 --position 0.0
    field topology
    field propagate --dt 3600
    field nails
    field status
"""

import json, os, sys, time, hashlib, argparse
from pathlib import Path

STATE_FILE = Path("/tmp/field-state.json")
PLATO_URL = "http://localhost:8847"

def load_field():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"nails": [], "iterations": 0}

def save_field(field):
    STATE_FILE.write_text(json.dumps(field, indent=2))

def conf_to_u8(confidence):
    return max(0, min(255, int(confidence * 255)))

def u8_to_conf(bits):
    return bits / 255.0

def effective_weight(nail, now):
    dt = max(0, now - nail["embedded_at"])
    return nail["weight"] * (2.71828 ** (-dt / nail["tau"]))

def field_read(nails, x, now):
    """Read the field at position x at time now.
    Returns the interpolated field value using inverse-distance weighting."""
    numerator = 0.0
    denominator = 0.0
    
    for nail in nails:
        w = effective_weight(nail, now)
        if w < 0.001:
            continue
        dx = x - nail["position"]
        dist_sq = dx * dx + 1e-6
        weight = w * nail["stiffness"] / dist_sq
        numerator += weight * nail["position"]
        denominator += weight
    
    return numerator / denominator if denominator > 0 else 0.0

def field_topology(nails, now):
    """Count local minima in the field at time now."""
    samples = 100
    minima = 0
    prev_slope = 0.0
    
    for i in range(1, samples):
        x1 = i / samples * 100 - 50
        x0 = (i - 1) / samples * 100 - 50
        y0 = field_read(nails, x0, now)
        y1 = field_read(nails, x1, now)
        slope = y1 - y0
        
        if prev_slope < 0 and slope >= 0:
            minima += 1
        prev_slope = slope
    
    return minima

def propagate(nails, now, dt):
    """Drift nails toward the field gradient.
    Low-weight nails move. High-weight nails anchor."""
    new_nails = []
    
    for nail in nails:
        w = effective_weight(nail, now)
        if w < 0.001:
            continue
        
        field_val = field_read(nails, nail["position"], now)
        drift = (field_val - nail["position"]) * (1 - w) * dt / nail["stiffness"]
        decay = 2.71828 ** (-dt / nail["tau"])
        
        new_nails.append({
            "position": nail["position"] + drift,
            "weight": nail["weight"] * decay,
            "stiffness": nail["stiffness"],
            "embedded_at": nail["embedded_at"],
            "tau": nail["tau"],
        })
    
    return new_nails

def cmd_embed(args):
    field = load_field()
    nail = {
        "position": args.position,
        "weight": args.weight,
        "stiffness": args.stiffness,
        "embedded_at": int(time.time()),
        "tau": args.tau,
    }
    field["nails"].append(nail)
    field["iterations"] = field.get("iterations", 0) + 1
    save_field(field)
    print(f"Embedded nail at position {args.position} (w={args.weight}, s={args.stiffness}, τ={args.tau})")
    print(f"Total nails: {len(field['nails'])}")

def cmd_read(args):
    field = load_field()
    if not field["nails"]:
        print("Field is empty — no nails embedded")
        return
    now = int(time.time())
    val = field_read(field["nails"], args.position, now)
    topo = field_topology(field["nails"], now)
    
    material = {6: "Cedar", 12: "Oak", 30: "Fiberglass", 200: "Steel"}
    h_level = {0: "H0 (flat)", 1: "H1 (additive)", 2: "H2 (multiplicative)", 3: "H3 (exponential)", 4: "H4+ (tetrative)"}
    
    mat = material.get(int(field["nails"][0]["stiffness"]), "Custom")
    # Find hyperoperation level from topology
    hyper = h_level.get(min(topo, 4), f"H{topo}+")
    
    print(f"Field at position {args.position}: {val:+.6f}")
    print(f"Topology: {topo} minima → {hyper}")
    print(f"Material: {mat}")
    print(f"Nails: {len(field['nails'])} active")

def cmd_topology(args):
    field = load_field()
    if not field["nails"]:
        print("Field is empty")
        return
    now = int(time.time())
    topo = field_topology(field["nails"], now)
    
    h_levels = {0: "H0 (flat/empty)", 1: "H1 (additive, stable)",
                2: "H2 (multiplicative, competing)", 3: "H3 (exponential, confined)",
                4: "H4+ (tetrative, breaching)"}
    
    print(f"Field topology: {topo} local minima")
    print(f"Hyperoperation level: {h_levels.get(min(topo, 4), 'H{topo}+ (unstable)')}")
    
    if topo >= 3:
        print("⚠️  Field is breaching — topology changing faster than hash can track")
    elif topo >= 2:
        print("→ Field has competing minima — system under moderate strain")
    elif topo == 1:
        print("✓ Field is stable — single equilibrium")
    else:
        print("— Field is flat — no structure")

def cmd_propagate(args):
    field = load_field()
    if not field["nails"]:
        print("Field is empty")
        return
    now = int(time.time())
    topo_before = field_topology(field["nails"], now)
    before_count = len(field["nails"])
    
    field["nails"] = propagate(field["nails"], now, args.dt)
    field["iterations"] = field.get("iterations", 0) + 1
    save_field(field)
    
    topo_after = field_topology(field["nails"], now + args.dt)
    
    print(f"Propagated by dt={args.dt}")
    print(f"Nails: {before_count} → {len(field['nails'])} ({before_count - len(field['nails'])} dropped)")
    print(f"Topology: {topo_before} → {topo_after}")
    
    if topo_after != topo_before:
        print(f"⚡ EMERGENCE: topology changed! {topo_before} → {topo_after}")

def cmd_nails(args):
    field = load_field()
    if not field["nails"]:
        print("No nails in field")
        return
    now = int(time.time())
    
    print(f"{'Pos':>8} {'Weight':>8} {'Eff.W':>8} {'Stiff':>8} {'Tau':>8} {'Age':>8}")
    print("-" * 60)
    for n in field["nails"]:
        w_eff = effective_weight(n, now)
        age = now - n["embedded_at"]
        mat = {6: "Ced", 12: "Oak", 30: "FG", 200: "Stl"}.get(int(n["stiffness"]), "Cus")
        print(f"{n['position']:>+8.2f} {n['weight']:>8.3f} {w_eff:>8.3f} {mat:>8} {n['tau']:>8.0f} {age:>8}")
    
    print(f"\nTotal: {len(field['nails'])} nails")

def cmd_status(args):
    field = load_field()
    now = int(time.time())
    
    if field["nails"]:
        topo = field_topology(field["nails"], now)
        sample = field_read(field["nails"], 0.0, now)
    else:
        topo = 0
        sample = 0.0
    
    print(f"Field state:")
    print(f"  Nails:       {len(field['nails'])}")
    print(f"  Topology:    {topo} minima")
    print(f"  Value at 0:  {sample:+.6f}")
    print(f"  Iterations:  {field.get('iterations', 0)}")
    print(f"  State file:  {STATE_FILE}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Continuous Constraint Field CLI")
    sub = parser.add_subparsers(dest="command")
    
    p_embed = sub.add_parser("embed", help="Embed a nail in the field")
    p_embed.add_argument("--position", type=float, required=True)
    p_embed.add_argument("--weight", type=float, default=0.5)
    p_embed.add_argument("--stiffness", type=float, default=12.0)
    p_embed.add_argument("--tau", type=float, default=3600.0)
    
    p_read = sub.add_parser("read", help="Read the field at a position")
    p_read.add_argument("--position", type=float, default=0.0)
    
    p_topology = sub.add_parser("topology", help="Check field topology")
    p_prop = sub.add_parser("propagate", help="Propagate nails by dt")
    p_prop.add_argument("--dt", type=float, default=3600.0)
    
    sub.add_parser("nails", help="List all nails")
    sub.add_parser("status", help="Field status")
    
    args = parser.parse_args()
    
    if args.command == "embed":
        cmd_embed(args)
    elif args.command == "read":
        cmd_read(args)
    elif args.command == "topology":
        cmd_topology(args)
    elif args.command == "propagate":
        cmd_propagate(args)
    elif args.command == "nails":
        cmd_nails(args)
    elif args.command == "status":
        cmd_status(args)
    else:
        parser.print_help()
