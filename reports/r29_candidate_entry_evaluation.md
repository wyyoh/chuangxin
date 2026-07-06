---
research_id: R29-POSTPASS-MATRIX-V6
status: candidate-ready
baseline_tag: final_selector_v6_20260626
baseline_commit: ffd327f5013e5bef4913750579a99dacf0c4dcfb
branch: candidate/r29-postpass-entry
created: 2026-06-26
updated: 2026-06-26
affects_final: false
supersedes:
  - results_research/R29_postpass_matrix_v6/R29_postpass_full30_recommendation.md
superseded_by: []
primary_data:
  - reports/r29_candidate_entry_full_public_candidate_config.csv
  - reports/r29_candidate_entry_candidate_config_summary.json
  - logs/r29_candidate_entry_full_public_candidate_config_cec.log
---

# R29 Candidate Entry Evaluation

## Objective

Promote the R29 post-pass matrix result into a guarded candidate entrypoint on
top of the current formal v6 baseline, without generating a submit archive.

The candidate keeps the v6 optimizer as the first stage, then tries the R29
post-pass only on coarse structural buckets. A post-pass output is accepted only
when it passes CEC against the original input, reduces AIG node count, and does
not increase AIG level.

## Baseline

| Item | Value |
| --- | ---: |
| Baseline tag | `final_selector_v6_20260626` |
| Baseline commit | `ffd327f5013e5bef4913750579a99dacf0c4dcfb` |
| Baseline nodes | `37464` |
| Baseline level sum | `278` |
| Baseline max level | `20` |
| Baseline CEC | `30/30` |
| Baseline fallback | `0` |

## Candidate

The candidate branch is `candidate/r29-postpass-entry`.

New candidate files:

- `tools/optimize_one_r29_postpass_candidate.py`
- `configs/pipelines_r29_postpass_candidate.yaml`
- `configs/final_selector_candidate.yaml`
- `configs/pipelines_candidate.yaml`

Modified candidate-only entry/eval files:

- `tools/optimize_one.py`
- `tools/eval_public_optimize_one.py`

R29 post-pass:

```text
mfs; strash; dc2; rewrite -z; balance
```

Eligible coarse gates:

- `r7b_high_overlap_guarded_fraig`
- `medium_runtime_fraig_cleanup`
- `large_smallpo_fraig_cleanup`
- `r11_deepsyn_medium_tiny_po`

Forbidden public-set selector conditions are not used. The gate is based on the
existing coarse selector reason produced by the v6 feature pipeline.

## Commands

Smoke:

```powershell
py -3 tools\eval_public_optimize_one.py --abc submit\bin\abc.exe --cases C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public --case-list results_candidate\r29_entry_smoke\cases.txt --selector configs\final_selector.yaml --pipelines configs\pipelines.yaml --out results_candidate\r29_entry_smoke\outputs --csv reports\r29_entry_smoke.csv
```

Full public with formal selector paths:

```powershell
py -3 tools\eval_public_optimize_one.py --abc submit\bin\abc.exe --cases C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public --selector configs\final_selector.yaml --pipelines configs\pipelines.yaml --out results_candidate\r29_postpass_entry_full_public --csv reports\r29_candidate_entry_full_public.csv
```

Full public with candidate selector/config paths:

```powershell
py -3 tools\eval_public_optimize_one.py --abc submit\bin\abc.exe --cases C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public --selector configs\final_selector_candidate.yaml --pipelines configs\pipelines_candidate.yaml --out results_candidate\r29_postpass_entry_full_public_candidate_config --csv reports\r29_candidate_entry_full_public_candidate_config.csv
```

Independent CEC:

```powershell
py -3 tools\verify_all_cec.py --abc submit\bin\abc.exe --cases C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public --outputs results_candidate\r29_postpass_entry_full_public_candidate_config --log logs\r29_candidate_entry_full_public_candidate_config_cec.log --timeout 300
```

## Input Data

- Public cases: `C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public`
- Baseline metrics: `reports/final_metrics.csv`
- Candidate metrics: `reports/r29_candidate_entry_full_public_candidate_config.csv`
- Candidate summary: `reports/r29_candidate_entry_candidate_config_summary.json`
- Independent CEC log: `logs/r29_candidate_entry_full_public_candidate_config_cec.log`

