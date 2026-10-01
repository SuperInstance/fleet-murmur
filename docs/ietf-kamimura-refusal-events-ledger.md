# Refusal-events ledger: IETF draft-kamimura-scitt-refusal-events-03 × pong-quilt named refusals

Status: design receipt. Source VERIFIED against the datatracker extraction;
fleet corpus VERIFIED present-tense against **SuperInstance/pong-quilt** main
merge `d51631e` (playtest-round-67 head, 2026-10-01; supersedes the `52b42b4`
/R65 pin of the first version — see *Corpus lifecycle* below). Companion to
`ietf-sahu-receipts-interop-receipt.md`; same shape, same law:
**edge weight = specificity × verification.**

Booked by the 2026-09-30 16:11 snowball pulse as the queue's synergy
candidate: pong-quilt accumulates NAMED refusal receipts on main while the
IETF draft goes standards-track. This ledger is the fleet's position on the
refusal-receipt standard, with pong-quilt's corpus as the first candidate
evidence pack (draft Appendix D shape).

## Source pin

- **Source:** T. Kamimura (VeritasChain Standards Organization), *Verifiable AI
  Refusal Events using SCITT*, `draft-kamimura-scitt-refusal-events-03`,
  2 August 2026, Intended status: Informational. Expires 3 February 2027.
  https://datatracker.ietf.org/doc/draft-kamimura-scitt-refusal-events/
- **Abstract sha256:** `b835f6633aac9d5e5c3ac5be84a5f05adc411c193edf0ed2a2d382214ff87a32`
  (reproduce: fetch the datatracker page, extract the three abstract paragraphs
  exactly as rendered, join with a blank line, UTF-8, sha256 — two-space
  sentence separators included, no trailing newline).
- **Channel honesty:** verified against the datatracker HTML extraction from
  this network on 2026-09-30. The CDDL grammar (§4) and JSON appendix (§C)
  were read but NOT machine-reproduced — recorded as read-only, not assumed.
- **Companion channel:** draft-sabey-refusal-transparency (refused agent-system
  transitions, replay resistance) is named by §1.4 as complementary; not yet
  audited by this fleet. Recorded as an open read, not a cleared claim.

## The claim set (what the draft asks for)

- Four event types: **ATTEMPT**, **DENY**, **GENERATE**, **ERROR**; every event
  carries `event-id` (UUIDv7 recommended), `timestamp`, `issuer`.
- ATTEMPT (§3.2) records receipt of a generation request and MUST be created
  **before any safety evaluation begins** — the anti-selective-logging rule.
  It carries `prompt-hash` (SHA-256+, the prompt itself MUST NOT be stored),
  `input-type`, optional `session-id`, `actor-hash` (pseudonymous), `model-id`,
  `policy-id`.
- DENY (§3.3) refuses a request: `attempt-id` (correlation to its ATTEMPT),
  optional `risk-category`, `risk-score`, `refusal-reason` (SHOULD NOT contain
  prompt content), `human-override`.
- **Completeness invariant (§3.6):** every registered ATTEMPT has exactly one
  Outcome — |ATTEMPT| = |DENY| + |GENERATE| + |ERROR|. Verifiers check it;
  transparency services do not enforce it.
- SCITT integration (§5): claim set as COSE_Sign1 payload, registration via
  SCRAPI, a Verifiable Refusal Record = ATTEMPT + DENY statements, receipts,
  and the attempt-id correlation, timestamp ordering.
- Privacy (§8): digests not payloads, pseudonymous actors, refusal-reason
  must not quote the prompt.

## The fleet corpus (SuperInstance/pong-quilt, main `d51631e`)

Six live named refusal / negative-outcome receipt kinds, verified
present-tense in the pin commit, plus one superseded kind whose lifecycle
is recorded below:

| kind | site (main @d51631e) | round | refusal-reason, named | prompt content? |
|---|---|---|---|---|
| `SAVE/COEV-EMPTY` | index.html:396 | R67 | empty C1 state — nothing to keep yet, "Train first"; the R64 refusal survives only for this state | none |
| `LOAD/COEV-MALFORMED` | index.html:425 | R67 | a coev-shaped file missing its load-bearing fields — named refusal, zero state change | none |
| `QA-REFUSAL` | index.html:248,253 | R12 | advice channel silent — sim pot under the shots floor, or a real QPAM backend's underflow; exhaustion is receipted, never dropped silently | none |
| `byo-qpam-fallback` | index.html:247 | R16 | BYO QPAM endpoint failure (JEV-invalid payload, fetch failure, no endpoint) — degrades to the labeled sim at same seed/pot, advice NAMED qa-sim, never laundered as byo-qpam | none |
| `WAL-EXPORT/REFUSED` | index.html:416 | R30 | WAL export self-verification verdict non-ok — refusal receipt, no file saved | none |
| `SEAL/REFUSED` | tools/prerun.js:144,152,203; tools/wal-session.js:185 | R37-era coev prerun | stone seal chain fails mirror/canonical/live verify — refusal path, exit 1, no checkpoint file | none |
| `WAL-EXPORT/EMPTY` | index.html:422 | R30 | empty receipt panel exports a genesis-only chain — receipted degenerate case, not a refusal but a named negative outcome kept for invariant accounting | none |

