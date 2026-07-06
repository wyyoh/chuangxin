# Current Pipeline Diagnosis

This diagnosis is based on the `phase_a_hardened_20260526` baseline artifacts. It is intentionally read-only with respect to current final files.

## Baseline Summary

- Final total AIG nodes: 47338.
- Final max level: 25.
- Final CEC: 30/30.
- Final fallback count: 0.
- Final opt runtime sum: 9.493 sec.
- Final CEC runtime sum: 6.164 sec.
- Final peak RSS max: 31.305 MB.

## Final Pipeline Usage

| pipeline | selected cases |
| --- | ---: |
| `dc2_fast` | 21 |
| `sop_fx` | 8 |
| `rewrite2` | 1 |

The final selector is coarse and uses only:

- `scale_grade_in: [tiny, small]` plus `high_fanin_sop: true` -> `sop_fx`.
- `scale_grade_in: [medium]` plus `near_two_input_aig: false` -> `rewrite2`.
- default -> `dc2_fast`.

## Largest Gains Vs Baseline

| case | pipeline | selected nodes | baseline nodes | gain | selected level | baseline level |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tc_public_30` | `dc2_fast` | 6613 | 9418 | 2805 | 21 | 22 |
| `tc_public_14` | `dc2_fast` | 3703 | 4474 | 771 | 25 | 26 |
| `tc_public_11` | `dc2_fast` | 328 | 1064 | 736 | 7 | 6 |
| `tc_public_22` | `dc2_fast` | 11067 | 11265 | 198 | 20 | 20 |
| `tc_public_21` | `dc2_fast` | 5577 | 5685 | 108 | 20 | 20 |
| `tc_public_20` | `dc2_fast` | 5559 | 5664 | 105 | 20 | 20 |
| `tc_public_19` | `dc2_fast` | 5304 | 5403 | 99 | 18 | 18 |
| `tc_public_13` | `dc2_fast` | 1058 | 1130 | 72 | 13 | 14 |
| `tc_public_4` | `sop_fx` | 69 | 115 | 46 | 8 | 9 |
| `tc_public_3` | `sop_fx` | 109 | 150 | 41 | 8 | 11 |

## Zero-Gain Cases

These cases tie the baseline on selected nodes:

`tc_public_10`, `tc_public_16`, `tc_public_17`, `tc_public_2`, `tc_public_23`, `tc_public_24`, `tc_public_25`, `tc_public_27`, `tc_public_28`, `tc_public_6`, `tc_public_7`, `tc_public_8`, `tc_public_9`.

## Portfolio Context

The existing offline portfolio confirms that the current final is already close to the best among the Phase A configured pipelines:

| pipeline | nodes | max level | fallbacks | CEC fails |
| --- | ---: | ---: | ---: | ---: |
| `dc2_fast` | 47430 | 25 | 0 | 0 |
| `rewrite2` | 49510 | 24 | 3 | 0 |
| `sop_fx` | 51743 | 26 | 8 | 0 |
| `aig_fast` | 51875 | 26 | 12 | 0 |
| `baseline` | 52423 | 26 | 0 | 0 |

Phase B/C diagnostic artifacts are not part of this phase A branch. Non-mutating inspection of tag `phase_b_c_diagnostics_20260526` shows the old selector candidate reached 47337 nodes, max level 25, CEC 30/30, by changing only `tc_public_8` from `sop_fx` to `dc2_fast` for a 1-node gain and local level delta +1. That is not strong enough evidence for direct promotion.

## Artifact Consistency

- `reports/final_metrics.csv` matches `submit/final_metrics.csv`.
- `logs/final_cec.log` matches `submit/final_cec.log`.
- `configs/final_selector.yaml` matches `submit/configs/final_selector.yaml`.
- `configs/pipelines.yaml` matches `submit/configs/pipelines.yaml`.
- `logs/final_cec.log` contains 30 `passed=True` entries.

## Reusable Tooling

- Evaluation: `tools/eval_public.py`.
- Offline portfolio runner: `tools/run_portfolio.py`.
- Per-case ABC execution, CEC, fallback, metrics, RSS: `tools/run_abc_case.py`.
- Final CEC verification: `tools/verify_all_cec.py`.
- BLIF feature extraction: `tools/extract_blif_features.py`.
- Selector validation and choice generation: `tools/select_pipeline.py`.
- ABC stats parsing: `tools/parse_abc_stats.py`.
- Scoreboard generation: `tools/build_scoreboard.mjs`.

## Phase 2/3 Notes

- `data/tc_public/` and `results/` are not tracked baseline artifacts; this worktree restored `data/tc_public/` via `tools/fetch_tc_public.ps1` for capability probing.
- Pipeline Search 2.0 must not overwrite `reports/final_metrics.csv`, `logs/final_cec.log`, `configs/final_selector.yaml`, or `submit_sharecone.zip`.