## Results

| Metric | v6 baseline | R29 candidate | Delta |
| --- | ---: | ---: | ---: |
| Total nodes | `37464` | `37260` | `-204` |
| Level sum | `278` | `277` | `-1` |
| Max level | `20` | `20` | `0` |
| CEC pass | `30/30` | `30/30` | `0` |
| Fallback | `0` | `0` | `0` |
| Bad entry return code | `0` | `0` | `0` |
| Inner fallback | `0` | `0` | `0` |
| Wins/ties/losses vs v6 | n/a | `9/21/0` | n/a |
| Gain excluding best case | n/a | `147` | n/a |
| Gain excluding top two cases | n/a | `111` | n/a |
| Total opt time | `76.225724s` | `105.041315s` | `+28.815591s` |
| Total CEC time | `55.517710s` | `64.621365s` | `+9.103655s` |
| Total stats time | `12.622708s` | `13.825113s` | `+1.202405s` |
| Peak RSS | `47.309 MB` | `47.184 MB` | `-0.125 MB` |

Accepted R29 cases:

| Case | Node delta | Level delta | Gate |
| --- | ---: | ---: | --- |
| `tc_public_12` | `-3` | `0` | `medium_runtime_fraig_cleanup` |
| `tc_public_14` | `-29` | `-1` | `r7b_high_overlap_guarded_fraig` |
| `tc_public_15` | `-9` | `0` | `r7b_high_overlap_guarded_fraig` |
| `tc_public_18` | `-3` | `0` | `medium_runtime_fraig_cleanup` |
| `tc_public_19` | `-27` | `0` | `large_smallpo_fraig_cleanup` |
| `tc_public_20` | `-33` | `0` | `large_smallpo_fraig_cleanup` |
| `tc_public_21` | `-36` | `0` | `large_smallpo_fraig_cleanup` |
| `tc_public_22` | `-57` | `0` | `large_smallpo_fraig_cleanup` |
| `tc_public_23` | `-7` | `0` | `r11_deepsyn_medium_tiny_po` |

Rejected R29 attempts:

| Case | Gate | Reject reason |
| --- | --- | --- |
| `tc_public_11` | `medium_runtime_fraig_cleanup` | `no_node_gain` |
| `tc_public_13` | `r7b_high_overlap_guarded_fraig` | `no_node_gain` |

## Correctness

- Candidate entry full public run: `30/30` CEC.
- Independent CEC from candidate output directory: `30/30`.
- Fallback count: `0`.
- Entry return-code failures: `0`.
- R29 post-pass CEC failures: `0`.
- R29 timeouts: `0`.
- R29 accepted outputs are rechecked after copying to final output.

## Risk

The main cost is runtime. The candidate adds about `39.121651s` total
opt+CEC+stats time on the public set versus v6. This is much smaller than the
unconditional matrix path because the online candidate only attempts R29 on
coarse eligible buckets, but it is still a real release tradeoff.

The selector-risk profile is acceptable for candidate evaluation because the
rules use existing coarse selector reasons rather than filenames, hashes, exact
public IDs, or exact public fingerprints.

## Selector Eligibility

The candidate passes the hard candidate gates:

- CEC `30/30`
- fallback `0`
- crash/timeout/CEC fail `0/0/0`
- selected nodes below formal baseline
- max level `20 <= 25`
- gain excluding best case positive
- gain excluding top two cases positive
- at least three stable gain cases
- no public-case-specific selector condition

The only promotion concern is runtime overhead. Because the official scoring
emphasizes ranking and not a direct public opt-time penalty in the observed
rules, this candidate is worth release packaging only if the team accepts the
extra runtime margin.

## Conclusion

Decision label: `promote-to-candidate`.

R29 should be treated as a verified candidate entrypoint. It improves v6 by
`204` nodes with no public losses, no level regression, no CEC failures, no
fallbacks, and independent CEC `30/30`.

It should not overwrite `submit/` or `submit_sharecone.zip` until the user
explicitly approves release packaging.

## Next Action

If approved, enter release packaging from `candidate/r29-postpass-entry`, promote
the candidate entrypoint/config to formal release paths, package once, compute
SHA256, and verify packaged CEC from inside `submit/`.
