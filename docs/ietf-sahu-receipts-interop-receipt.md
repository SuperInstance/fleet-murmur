# Design receipt: IETF draft-sahu-agent-action-receipts-00 × fleet receipts doctrine

Status: VERIFIED against the source (not the relay). Companion to
`dei-distributed-qd-design-receipt.md` (arXiv 2605.27130); same shape,
same law: **edge weight = specificity × verification.**

## Source pin

- **Source:** N. Sahu, *Signed, Hash-Chained Action Receipts for AI Agents*,
  `draft-sahu-agent-action-receipts-00`, 16 August 2026, Intended status:
  Informational. https://datatracker.ietf.org/doc/draft-sahu-agent-action-receipts/
- **Abstract sha256:** `f82379e3bc40c5749db620576a5bdefe6e6f930eb5ff4a7738219d21ab08253b`
  (abstract quoted verbatim below the fold in this doc's commit message;
  reproduce by fetching the datatracker page and hashing the abstract
  paragraphs exactly as rendered, two-space sentence separators included).
- **Channel honesty:** the canonical `.txt` at `ietf.org/archive/id/` returned
  a Cloudflare challenge from this network; all claims below are verified
  against the datatracker HTML extraction. **Appendix A test vectors were NOT
  reproduced** (byte-exact reconstruction is ambiguous through page-wrap
  formatting) — recorded NOT-VERIFIED, not assumed. A vector re-run is the
  designated follow-up when a clean `.txt` channel exists.

## The relay check (edge-watch → source)

Edge-watch relayed: "signed, hash-chained agent action receipts whose survey
maps the whole cluster (asqav, SCITT capsule/execution, audit-trail, acta, + new
MVPS append-only hash-chained audit-log draft)."

- **VERIFIED.** §1.1 cites all of: farley-acta-signed-receipts,
  marques-asqav-compliance-receipts (signature *required*, regulatory profile),
  msebenzi-evidence-action (recomputable without trusting the runtime),
  sharif-agent-audit-trail (NDJSON + equivalent linkage member),
  noa-scitt-ai-agent-receipt and mih-scitt-agent-action-capsule (transparency-
  service statements, offline mode retained), emirdag-scitt-ai-agent-execution
  (per-record chain + independent custodian), kuehlewind-audit-architecture
  (architecture, no wire format), RFC 9943 (SCITT), and melegassi-opsawg-mvps-
  logging (append-only hash-chained externally-anchored audit logs, §9).
- Receipts-interop is now **8+ external shapes** in active draft, several
  converging on the same construction. "The signed-chain shape is
  commoditizing" — **VERIFIED**, stronger than relayed.

## The one construction that matters

Sahu's claimed distinction (§1.1, §6): the chain link is **SHA-256 over the
previous record's transmitted octets** — including its signature and any
member the verifier does not recognize. Every other cited linkage digests a
re-canonicalization of the previous record, or of the record minus its
signature. Consequences the draft draws:

| Draft (sahu) | Fleet (murmur/WAL family) |
|---|---|
| Link = digest of transmitted line octets; verifier MUST NOT re-serialize | Link = fnv1a-64 over a canonicalized key set (`{args,cell,hash,op,prev_hash,seq}` for WAL rows) |
| No canonicalizer in the verification path at all | Canonicalizer agreement required between writer and verifier |
| Signature (Ed25519) inside the digested octets → each link transitively commits to the signing key's output | Chains are unsigned; trust comes from the keeper registry + replay consensus, not per-row signatures |
| One writer per chain; cross-signer merge is verifier-side only | Multi-writer lanes with adjudication (coroner, HolonomyConsensus) — **tension, see below** |

## Doctrine resonances (the reason this receipt exists)

- **§9 "tamper-evidence, not tamper-proofing."** Same sentence fleet doctrine
  has been acting out: a compromised signer can mint well-formed fiction; the
  chain only binds whoever holds the key. VERIFIED alignment.
- **§9 "actions never recorded leave no trace."** The fleet's answer is the
  delivery-mode vocabulary (CONFIRMED / SIMULATED / UNCONFIRMED / REFUSED) and
  the trial balance — suppression shows up as a missing row in an attempted
  spread. The draft has no mode vocabulary; its suppression boundary is the
  signer. FOUND: complementary, not overlapping.
- **§9 head truncation → signed head assertion.** The draft names the exact
  gap and the exact fix: "a signed head assertion carrying at least the chain
  identity, the record count, and the head digest." That is **stone.sign +
  trustedKeys** — this morning's two key actions — now externally validated as
  the industry's named hole, not just our coroner tier-A prerequisite. VERIFIED
  resonance; priority justification documented.
- **§10 privacy: digests, not payloads.** "Where a receipt must commit to
  content, it SHOULD carry a digest of that content rather than the content
  itself." Fleet WAL rows already do payload-by-hash (`points_sha`, `bars_sha`,
  murmur-seal file sealing). VERIFIED alignment.
- **§9 canonicalization is an attack surface.** The draft's whole octet-link
  design exists because re-canonicalization disagrees between implementations.
  Fleet canonicalized rows carry this risk by construction; mitigated today by
  the schema-drift pins and one shared canonicalizer per family. FOUND:
  documented divergence, deliberate.

## What the draft does NOT have (moat check)

- No delivery-mode honesty vocabulary, no trial balance, no gossip/transport
  semantics, no re-execution. Receipts are attestations; the fleet's receipts
  are replayable state transitions. NOT-FOUND — the five-opcode + re-execution
  moat stands.
- No multi-writer story. One-writer-per-chain with verifier-side merge is the
  draft's answer to federation; the fleet runs adjudicated multi-writer lanes.
  INFERRED tension: if fleet chains ever export sahu-shaped records, the export
  is one-writer-per-chain by construction (per-lane), and cross-lane truth
  stays adjudication, not chain merging.

## Consequences (what changes because this exists)

1. **Watch the drafts cluster as both threat and interop surface.** A future
   -01 or a WGLC could standardize the octet-link shape; fleet export tooling
   should treat "sahu-compatible JSONL export" as a someday requirement, not a
   fantasy. No code today; this receipt is the tripwire.
2. **stone.sign + trustedKeys just got external cover.** When the keeper
   publishes the registry and the producer pins chain heads, cite this draft's
   §9 as independent confirmation the construction is the recognized answer.
3. **Canonicalizer discipline stays load-bearing.** Every new WAL row shape
   must keep the schema-drift pin pattern; the industry's own documents now
   name canonicalization drift as an attack surface.

*Receipt law: relay → source → claims tagged → consequence. Edge weight =
specificity × verification. Fetched 2026-09-28 via datatracker; sha256 pinned
above; vectors pending a clean .txt channel.*
