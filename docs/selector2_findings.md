# Selector 2.0 Findings

Phase 7 only. This candidate was validated without modifying `configs/final_selector.yaml`, `configs/pipelines.yaml`, or the submit package.

## Rule

`large_runtime_aig_high_effort`: choose `high_aig_three_round` only when `scale_grade in [large]`, `high_fanin_sop=false`, `near_two_input_aig=true`, and `runtime_size_bin in [runtime_large]`.

All other buckets retain the current final selector behavior: tiny/small high-fanin SOP -> `sop_fx`, medium non-AIG-like -> `rewrite2`, default -> `dc2_fast`.

## Validation Summary

- Selected total nodes: 45870 vs current final 47338.
- Raw total nodes: 45870.
- Max selected level: 25.
- Raw CEC: 30/30.
- Fallback count: 0.
- Wins/ties/losses vs current final: 6/24/0.
- gain_excluding_best_case: 276.
- gain_excluding_top2_cases: 87.
- Runtime/RSS warning counts: 0/0.

## Switched Cases

| case | bucket | selected pipeline | reason |
| --- | --- | --- | --- |
| tc_public_14 | large|runtime_large|near_aig=true|high_sop=false | high_aig_three_round | large_runtime_aig_high_effort |
| tc_public_19 | large|runtime_large|near_aig=true|high_sop=false | high_aig_three_round | large_runtime_aig_high_effort |
| tc_public_20 | large|runtime_large|near_aig=true|high_sop=false | high_aig_three_round | large_runtime_aig_high_effort |
| tc_public_21 | large|runtime_large|near_aig=true|high_sop=false | high_aig_three_round | large_runtime_aig_high_effort |
| tc_public_22 | large|runtime_large|near_aig=true|high_sop=false | high_aig_three_round | large_runtime_aig_high_effort |
| tc_public_30 | large|runtime_large|near_aig=true|high_sop=false | high_aig_three_round | large_runtime_aig_high_effort |

## Retained Current Final Cases

24 cases retained current final pipeline choices.

## Level Regressions

No selected-level regression was observed.

## Phase 8 Gate

- Meets Phase 8 numeric gate: yes.
- Selector rule uses only coarse structural features and does not reference file names, paths, hashes, exact counts, public case ids, or oracle results.
- The high-effort rule covers a multi-case large AIG-like bucket, not a single public case.

## Stop Point

Phase 7 completed. Phase 8 decision and final replacement were not run.
