"""test_refusal_events_ledger.py — the refusal-events ledger is a receipt, not a summary.

The 2026-09-30 pulse booked the 16:11 synergy candidate: pong-quilt accumulates
NAMED refusal receipts on main while IETF draft-kamimura-scitt-refusal-events-03
goes standards-track. This pin keeps the ledger doc honest:

1. it exists at the canonical path;
2. it pins the source draft by name + author (Kamimura) + abstract sha256;
3. it cites SuperInstance/pong-quilt BY NAME at a pinned main merge — the
   citation that mints the pq -> fm referral edge under the weight law
   (edge weight = specificity x verification);
4. its corpus table names every refusal kind present on pong-quilt main
   at the pin (six live kinds at d51631e/R67, site + round provenance each),
   and names the superseded kind (SAVE/COEV-UNSTABLE, R64–R66 era) with its
   lifecycle recorded — refusals are era-stamped receipts, a named refusal
   has a natural lifecycle (R67 PLAYLOG d(honesty)/d(refusals));
5. it records the honest gap: the draft's completeness invariant is named
   and marked NOT met (no ATTEMPT pairing, no transparency service) — the
   anti-Goodhart bar, a ledger that only claims what it clears.

FAIL-first evidence in the PR: on a tree without the ledger doc the
existence pin trips RED naming the missing file; with a refusal kind
dropped from the corpus the corpus pin trips RED naming the kind.
"""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "docs" / "ietf-kamimura-refusal-events-ledger.md"

DRAFT_NAME = "draft-kamimura-scitt-refusal-events-03"
AUTHOR = "Kamimura"
ABSTRACT_SHA = "b835f6633aac9d5e5c3ac5be84a5f05adc411c193edf0ed2a2d382214ff87a32"
PQ_PIN = "SuperInstance/pong-quilt"
MAIN_MERGE = "d51631e"

# The named refusal / negative-outcome receipt kinds on pong-quilt main
# at pin d51631e (playtest-round-67 head, 2026-10-01), each verified
# present-tense in the pin commit. SAVE/COEV-EMPTY and LOAD/COEV-MALFORMED
# arrived with R67's coev-quilt writer; SAVE/COEV-UNSTABLE is the R64–R66
# name, superseded by the writer (it survives only as SAVE/COEV-EMPTY for
# the empty C1 state) — the corpus pins the supersession by name.
REFUSAL_KINDS = [
    "SAVE/COEV-EMPTY",        # index.html:396 — R67: empty C1 state, nothing to keep yet (supersedes SAVE/COEV-UNSTABLE)
    "LOAD/COEV-MALFORMED",    # index.html:425 — R67: coev-shaped file missing load-bearing fields, zero state change
    "QA-REFUSAL",           # index.html:248,253 — R12: advice channel silent, exhaustion receipted
    "byo-qpam-fallback",    # index.html:247 — R16: BYO QPAM failure degrades to labeled sim, named
    "WAL-EXPORT/REFUSED",   # index.html:416 — R30: WAL self-verify non-ok, no file saved
    "SEAL/REFUSED",         # tools/prerun.js:144,152,203; tools/wal-session.js:185 — stone seal verify failed
    "WAL-EXPORT/EMPTY",     # index.html:422 — R30: genesis-only export, receipted degenerate case
]

# The R64–R66 era name, retired by R67's coev writer: pinned here so the
# corpus can never silently drop the supersession (the anti-Goodhart bar
# cuts both ways — no silent weakening of pins, no silent erasure of history).
SUPERSEDED_KIND = "SAVE/COEV-UNSTABLE"


def _text():
    assert LEDGER.exists(), (
        "docs/ietf-kamimura-refusal-events-ledger.md missing — the refusal-events "
        "ledger is the fleet's position on draft-kamimura-scitt-refusal-events-03; "
        "restore it or re-book the lane"
    )
    return LEDGER.read_text()


def test_ledger_exists():
    assert len(_text()) > 1500, "ledger doc present but suspiciously thin — a receipt, not a stub"


def test_source_pin_complete():
    text = _text()
    assert DRAFT_NAME in text, "ledger must pin the source draft by name"
    assert AUTHOR in text, "ledger must name the draft author (Kamimura)"
    assert ABSTRACT_SHA in text, "ledger must carry the abstract sha256 (reproducible source pin)"


def test_pong_quilt_cited_by_name_at_main_pin():
    text = _text()
    assert PQ_PIN in text, (
        "ledger must cite SuperInstance/pong-quilt by name — the by-name citation "
        "is what mints the pq -> fm referral edge under the weight law"
    )
    assert MAIN_MERGE in text, "ledger must pin the pong-quilt main merge sha it audited"


def test_corpus_names_all_refusal_kinds_at_pin():
    text = _text()
    missing = [kind for kind in REFUSAL_KINDS if kind not in text]
    assert not missing, (
        f"corpus dropped refusal kinds present on main at the pin: {missing} — "
        "either restore them or re-audit main and update the pin commit"
    )


def test_superseded_kind_lifecycle_recorded():
    text = _text()
    assert SUPERSEDED_KIND in text, (
        f"the superseded kind {SUPERSEDED_KIND} vanished from the corpus — "
        "refusals are era-stamped receipts; the R67 supersession must stay "
        "named (no silent erasure of pin history)"
    )
    assert "SAVE/COEV-EMPTY" in text, (
        "the supersession must name the successor kind SAVE/COEV-EMPTY"
    )


def test_completeness_invariant_honestly_recorded_as_not_met():
    text = _text()
    assert "completeness invariant" in text, (
        "ledger must engage the draft's core integrity property by name"
    )
    assert "not met" in text, (
        "ledger must record the honest classification: the completeness invariant "
        "is NOT met (no ATTEMPT pairing, no transparency-service registration) — "
        "claiming otherwise would be a Goodhart violation"
    )
