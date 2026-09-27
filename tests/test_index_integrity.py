"""test_index_integrity.py — INDEX.md is a receipt, not a souvenir.

The 2026-09-28 reorg moved 100+ top-level entries into docs/, assets/,
labs/, and coord/. INDEX.md maps old paths to new ones. This pin keeps
the map honest: every destination named in the index must exist, and the
index must live at the root (the contract agents and docs cite).

FAIL-first evidence in the reorg PR: with INDEX.md absent, the existence
pin trips RED naming the missing file; with a row pointing at a
nonexistent path, the row pin trips RED naming the path.
"""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "INDEX.md"


def _rows():
    assert INDEX.exists(), (
        "INDEX.md missing from repo root — the reorg map is the contract; "
        "restore it or regenerate the old→new mapping"
    )
    rows = []
    for line in INDEX.read_text().splitlines():
        if line.startswith("| `") and "->" not in line and "---" not in line:
            parts = [p.strip().strip("`") for p in line.strip("|").split("|")]
            if len(parts) == 2:
                rows.append(parts)
    return rows


def test_index_exists_and_has_mappings():
    rows = _rows()
    assert len(rows) >= 100, f"INDEX.md names only {len(rows)} mappings — the reorg moved 100+"


def test_every_mapped_destination_exists():
    missing = [new for _, new in _rows() if not (ROOT / new).exists()]
    assert missing == [], (
        "INDEX.md destinations that do not exist (map drifted from the tree): "
        + ", ".join(missing[:8])
    )
