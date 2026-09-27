"""FAIL-first pins: the doctor takes his own medicine.

fleet-murmur sells MurmurLedger — a hash-chained, replayable receipt ledger —
as its product. But the workspace's own append-only state files
(HEARTBEAT.md, STATUS.md, FLEET-STATUS.md, memory/JOURNAL.md, archivist
snapshots) were never run through it. S6 (Cocapn discovery wave) ranked this
repo the #1 unsealed spine in the account.

tools/murmur_seal.py closes that gap: one CLI to seal a file's identity
(sha256 + bytes + line count) into the workspace's own ledger, diff a file
against its last seal, and verify the chain.

Every test here must be RED on the pre-build tree:
    python3 -m pytest tests/test_murmur_seal.py -q
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import murmur_seal


def write_state(tmp_path: Path, name: str, body: str) -> Path:
    p = tmp_path / name
    p.write_text(body)
    return p


# ---------------------------------------------------------------- sealing

def test_seal_writes_verifying_chain(tmp_path):
    f = write_state(tmp_path, "HEARTBEAT.md", "beat: 1\n")
    ledger = tmp_path / "ledger" / "self-seal.jsonl"
    row = murmur_seal.seal(f, ledger=ledger)
    result = murmur_seal.verify(ledger)
    assert result["ok"], result
    assert row["event"] == "SEAL"
    assert row["sha256"] == murmur_seal.sha256_file(f)
    assert row["bytes"] == len(b"beat: 1\n")
    assert row["lines"] == 1


def test_seal_names_relative_path_portably(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "state").mkdir()
    f = write_state(tmp_path, "STATUS.md", "status: GREEN\n")
    row = murmur_seal.seal(f, ledger=tmp_path / "state" / "ledger.jsonl")
    # Absolute machine paths break replay on any other node; seals must be
    # location-independent the way gossip receipts are.
    assert not os.path.isabs(row["file"])
    assert row["file"] == "STATUS.md"


def test_unchanged_file_is_noop_second_seal(tmp_path):
    """Append-only does not mean spam-only: re-sealing identical bytes must
    not grow the chain (the chain is for state transitions, not polls)."""
    f = write_state(tmp_path, "HEARTBEAT.md", "beat: 1\n")
    ledger = tmp_path / "ledger.jsonl"
    murmur_seal.seal(f, ledger=ledger)
    before = len(ledger.read_text().splitlines())
    note = murmur_seal.seal(f, ledger=ledger)
    after = len(ledger.read_text().splitlines())
    assert after == before
    assert note["status"] == "UNCHANGED"


def test_changed_file_appends_new_seal(tmp_path):
    f = write_state(tmp_path, "STATUS.md", "status: GREEN\n")
    ledger = tmp_path / "ledger.jsonl"
    murmur_seal.seal(f, ledger=ledger)
    f.write_text("status: RED\n")
    row = murmur_seal.seal(f, ledger=ledger)
    assert row["status"] == "SEALED"
    assert row["sha256"] != murmur_seal.sha256_file(write_state(tmp_path, "x", "status: GREEN\n"))


def test_multiple_files_share_one_chain_in_order(tmp_path):
    a = write_state(tmp_path, "HEARTBEAT.md", "a\n")
    b = write_state(tmp_path, "FLEET-STATUS.md", "b\n")
    ledger = tmp_path / "ledger.jsonl"
    murmur_seal.seal(a, ledger=ledger)
    murmur_seal.seal(b, ledger=ledger)
    rows = murmur_seal.verify(ledger)["rows"]
    assert [r["file"] for r in rows] == ["HEARTBEAT.md", "FLEET-STATUS.md"]


# ---------------------------------------------------------------- diff

def test_diff_reports_unsealed_change(tmp_path):
    f = write_state(tmp_path, "STATUS.md", "GREEN\n")
    ledger = tmp_path / "ledger.jsonl"
    murmur_seal.seal(f, ledger=ledger)
    f.write_text("RED\n")
    d = murmur_seal.diff(f, ledger=ledger)
    assert d["status"] == "CHANGED"
    assert d["file"] == "STATUS.md"


def test_diff_clean_when_matching(tmp_path):
    f = write_state(tmp_path, "STATUS.md", "GREEN\n")
    ledger = tmp_path / "ledger.jsonl"
    murmur_seal.seal(f, ledger=ledger)
    assert murmur_seal.diff(f, ledger=ledger)["status"] == "MATCHES"


def test_diff_unsealed_file_says_so(tmp_path):
    f = write_state(tmp_path, "NEVER.md", "?\n")
    d = murmur_seal.diff(f, ledger=tmp_path / "ledger.jsonl")
    assert d["status"] == "UNSEALED"


# ---------------------------------------------------------------- chain safety

def test_tampered_ledger_fails_verify(tmp_path):
    f = write_state(tmp_path, "STATUS.md", "GREEN\n")
    ledger = tmp_path / "ledger.jsonl"
    murmur_seal.seal(f, ledger=ledger)
    lines = ledger.read_text().splitlines()
    row = json.loads(lines[0])
    row["sha256"] = "forged"
    lines[0] = json.dumps(row)
    ledger.write_text("\n".join(lines) + "\n")
    assert not murmur_seal.verify(ledger)["ok"]


# ---------------------------------------------------------------- CLI

def run_cli(*argv, cwd=REPO):
    return subprocess.run(
        [sys.executable, str(REPO / "tools" / "murmur_seal.py"), *argv],
        capture_output=True, text=True, cwd=cwd, timeout=60)


def test_cli_seal_verify_roundtrip(tmp_path):
    f = write_state(tmp_path, "HEARTBEAT.md", "beat\n")
    ledger = tmp_path / "ledger.jsonl"
    r1 = run_cli("seal", str(f), "--ledger", str(ledger))
    assert r1.returncode == 0, r1.stderr
    r2 = run_cli("verify", "--ledger", str(ledger))
    assert r2.returncode == 0, r2.stderr
    assert json.loads(r2.stdout.strip().splitlines()[-1])["ok"] is True


def test_cli_verify_exit_2_on_broken_chain(tmp_path):
    f = write_state(tmp_path, "HEARTBEAT.md", "beat\n")
    ledger = tmp_path / "ledger.jsonl"
    run_cli("seal", str(f), "--ledger", str(ledger))
    ledger.write_text(ledger.read_text() + '{"event":"SEAL","prev":"forged","hash":"forged"}\n')
    r = run_cli("verify", "--ledger", str(ledger))
    assert r.returncode == 2
