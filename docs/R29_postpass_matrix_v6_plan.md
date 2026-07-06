---
research_id: R29-POSTPASS-MATRIX-V6
status: active
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
---

# R29 Post-pass Matrix V6 Plan

## Objective

Explore whether the R28 success pattern can be extended safely: apply lightweight
ABC post-passes on top of the verified v6 formal outputs, accept only outputs
that pass CEC, reduce nodes, and do not increase level.

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

## Input Data

- v6 baseline metrics: `reports/final_metrics.csv`
- coarse structural features: `reports/features.csv`
- baseline outputs: `submit/results/final_public`
- original input BLIFs: the `input_path` fields in `reports/final_metrics.csv`,
  with `C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public` as the
  explicit fallback.

## Candidate Post-passes

The first matrix uses six lightweight post-passes:

- `r29_fraig_dc2_bal`: `fraig; dc2; balance`
- `r29_mfs_dc2_bal`: `mfs; dc2; balance`
- `r29_mfs_fraig_bal`: `mfs; fraig; balance`
- `r29_mfs_fraig_dc2_bal`: `mfs; fraig; dc2; balance`
- `r29_fraig_mfs_dc2_bal`: `fraig; mfs; dc2; balance`
- `r29_mfs_fraig_dc2_rwz_bal`: `mfs; fraig; dc2; rewrite -z; balance`

## Results

Pending. Smoke selection has been generated in
`results_research/R29_postpass_matrix_v6/R29_smoke_selection.csv`.

## Correctness

Every attempted post-pass output must pass ABC CEC against the original input
before it can be marked `accepted`. A case-level accepted row also requires
`nodes_after < baseline_nodes` and `levels_after <= baseline_levels`.

## Risk

This is research-only. It does not modify `configs/final_selector.yaml`,
`configs/pipelines.yaml`, `submit/`, or `submit_sharecone.zip`.

The main risk is public-set overfitting if the winning cases cannot be explained
by coarse structural features. A full 30 result is not enough for promotion
unless gain excluding the best and top two cases remains positive.

## Selector Eligibility

No selector is generated in R29 Gate 2. Any later candidate must use coarse
structural predicates only, such as selector reason, chosen variant, scale
bucket, runtime bucket, high-fanin SOP flag, near-two-input-AIG flag, and
TFI-overlap-derived buckets. Case names are audit labels only.

## Conclusion

Decision label: `continue`.

The R28 pattern produced a clean v6 increment. A bounded post-pass matrix is
worth one smoke round because it tests the same monotonic accept/rollback idea
without contaminating the formal final.

## Next Action

Run the smoke matrix. Continue to full public 30 only if at least one candidate
has all smoke CEC passing, no timeout/crash, at least two safe gains, and
positive smoke total safe gain.
