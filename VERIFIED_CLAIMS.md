# VERIFIED_CLAIMS — fleet-murmur

Registry convention (ported from pong-quilt): every shipped claim names its
test evidence. `tests/test_honesty_pass.py::test_readme_claims_have_tests_and_counts_match`
pins this two ways — a claim row naming a missing file, or a README count that
drifts from the live suite, is build-red.

| VC | Claim | Evidence | Test file |
|----|-------|----------|-----------|
| VC01 | A zero-delivery transport never claims coverage — dropped batches are named, not folded into delivery | test_dropped_transport_never_claims_delivery, test_partial_batch_not_claimed_as_full | tests/test_honesty_pass.py |
| VC02 | Rounds without a transport are labeled SIMULATED, never CONFIRMED | test_no_transport_round_is_labeled_simulated | tests/test_honesty_pass.py |
| VC03 | A transport returning an iterable of msg_ids is honored exactly (precise contract) | test_precise_transport_contract_list_of_msg_ids | tests/test_honesty_pass.py |
| VC04 | The receipt ledger is hash-chained, replayable, and verifies clean | test_receipt_ledger_hash_chained_and_replayable | tests/test_honesty_pass.py |
| VC05 | Tampered or forged ledger rows are detected by verify() | test_ledger_tamper_detected | tests/test_honesty_pass.py |
| VC06 | Receipt trial balance: attempted == confirmed + simulated + unconfirmed + refused + dropped | test_gossip_protocol_emits_ledger_receipts_with_modes | tests/test_honesty_pass.py |
| VC07 | Quality-gate refusals leave a REFUSE receipt and never enter the rumor mill | test_quality_gate_refusal_produces_refusal_receipt_not_spread | tests/test_honesty_pass.py |
| VC08 | README's stated test count equals the live collected count; every registry row names an existing test | test_readme_claims_have_tests_and_counts_match | tests/test_honesty_pass.py |
| VC09 | Base protocol: dedup, fanout spread, hop counting, peer liveness, convergence detection | suite green | tests/test_fleet_murmur.py |
| VC10 | The quality-gate-stream adapter is written against the live qgs API and pinned by real-package runs: empty payloads refused, passing rumors enter the mill, absence returns None never faked, the seam names SuperInstance/quality-gate-stream | tests/test_qgs_adapter_glue.py (4 live pins run the real package; abstain as skips when uninstalled) | tests/test_qgs_adapter_glue.py |
