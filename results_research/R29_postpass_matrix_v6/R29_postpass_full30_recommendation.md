---
research_id: R29-POSTPASS-MATRIX-V6
status: candidate-ready
baseline_tag: final_selector_v6_20260626
baseline_commit: ffd327f5013e5bef4913750579a99dacf0c4dcfb
branch: research/r29-postpass-matrix-v6
created: 2026-06-26
updated: 2026-06-26
affects_final: false
supersedes: []
superseded_by: []
primary_data:
  - results_research/R29_postpass_matrix_v6/R29_smoke_selection.csv
  - results_research/R29_postpass_matrix_v6/R29_postpass_smoke.csv
  - results_research/R29_postpass_matrix_v6/R29_postpass_full30.csv
  - results_research/R29_postpass_matrix_v6/R29_guarded_mfs_strash_dc2_rwz_full_metrics.csv
  - logs/R29_guarded_mfs_strash_dc2_rwz_full_cec.log
---

# R29 Post-pass Matrix Full 30 Recommendation

## Objective

Decide whether the R29 lightweight post-pass matrix should advance from
research smoke/full-public evidence into a candidate entrypoint/config phase.

## Baseline

- Formal baseline: `final_selector_v6_20260626`
- Commit: `ffd327f5013e5bef4913750579a99dacf0c4dcfb`
- Public metrics: `37464` selected AIG nodes, total levels `278`, max level
  `20`
- Correctness: CEC `30/30`, fallback `0`, crash/timeout/CEC fail `0/0/0`
- Formal zip SHA256:
  `EF7638BC06771F86485588A16786EAD760550CA86EFAD858B93EE1D808AA4E7F`

## Commands

Smoke selection:

```powershell
py -3 tools\r29_postpass_matrix.py select-smoke --metrics reports\final_metrics.csv --features reports\features.csv --out-dir results_research\R29_postpass_matrix_v6 --limit 10
```

Smoke matrix:

```powershell
py -3 tools\r29_postpass_matrix.py smoke --abc submit\bin\abc.exe --metrics reports\final_metrics.csv --case-list results_research\R29_postpass_matrix_v6\R29_smoke_cases.txt --outputs-root submit\results\final_public --cases-root C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public --out-dir results_research\R29_postpass_matrix_v6 --csv results_research\R29_postpass_matrix_v6\R29_postpass_smoke.csv --summary results_research\R29_postpass_matrix_v6\R29_postpass_smoke_summary.md
```

Full public matrix:

```powershell
py -3 tools\r29_postpass_matrix.py smoke --abc submit\bin\abc.exe --metrics reports\final_metrics.csv --case-list results_research\R29_postpass_matrix_v6\R29_full_cases.txt --outputs-root submit\results\final_public --cases-root C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public --out-dir results_research\R29_postpass_matrix_v6\full30 --csv results_research\R29_postpass_matrix_v6\R29_postpass_full30.csv --summary results_research\R29_postpass_matrix_v6\R29_postpass_full30_summary.md --pipeline-names r29_fraig_dc2_bal r29_mfs_fraig_dc2_bal r29_mfs_fraig_dc2_rwz_bal r29_mfs_strash_dc2_rwz_bal
```

Independent guarded-output CEC:

```powershell
py -3 tools\verify_all_cec.py --abc submit\bin\abc.exe --cases C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public --outputs results_research\R29_postpass_matrix_v6\guarded_r29_mfs_strash_dc2_rwz_full_public --log logs\R29_guarded_mfs_strash_dc2_rwz_full_cec.log --timeout 300
```

## Input Data

- Baseline metrics: `reports/final_metrics.csv`
- Structural features: `reports/features.csv`
- v6 formal outputs: `submit/results/final_public`
- Original BLIFs: `C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public`

## Results

Best full-public candidate:

- Candidate: `r29_mfs_strash_dc2_rwz_bal`
- Steps: `mfs; strash; dc2; rewrite -z; balance`
- Guarded result: `37260` selected AIG nodes
- Node gain vs v6: `204`
- Total level sum: `277` versus v6 `278`
- Max level: `20`
- Accepted cases: `9`
- Rejected/no-gain cases: `19`
- Rejected/level-regression cases: `2`
- CEC fail: `0`
- Timeout: `0`
- Opt fail: `0`
- Gain excluding best case: `147`
- Gain excluding top two cases: `111`

Full matrix comparison:

| candidate | accepted | safe gain | gain excl. best | gain excl. top2 | CEC fail | timeout | opt fail | level regression |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `r29_fraig_dc2_bal` | 9 | 165 | 120 | 90 | 0 | 0 | 0 | 2 |
| `r29_mfs_fraig_dc2_bal` | 9 | 177 | 132 | 102 | 0 | 0 | 0 | 2 |
| `r29_mfs_fraig_dc2_rwz_bal` | 9 | 204 | 147 | 111 | 0 | 0 | 0 | 2 |
| `r29_mfs_strash_dc2_rwz_bal` | 9 | 204 | 147 | 111 | 0 | 0 | 0 | 2 |

The best two candidates tie on public metrics. `r29_mfs_strash_dc2_rwz_bal` is
preferred for the next candidate phase because the explicit `strash` before
`dc2` avoids the command-shape issue observed in `mfs; dc2; balance`.

## Correctness

The full matrix checks every attempted candidate output with ABC CEC against
the original BLIF before marking it `accepted`. The materialized guarded output
tree then passed independent full public CEC:

- `logs/R29_guarded_mfs_strash_dc2_rwz_full_cec.log`
- equivalent count: `30`
- bad/error count: `0`

No formal submit artifact was modified.

## Risk

The current full-public result is strong, but it is not yet a release candidate.
The matrix materialization uses offline accepted/rejected rows. A real candidate
entrypoint must reproduce the same behavior online: run v6, try the post-pass
only under coarse gates, CEC-check the post-pass output, and accept only when
nodes decrease and level does not increase.

Runtime is the main remaining risk. If the post-pass is tried unconditionally on
all 30 public cases, the measured extra matrix overhead is approximately:

- post-pass opt: `29.220031s`
- post-pass CEC: `7.589127s`
- post-pass stats: `1.220020s`

The candidate phase should therefore use a coarse gate to avoid pointless
attempts on buckets that showed no gain.

## Selector Eligibility

The gain cases are explainable by coarse v6 buckets rather than public case
identity:

- `r7b_high_overlap_guarded_fraig`
- `medium_runtime_fraig_cleanup`
- `large_smallpo_fraig_cleanup`
- `r11_deepsyn_medium_tiny_po`

The next candidate entrypoint should attempt the R29 post-pass only on these
coarse buckets, then keep the same online accept rule:

- candidate CEC must pass
- `nodes_after < baseline_nodes`
- `levels_after <= baseline_levels`
- otherwise keep the v6 output

It must not use case names, hashes, exact public fingerprints, or exact port
name/order conditions.

## Conclusion

Decision label: `promote-to-candidate`.

R29 passes the research full-public evidence threshold and should enter a
candidate entrypoint/config phase. It should not be promoted directly to the
formal final and should not generate a submit package yet.

## Next Action

Build a candidate R29 entrypoint that wraps v6 and conditionally tries
`mfs; strash; dc2; rewrite -z; balance` on the coarse eligible buckets. Then run
full public 30 plus independent CEC from that entrypoint. If it reproduces
`37260` nodes, max level `20`, CEC `30/30`, fallback `0`, and acceptable
runtime/RSS, move to candidate review.