### Corpus lifecycle — refusals are era-stamped receipts

`SAVE/COEV-UNSTABLE` (R64–R66, pinned at index.html:395 under `52b42b4`)
was correct for three rounds: coev-mode SAVE would have written the
franken-quilt (coev gen/champ over classic pop, mixed lineage), so the save
was refused named. R67's coev-quilt writer made the franken class impossible
by construction — the coev banner now WRITES a one-lane file with no classic
field able to disagree with the weights — and the refusal's job moved from
"stop the lie" to "name the empty state": the same site now receipts
`SAVE/COEV-EMPTY` when there is nothing to keep. The R64 name is retired,
not erased: pong-quilt's own pins disclose the supersession in both
directions (the updated r64 pin asserts the surviving empty-state refusal
AND the writer's truth). A named refusal has a natural lifecycle; a ledger
that only appends without retiring is itself a mild Goodhart surface.

## Mapping to the draft — what clears, what does not

**Clears, VERIFIED:**

- *§8.1 privacy — digests, not payloads.* Every refusal kind above carries a
  named `refusal-reason` and zero prompt/request content. pong-quilt's receipt
  culture (hashes, named kinds, no payloads) is already §8.1-shaped.
- *refusal-reason named and human-readable.* Each kind's reason string names
  the wound and its round lineage — no silent drops anywhere in the corpus;
  lifecycle transitions (SAVE/COEV-UNSTABLE → SAVE/COEV-EMPTY) are disclosed
  at the pin sites, not smoothed over.
- *Issuer identifiable.* Every receipt row is issued by the page/tooling under
  the SuperInstance/pong-quilt repo identity; round provenance (R12/R16/R30/
  R59/R64) is the informal correlation anchor.

**Does NOT clear — recorded, not assumed:**

- *§3.6 completeness invariant: **not met**.* pong-quilt logs DENY-shaped rows
  with no preceding ATTEMPT. There is no `attempt-id` correlation (round
  lineage is informal), so |ATTEMPT| = |DENY| + … cannot even be evaluated.
  The §3.2 rule that ATTEMPT MUST precede safety evaluation is precisely the
  property the fleet does not yet log.
- *§5 transparency registration: **not met**.* The receipt panel is a local
  append-only ledger, not a SCITT transparency service; there are no signed
  statements, no SCRAPI registration, no inclusion receipts. The fleet's
  answer to tamper-evidence today is its own chain tooling (murmur/WAL/stone
  families), not RFC 9943 registration.
- *§3.3 risk vocabulary.* The fleet's kinds are mechanism-named
  (SAVE/COEV-UNSTABLE, QA-REFUSAL), not risk-category-named (Appendix A
  taxonomy). Mapping the corpus onto deployment risk categories is future
  work, deliberately not retrofitted.

**Classification:** the fleet corpus is a set of DENY-shaped, locally
receipted audit rows without ATTEMPT pairing or transparency-service
registration. Honest posture: audit-trail spirit met (named refusals, no
payloads, append-only); cryptographic completeness and third-party
verifiability not claimed.

## Upgrade lane (what would mint a real SCITT profile)

Sized as a future lane, not this pulse — each step is small but the chain is
a day-class build against live advice/save flows:

1. **ATTEMPT row before evaluation** — advice generation and coev SAVE each
   open an ATTEMPT (UUIDv7 event-id) before the decision point, carrying
   input-type and a prompt-hash (page-side hash only, §8.1).
2. **DENY carries attempt-id** — the six kinds above gain the correlation
   field; completeness becomes evaluable per-session.
3. **Transparency registration** — a SCRAPI-shaped registrar for the receipt
   ledger (the fleet already has seal/chain tooling; registration is the new
   piece), retaining offline mode per fleet doctrine.
4. **Completeness monitor** — application-level verifier (§3.6: services do
   not enforce; verifiers do) as a CI pin over exported evidence packs.

## Why this ledger exists

- **Positions the fleet early** on the refusal-receipt standard while the
  draft is informational and open — the same window in which the fleet
  already tracks draft-sahu-agent-action-receipts (see the companion
  receipt).
- **Names the corpus as the first evidence pack.** The six kinds, with round
  provenance and site pins, are the fleet's candidate Appendix-D evidence
  pack; the upgrade lane above is the gap list to make it submittable.
- **Keeps the edge honest.** The pq → fm referral this ledger mints cites
  SuperInstance/pong-quilt by name at a pinned main merge; the citation is
  specific (six kinds, sites, rounds) so the edge weight is earned under the
  specificity × verification law, not asserted.
