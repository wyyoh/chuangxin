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
  - results_candidate/r7b_random_name_stress/random_case_map.csv
  - results_candidate/r7b_random_name_stress/features.csv
  - reports/r7b_random_name_stress_metrics.csv
  - reports/r7b_random_name_stress_compare.csv
  - logs/r7b_random_name_stress_cec.log
---

# R7b Randomized Case-Name Stress Summary

## Objective

Strengthen the anti-fingerprint evidence for pure R7b by rerunning the full
candidate flow on public circuits copied into fixed-seed random directory names
such as `case_j7dnjet36a`. Unlike the earlier `anon_013` stress, these names do
not preserve original public order in their lexical sort.

## Baseline

- Candidate baseline: `reports/r7b_pure_clean_metrics.csv`
- Candidate nodes: `44559`
- Candidate max level: `21`
- Candidate CEC: `30/30`
- Candidate fallback: `0`

## Commands

```powershell
python tools\extract_blif_features.py --cases data\tc_public_rand_r7b_stress --csv results_candidate\r7b_random_name_stress\base_features.csv
python tools\extract_r7b_features.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --cases data\tc_public_rand_r7b_stress --base-features results_candidate\r7b_random_name_stress\base_features.csv --csv results_candidate\r7b_random_name_stress\features.csv --work-dir results_candidate\r7b_random_name_stress\feature_profile --timeout 120
python tools\eval_public.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --cases data\tc_public_rand_r7b_stress --selector configs\final_selector_r7b_candidate.yaml --features results_candidate\r7b_random_name_stress\features.csv --pipelines configs\pipelines_r7b_pure_candidate.yaml --out results_candidate\r7b_random_name_stress\public30 --csv reports\r7b_random_name_stress_metrics.csv --opt-timeout 300 --cec-timeout 300 --stats-timeout 120
python tools\verify_all_cec.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --cases data\tc_public_rand_r7b_stress --outputs results_candidate\r7b_random_name_stress\public30 --log logs\r7b_random_name_stress_cec.log --timeout 300
```

## Input Data

- Random-name copy of `data/tc_public`, ignored by Git
- Mapping file: `results_candidate/r7b_random_name_stress/random_case_map.csv`

## Results

| Check | Result |
| --- | ---: |
| randomized cases | `30` |
| R7b-eligible randomized cases | `case_j7dnjet36a`, `case_plzua5wike`, `case_q85mtt9qhs` |
| pipeline mismatches vs clean run | `0` |
| node mismatches vs clean run | `0` |
| level mismatches vs clean run | `0` |
| randomized total nodes | `44559` |
| randomized max level | `21` |
| randomized CEC | `30/30` |
| randomized fallback | `0` |

## Correctness

`logs/r7b_random_name_stress_cec.log` passed all 30 CEC checks. The comparison
CSV shows exact pipeline, node, and level equality with the clean candidate after
applying the random-name mapping.

## Risk

This is still a public-circuit stress test, not a hidden-set proof. It does,
however, remove the strongest public-name/order concern: the candidate result is
stable under random directory names and changed lexical order.

## Selector Eligibility

Strengthened. R7b selection remains driven by generated structural overlap
features, not directory names, case order, hashes, or `tc_public_xx` identifiers.

## Conclusion

Decision: `promote-to-candidate`

Pure R7b passes randomized-name anti-fingerprint stress.

## Next Action

Keep as candidate evidence. Do not merge into the formal final or generate a
submit archive without explicit approval.
