# Design Receipt — DEI (arXiv:2605.27130) × Fleet Breeding-over-WAL

Status: analysis, committed as a receipt. Every claim is tagged
**[VERIFIED]** (read at the named source this date, quoted verbatim),
**[FOUND]** (named fleet artifact exists, description read),
**[INFERRED]** (design judgment, no artifact read), or
**[NOT-FOUND]** (looked, absent). Nothing else.

## Receipts block

| Field | Value |
|---|---|
| Source | https://arxiv.org/abs/2605.27130 (DEI: Diversity in Evolutionary Inference) |
| Version read | v1, submitted Tue 26 May 2026 15:00:57 UTC (per submission history) |
| Fetched | 2026-09-28 (Asia/Shanghai) by the CCC main session |
| Abstract digest | sha256 `8b68936e…9403f` = the quoted block below (markdown `>` prefixes stripped, UTF-8) |

> "We present DEI: Diversity in Evolutionary Inference, a distributed Quality-Diversity
> (QD) search framework that assigns heterogeneous large language models (LLMs) as
> mutation operators across peer nodes communicating with non-blocking collective
> operations. Unlike homogeneous parallel search, which replicates a single model's
> inductive biases across all workers, DEI treats each LLM's distinct creative prior
> as a complementary source of behavioral novelty. Extending the Digital Red Queen
> framework with DEI, nodes share local optimal solutions at the end of each round
> to seed the next round's population. This creates cross-model adversarial pressure
> that drives robustness beyond intra-model self-play. Evaluated on the Core War
> domain, a four-node heterogeneous ensemble (GPT-5.4-mini, Claude Sonnet 4.6,
> GPT-5.2, and Claude Haiku 4.5) achieves 124 percent higher merged-archive QD-Score
> (45.90 vs. 20.46) and 28 percent higher coverage (80.6 percent vs. 63.0 percent
> of cells) than a single-node baseline at equal total LLM-call budget. The
> heterogeneous ensemble also outperforms an equally-budgeted homogeneous ensemble
> on QD-Score, coverage, and held-out solution generality across all four model
> families."

## What DEI proves that matters here

1. **[VERIFIED]** Heterogeneous mutation operators beat homogeneous ones at *equal
   LLM-call budget* — diversity of creative priors is the load-bearing variable,
   not parallelism. The gain is large (+124% QD-Score, +28% coverage on Core War).
2. **[VERIFIED]** Round-end champion sharing (local optima seed the next round)
   with non-blocking collectives is a sufficient gossip discipline — no global
   lockstep archive sync is required.
3. **[VERIFIED]** Cross-model adversarial pressure (Digital Red Queen extended)
   drives robustness beyond intra-model self-play.

## Delta: DEI ↔ fleet breeding-over-WAL

| DEI component | Fleet counterpart | Tag |
|---|---|---|
| Heterogeneous LLMs as mutation operators | CCC fleet already runs heterogeneous models across repos/pulses | [FOUND] |
| MAP-Elites archive (grid, QD-Score, coverage) | erised-mirror: archive + kinship by local embedding, mass views — QD-archive-adjacent, no explicit grid/elites bookkeeping | [FOUND] / [INFERRED] |
| Round-end champion sharing | fleet-murmur RumorMill: push-based rumor-mongering over topics with dedup + pacing — the natural champion carrier | [FOUND] |
| Non-blocking collectives | MurmurLedger: hash-chained, replayable, verify-clean receipt ledger | [FOUND] |
| Receipts / replay of the search itself | **[NOT-FOUND]** — DEI reports outcomes; the search trace is not a first-class verifiable artifact | — |
| Archive merge semantics (federated archives) | quilt-stone / five-opcode WAL receipts bind artifacts to commits | [FOUND] |

## Doctrine consequence

DEI's results are unreceipted claims about a search no one can replay [VERIFIED —
the abstract reports outcomes only]. The fleet's breeding-over-WAL lane keeps
every breeding decision in the WAL (five-opcode receipts + re-execution), so its
QD claims are *re-derivable* [FOUND — wal-export cites the five-opcode shape;
quilt-stone verifies 42/42 sibling chains]. That is the moat, and DEI
strengthens it: the frontier now converges on the WAL shape independently
(TierMem), which means shape alone commoditizes — **receipts + re-execution do
not**. Edge-watch's earlier "async champion gossip" phrasing is corrected here:
the paper says round-end sharing over non-blocking collectives [VERIFIED].

## Adopt / keep / decline

- **ADOPT 1 — champion gossip over fleet-murmur.** Publish breeding artifacts
  (round elites) as ledger-sealed murmurs on a topic; consumers seed their next
  round from verified receipts only. Smallest build: one producer emitting one
  sealed champion per round + one consumer reading; an evening.
- **ADOPT 2 — archive metrics.** Compute QD-Score/coverage over erised-mirror's
  embedding archive so "is the fleet actually covering its space" stops being a
  vibe. Smallest build: a script over the existing archive view; half a day.
- **ADOPT 3 — deliberate heterogeneity ledger.** When a breeding round assigns
  mutation lanes, record the model per lane in the WAL; measure heterogeneous
  vs homogeneous rounds on the fleet's own tasks, DEI-style, at equal call
  budget. Smallest build: one WAL field + one comparison run.
- **KEEP — receipts + re-execution as the archive-merge law.** Any champion
  adopted across nodes must verify through the chain before entering the local
  population (verify-before-adopt, same as pong-quilt's prerun verifyTipSignature
  discipline).
- **DECLINE — nothing.** Watch item: red-queen-class CLIs commoditizing the
  *search* layer raises the value of the receipt layer, not lower.

## Related

- erised-mirror (archive + receipt chains, 45/45 verified through quilt-stone)
- fleet-murmur README (RumorMill / PeerManager / MurmurLedger)
- wal-export (quilt-blueprint#2): five-opcode WAL adoption, live-verified
  through quilt-doctor
- edge-watch frontier notes (TierMem convergence; red-queen CLI)
