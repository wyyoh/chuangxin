# Final Selector v2 Decision

## Decision

Selector v2 is promoted as the final candidate after Phase 8 review.

| Metric | Phase A hardened | Selector v2 final |
| --- | ---: | ---: |
| Selected AIG nodes | 47338 | 45870 |
| Node gain | - | 1468 |
| Max level | 25 | 25 |
| CEC | 30/30 | 30/30 |
| Fallback count | 0 | 0 |
| Crash / timeout / CEC fail | 0 / 0 / 0 | 0 / 0 / 0 |
| Wins / ties / losses vs Phase A | - | 6 / 24 / 0 |

## Replacement Rationale

Selector v2 changes only the coarse selector and one ABC pipeline definition. It keeps the same no-pthread ABC binary and the same CEC/fallback gates.

The promoted rule selects `high_aig_three_round` only for coarse large, runtime-large, near-two-input AIG-like structures with `high_fanin_sop=false`. All other buckets retain the Phase A selector behavior:

- default: `dc2_fast`
- tiny/small high-fanin SOP: `sop_fx`
- medium non-near-two-input-AIG: `rewrite2`

The rule is structural and hidden-set plausible. It does not use file names, paths, hashes, case identifiers, exact counts, or oracle winners.

## Anti-Overfit Evidence

Phase 6 and Phase 7 results support promotion:

- `high_aig_three_round` was the only Phase 5 candidate passing the Phase 7 hard gate.
- Phase 7 selector validation produced 45870 selected nodes, max level 25, CEC 30/30, fallback 0.
- `gain_excluding_best_case = 276`.
- `gain_excluding_top2_cases = 87`.
- Wins/ties/losses were 6/24/0, so the gain is not from a single public case.
- Runtime and RSS warning counts were both 0.

## Why Not ShareCone

ShareCone remains a research candidate only. Public aggregate metrics were worse than Selector v2 and the Phase A final:

- ShareCone v1: 49825 nodes, max level 22, 11 fallback cases.
- ShareCone v2: 48832 nodes, max level 22, 8 fallback cases.
- Selector v2 final: 45870 nodes, max level 25, fallback 0.

No ShareCone pipeline is enabled in the final selector.

## Why Not Oracle

Oracle results are upper-bound analysis only. They depend on per-case winners and are marked `ORACLE_ONLY_DO_NOT_SUBMIT` in search artifacts. They are not used in the final selector and are not packaged as submission behavior.

## Risks And Rollback

Main residual risk is that the promoted bucket may be less predictive on hidden cases than on public cases. The rule is deliberately conservative: it covers only large runtime-size near-two-input AIG-like structures and avoids tiny/small high-fanin SOP buckets.

Rollback is straightforward:

- restore `configs/final_selector.yaml` from `configs/final_selector_phase_a_hardened.yaml`;
- restore the old package from `submit_sharecone_phase_a_hardened.zip`;
- use tag `phase_a_hardened_20260526` as the full repository recovery point.
