---
research_id: R7B-FRAIG-WINDOW
status: candidate-ready
baseline_tag: final_selector_v2_20260526
baseline_commit: 0b0edf4890283e36fac943166a8c84a148c120b8
branch: candidate/r7b-pure
created: 2026-06-22
updated: 2026-06-22
affects_final: false
supersedes: []
superseded_by: []
primary_data:
  - reports/r7b_rerun_20260622_metrics.csv
  - reports/r7b_rerun_20260622_diff.csv
  - logs/r7b_rerun_20260622_cec.log
  - results_candidate/r7b_rerun_20260622/features.csv
---

# R7b Candidate Rerun Reproduction

## Objective

Re-run the R7b ABC-native multi-output FRAIG/ODC window rewrite candidate from
the clean candidate worktree, without modifying the formal selector, formal
pipelines, submit directory, or submit archive.

## Baseline

- Formal baseline tag: `final_selector_v2_20260526`
- Formal commit: `0b0edf4890283e36fac943166a8c84a148c120b8`
- Formal nodes: `45870`
- Formal max level: `25`
- Formal CEC: `30/30`
- Formal fallback: `0`

## Commands

```powershell
python tools\extract_blif_features.py --cases data\tc_public --csv results_candidate\r7b_rerun_20260622\base_features.csv
python tools\extract_r7b_features.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --cases data\tc_public --base-features results_candidate\r7b_rerun_20260622\base_features.csv --csv results_candidate\r7b_rerun_20260622\features.csv --work-dir results_candidate\r7b_rerun_20260622\feature_profile --timeout 120
python tools\eval_public.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --cases data\tc_public --selector configs\final_selector_r7b_candidate.yaml --features results_candidate\r7b_rerun_20260622\features.csv --pipelines configs\pipelines_r7b_pure_candidate.yaml --out results_candidate\r7b_rerun_20260622\public30 --csv reports\r7b_rerun_20260622_metrics.csv --opt-timeout 300 --cec-timeout 300 --stats-timeout 120
python tools\verify_all_cec.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --cases data\tc_public --outputs results_candidate\r7b_rerun_20260622\public30 --log logs\r7b_rerun_20260622_cec.log --timeout 300
```

The local shell used the bundled Codex Python executable because `python` was
not on this PowerShell PATH.

## Input Data

- `data/tc_public/*/input.blif`
- `configs/final_selector_r7b_candidate.yaml`
- `configs/pipelines_r7b_pure_candidate.yaml`
- `results_candidate/r7b_rerun_20260622/base_features.csv`
- `results_candidate/r7b_rerun_20260622/features.csv`
- ABC executable:
  `C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe`
- ABC SHA256:
  `85F59E6291A1C4B10B757BF163D14D2152EAA974B21BC6F4E13F44EC49969805`

## Results

| Metric | Formal v2 | R7b rerun |
| --- | ---: | ---: |
| selected nodes | `45870` | `44559` |
| node delta |  | `-1311` |
| max level | `25` | `21` |
| CEC pass | `30/30` | `30/30` |
| fallback | `0` | `0` |
| wins/ties/losses |  | `3/27/0` |
| gain excluding best case |  | `20` |
| gain excluding top two cases |  | `5` |
| local level regressions |  | `0` |
| total opt runtime |  | `94.92s` |
| max opt runtime |  | `33.59s` |
| max peak RSS |  | `34.93 MB` |

Improving cases are unchanged from the clean reproduction:

| case | formal pipeline | candidate pipeline | nodes | levels |
| --- | --- | --- | ---: | ---: |
| `tc_public_13` | `dc2_fast` | `r7b_r7win_fraig_high` | `1058 -> 1043` | `13 -> 13` |
| `tc_public_14` | `high_aig_three_round` | `r7b_r7win_fraig_high` | `3514 -> 2223` | `25 -> 17` |
| `tc_public_15` | `dc2_fast` | `r7b_r7win_fraig_high` | `927 -> 922` | `11 -> 11` |

## Correctness

The evaluator reports `cec_pass=True` for all 30 cases, and the independent CEC
log reports 30 passed checks. The CEC log contains ABC startup messages saying
`Cannot open file "abc.rc"` and nearby parent rc paths; these are optional ABC
initialization files and not BLIF, output, or miter file failures. There are no
`NOT EQUIVALENT`, `passed=False`, optimization crashes, timeouts, or fallbacks.

## Risk

- The candidate requires the ABC build containing the `r7win` command.
- The candidate requires the generated `r7b_eligible` feature from
  `tools/extract_r7b_features.py`.
- This rerun does not package or test a submit archive.
- R8 port-order research files are present as separate untracked worktree
  evidence and are not part of this R7b rerun.

## Selector Eligibility

R7b remains selector-eligible. The rule uses the generated coarse
`r7b_eligible` overlap/cluster feature and does not use filenames, hashes,
`tc_public_xx`, exact public-set fingerprints, or exact port names. Prior
anonymized case-name, randomized case-name, and PI/PO port-name stresses all
reproduced the same `44559` selected nodes with mismatch count `0`.

## Conclusion

Decision: `promote-to-candidate`

This rerun confirms the R7b candidate result exactly: `44559` nodes, max level
`21`, CEC `30/30`, fallback `0`, wins/ties/losses `3/27/0`, positive
excluding-best and excluding-top-two gains, and no local level regression.

## Next Action

Ask the user before merging the ABC command, replacing the formal selector, or
generating a submit archive.
