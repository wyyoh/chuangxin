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
  - results_candidate/r7b_anon_stress/anon_case_map.csv
  - results_candidate/r7b_anon_stress/features.csv
  - reports/r7b_anon_stress_metrics.csv
  - reports/r7b_anon_stress_compare.csv
  - logs/r7b_anon_stress_cec.log
---

# R7b Anonymized Case-Name Stress Summary

## Objective

Verify that the pure R7b candidate does not depend on public case directory
names such as `tc_public_13`. The stress test copies the same BLIF inputs into
anonymous directories (`anon_001` ... `anon_030`), regenerates features, reruns
the selector, and compares results after mapping back to the original order.

## Baseline

- Formal baseline: `final_selector_v2_20260526`
- Candidate baseline: `reports/r7b_pure_clean_metrics.csv`
- Candidate nodes: `44559`
- Candidate max level: `21`
- Candidate CEC: `30/30`
- Candidate fallback: `0`

## Commands

```powershell
python tools\extract_blif_features.py --cases data\tc_public_anon_r7b_stress --csv results_candidate\r7b_anon_stress\base_features.csv
python tools\extract_r7b_features.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --cases data\tc_public_anon_r7b_stress --base-features results_candidate\r7b_anon_stress\base_features.csv --csv results_candidate\r7b_anon_stress\features.csv --work-dir results_candidate\r7b_anon_stress\feature_profile --timeout 120
python tools\eval_public.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --cases data\tc_public_anon_r7b_stress --selector configs\final_selector_r7b_candidate.yaml --features results_candidate\r7b_anon_stress\features.csv --pipelines configs\pipelines_r7b_pure_candidate.yaml --out results_candidate\r7b_anon_stress\public30 --csv reports\r7b_anon_stress_metrics.csv --opt-timeout 300 --cec-timeout 300 --stats-timeout 120
python tools\verify_all_cec.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --cases data\tc_public_anon_r7b_stress --outputs results_candidate\r7b_anon_stress\public30 --log logs\r7b_anon_stress_cec.log --timeout 300
```

## Input Data

- Anonymous copy of `data/tc_public`, ignored by Git
- Mapping file: `results_candidate/r7b_anon_stress/anon_case_map.csv`

## Results

| Check | Result |
| --- | ---: |
| anonymized cases | `30` |
| R7b-eligible anonymized cases | `anon_013`, `anon_014`, `anon_015` |
| pipeline mismatches vs clean run | `0` |
| node mismatches vs clean run | `0` |
| level mismatches vs clean run | `0` |
| anonymized total nodes | `44559` |
| anonymized max level | `21` |
| anonymized CEC | `30/30` |
| anonymized fallback | `0` |

## Correctness

The independent CEC log `logs/r7b_anon_stress_cec.log` passed all 30 cases.
`reports/r7b_anon_stress_compare.csv` shows exact pipeline/node/level equality
with the clean non-anonymized candidate run after applying the mapping.

## Risk

This is not a hidden-set substitute: the circuits are still public circuits.
However, it directly checks that the current selector/tool flow does not require
the public directory names to produce the candidate result.

## Selector Eligibility

Strengthened. The only R7b selector input is the generated coarse
`r7b_eligible` feature. Anonymous directory names reproduce the same selected
R7b bucket and metrics, so there is no observed dependency on `tc_public_xx`.

## Conclusion

Decision: `promote-to-candidate`

The pure R7b candidate passes the anonymized case-name stress test.

## Next Action

Keep this as candidate evidence. Do not merge into the formal final or generate
a submit archive without explicit approval.
