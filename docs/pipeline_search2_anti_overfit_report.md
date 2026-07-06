# Pipeline Search 2.0 Anti-overfit Report

Phase 6 only. No selector candidate was generated, and no final/submit artifacts were modified.

## Candidate Summary

| candidate | raw nodes | selected nodes | max level | CEC | fallback | W/T/L | gain excl best | gain excl top2 | best-case ratio | Phase 7 eligible |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| aig_resyn_resub_zero | 47095 | 47031 | 25 | 30/30 | 2 | 3/24/3 | -40 | -82 | 1.165 | no |
| choice_fraig_clean | 45916 | 45850 | 21 | 30/30 | 2 | 3/21/6 | -77 | -92 | 1.054 | no |
| choice_fraig_ifraig_recover | 46233 | 45462 | 21 | 30/30 | 2 | 10/14/6 | -327 | -558 | 1.296 | no |
| choice_ifraig_clean | 45916 | 45850 | 21 | 30/30 | 2 | 3/21/6 | -77 | -92 | 1.054 | no |
| dc2_fraig_cleanup | 46233 | 45462 | 21 | 30/30 | 2 | 10/14/6 | -327 | -558 | 1.296 | no |
| dc2_ifraig_cleanup | 46233 | 45462 | 21 | 30/30 | 2 | 10/14/6 | -327 | -558 | 1.296 | no |
| high_aig_three_round | 45919 | 45884 | 25 | 30/30 | 1 | 11/15/4 | 227 | 38 | 0.840 | yes |

## Raw vs Selected

- All seven candidates have raw CEC 30/30 and selected total nodes below 47338.
- Selected totals are not purely raw for any candidate: every candidate has 1 or 2 metric-regression fallbacks.
- Candidates whose raw anti-overfit is weak are marked research-only even if selected totals look strong.

## high_aig_three_round

- Selected total nodes: 45884 (< 47338).
- Raw total nodes: 45919 (< 47338).
- Max level: 25 (<= 25).
- Wins/ties/losses: 11/15/4.
- gain_excluding_best_case: 227; gain_excluding_top2_cases: 38.
- Fallback count: 1; raw remains globally better without relying on fallback.
- Runtime/RSS warnings: 0/0.

Largest high_aig_three_round raw gains are concentrated on large near-two-input AIG-like cases, but the candidate still has positive gain after removing the best and top two gains. Regressions are small and mostly tiny/small high-fanin SOP or small cleanup-sensitive cases.

High-aig regression cases with raw node loss:

| case | raw delta | level delta | bucket | coarse avoidable |
| --- | ---: | ---: | --- | --- |
| tc_public_4 | 35 | 1 | tiny\|high_sop\|non_aig\|two_ratio_low | yes |
| tc_public_3 | 24 | 1 | tiny\|high_sop\|non_aig\|two_ratio_low | yes |
| tc_public_1 | 14 | -2 | tiny\|high_sop\|non_aig\|two_ratio_low | yes |
| tc_public_26 | 4 | 0 | medium\|not_sop\|near_aig\|two_ratio_near_one | no |

Coarse bucket leads for high_aig_three_round:

| bucket feature | bucket value | cases | W/T/L | total delta | selector-rule candidate |
| --- | --- | ---: | --- | ---: | --- |
| scale_grade | large | 6 | 6/0/0 | -1468 | yes |
| scale_grade | medium | 5 | 2/2/1 | -17 | yes |
| scale_grade | small | 13 | 2/11/0 | -6 | yes |
| high_fanin_sop | false | 22 | 9/12/1 | -1490 | yes |
| near_two_input_aig | true | 18 | 8/9/1 | -1475 | yes |
| two_input_ratio_bin | two_ratio_mid | 3 | 2/1/0 | -16 | yes |
| two_input_ratio_bin | two_ratio_near_one | 12 | 7/4/1 | -1286 | yes |
| two_input_ratio_bin | two_ratio_very_high | 2 | 1/1/0 | -189 | yes |
| names_bin | names_large | 6 | 6/0/0 | -1468 | yes |
| names_bin | names_medium | 5 | 2/2/1 | -17 | yes |
| names_bin | names_small | 13 | 2/11/0 | -6 | yes |
| cubes_bin | cubes_large | 5 | 5/0/0 | -1279 | yes |
| cubes_bin | cubes_medium | 3 | 2/1/0 | -204 | yes |
| cubes_bin | cubes_small | 10 | 2/7/1 | -7 | yes |
| max_fanin_bin | fanin_3_4 | 5 | 1/4/0 | -1 | yes |
| max_fanin_bin | fanin_le2 | 21 | 9/11/1 | -1490 | yes |
| outputs_bin | po_medium | 10 | 3/6/1 | -191 | yes |
| outputs_bin | po_small | 15 | 6/6/3 | -1212 | yes |
| outputs_bin | po_tiny | 4 | 1/3/0 | -1 | yes |
| level_bin | level_high | 5 | 5/0/0 | -1441 | yes |

## Phase 7 Gate

- Phase 7 eligible by hard gates: high_aig_three_round.
- Robust Pareto candidate(s): high_aig_three_round.
- Recommended Phase 7 priority: `high_aig_three_round` first, because it is the only candidate with both gain_excluding_best_case and gain_excluding_top2_cases positive.
- All other Phase 5 candidates are research-only at this gate because their raw gains collapse after removing the best public case or top two cases.
- Suggested coarse direction for high_aig_three_round: large/medium near-two-input AIG-like or runtime-large buckets; avoid tiny/small high-fanin SOP buckets where final `sop_fx` remains better.

## Stop Point

Phase 6 completed. Phase 7 selector generation and Phase 8 final decision were not run.
