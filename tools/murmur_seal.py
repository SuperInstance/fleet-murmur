#!/usr/bin/env python3
"""murmur-seal — run the workspace's own state through MurmurLedger.

fleet-murmur's product is a hash-chained, replayable receipt ledger. This
tool applies it at home: seal a state file's identity (sha256 + bytes +
line count) into the workspace ledger, diff a file against its last seal,
and verify the chain end to end.

Doctrine (ported from the honesty pass):
- Seals record IDENTITY, not content — a seal never copies what it vouches
  for, so sealing never leaks the file it protects.
- Chains record TRANSITIONS — re-sealing identical bytes is a no-op; the
  chain is for state changes, not polls.
- Paths are RELATIVE — absolute machine paths break replay on any other
  node, the way gossip receipts must travel.

Usage:
    python tools/murmur_seal.py seal <file> [--ledger PATH]
    python tools/murmur_seal.py diff  <file> [--ledger PATH]
    python tools/murmur_seal.py verify [--ledger PATH]

Default ledger: state/ledger/murmur-seal.jsonl (created on first seal).
Exit codes: 0 ok · 1 usage/IO error · 2 broken chain.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from fleet_murmur.ledger import MurmurLedger  # noqa: E402

DEFAULT_LEDGER = Path("state") / "ledger" / "murmur-seal.jsonl"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _rel(path: Path, ledger_path: Path | None = None) -> str:
    """Location-independent name: cwd first (the usual seal context),
    then the ledger's own directory (tests, out-of-tree state), then
    absolute as the honest last resort. '..' paths are never sealed —
    they break replay on any other node, same rule as gossip receipts."""
    ap = os.path.abspath(path)
    anchors = [os.getcwd()]
    if ledger_path is not None:
        anchors.append(str(Path(ledger_path).parent))
    for anchor in anchors:
        r = os.path.relpath(ap, os.path.abspath(anchor))
        if not r.startswith(".."):
            return r
    return ap


def _last_seal(rows, name: str):
    for row in reversed(rows):
        if row.get("file") == name and row.get("event") == "SEAL":
            return row
    return None


def _rows(ledger_path: Path):
    if not ledger_path.exists():
        return []
    return MurmurLedger(ledger_path).replay()


def seal(path: str, ledger: str | Path = DEFAULT_LEDGER) -> dict:
    """Seal a file's identity into the workspace ledger. Idempotent on
    identical bytes; a genuine change appends a new SEAL row."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"seal: no such file: {path}")
    name = _rel(p, Path(ledger))
    ledger_path = Path(ledger)
    rows = _rows(ledger_path)
    digest = sha256_file(p)
    prev = _last_seal(rows, name)
    if prev and prev.get("sha256") == digest:
        return {"event": "SEAL", "file": name, "status": "UNCHANGED",
                "sha256": digest, "sealed_at": prev.get("ts")}
    raw = p.read_bytes()
    row = MurmurLedger(ledger_path).append(
        "SEAL", file=name, sha256=digest, bytes=len(raw),
        lines=raw.count(b"\n"),
    )
    row["status"] = "SEALED"
    return row


def diff(path: str, ledger: str | Path = DEFAULT_LEDGER) -> dict:
    """Compare a file against its last seal. MATCHES / CHANGED / UNSEALED."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"diff: no such file: {path}")
    name = _rel(p, Path(ledger))
    prev = _last_seal(_rows(Path(ledger)), name)
    if prev is None:
        return {"file": name, "status": "UNSEALED"}
    digest = sha256_file(p)
    status = "MATCHES" if digest == prev.get("sha256") else "CHANGED"
    return {"file": name, "status": status, "sealed_sha256": prev.get("sha256"),
            "current_sha256": digest, "sealed_at": prev.get("ts")}


def verify(ledger: str | Path = DEFAULT_LEDGER) -> dict:
    """Replay the chain. ok=False names the divergences, not just 'bad'."""
    ledger_path = Path(ledger)
    if not ledger_path.exists():
        return {"ok": False, "reason": f"no ledger at {ledger_path}", "rows": []}
    result = MurmurLedger(ledger_path).verify()
    result["rows"] = _rows(ledger_path) if result["ok"] else []
    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="murmur-seal")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for cmd in ("seal", "diff"):
        sp = sub.add_parser(cmd)
        sp.add_argument("file")
        sp.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    vp = sub.add_parser("verify")
    vp.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    args = ap.parse_args(argv)

    try:
        if args.cmd == "seal":
            out = seal(args.file, ledger=args.ledger)
        elif args.cmd == "diff":
            out = diff(args.file, ledger=args.ledger)
        else:
            out = verify(ledger=args.ledger)
            if not out["ok"]:
                print(json.dumps(out, default=str))
                return 2
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 1
    print(json.dumps(out, default=str))  # one JSON object per line — machine-first
    return 0


if __name__ == "__main__":
    sys.exit(main())
