---
research_id: R8-PORT-ORDER
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
  - reports/r8_order_choosebest_cli_smoke.csv
  - reports/r8_order_choosebest_singlecase_anon_metrics.csv
  - reports/r8_order_choosebest_singlecase_random_metrics.csv
  - reports/r8_order_choosebest_singlecase_casename_compare.csv
  - logs/r8_order_choosebest_cli_smoke_cec.log
  - logs/r8_order_choosebest_singlecase_anon_cec.log
  - logs/r8_order_choosebest_singlecase_random_cec.log
---

# R8 Single-Case Hardening Summary

## Objective

Add release-adjacent hardening evidence for the R8 single-case order
choose-best candidate without modifying the formal final selector, formal
pipelines, submit directory, or submit archive.

## Baseline

- Formal baseline: `final_selector_v2_20260526`, `45870` nodes, max level `25`,
  CEC `30/30`, fallback `0`
- R8 candidate evidence before this hardening: `43775` nodes, max level `21`,
  CEC `30/30`, fallback `0`

## Commands

CLI smoke:

```powershell
python tools\optimize_one_r8_order_choosebest.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --input data\tc_public\<case>\input.blif --output results_candidate\r8_order_choosebest_cli_smoke\<case>\output.blif --selector configs\final_selector_r7b_candidate.yaml --pipelines configs\pipelines_r7b_pure_candidate.yaml --work-dir results_candidate\r8_order_choosebest_cli_smoke\<case>\work --metrics-json results_candidate\r8_order_choosebest_cli_smoke\<case>\metrics.json --case-label input --variant-index 1 --opt-timeout 300 --cec-timeout 300 --stats-timeout 120
```

The CLI smoke covered representative high-gain and guard cases:
`tc_public_14`, `tc_public_30`, and `tc_public_3`. Each output was also checked
with a direct ABC CEC command.

Case-name/path stress:

```powershell
python tools\eval_public_r8_order_choosebest_singlecase.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --cases data\tc_public_anon_r7b_stress --selector configs\final_selector_r7b_candidate.yaml --pipelines configs\pipelines_r7b_pure_candidate.yaml --out results_candidate\r8_order_choosebest_singlecase_anon\public30 --csv reports\r8_order_choosebest_singlecase_anon_metrics.csv --opt-timeout 300 --cec-timeout 300 --stats-timeout 120
python tools\verify_all_cec.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --cases data\tc_public_anon_r7b_stress --outputs results_candidate\r8_order_choosebest_singlecase_anon\public30 --log logs\r8_order_choosebest_singlecase_anon_cec.log --timeout 300
python tools\eval_public_r8_order_choosebest_singlecase.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --cases data\tc_public_rand_r7b_stress --selector configs\final_selector_r7b_candidate.yaml --pipelines configs\pipelines_r7b_pure_candidate.yaml --out results_candidate\r8_order_choosebest_singlecase_random\public30 --csv reports\r8_order_choosebest_singlecase_random_metrics.csv --opt-timeout 300 --cec-timeout 300 --stats-timeout 120
python tools\verify_all_cec.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --cases data\tc_public_rand_r7b_stress --outputs results_candidate\r8_order_choosebest_singlecase_random\public30 --log logs\r8_order_choosebest_singlecase_random_cec.log --timeout 300
```

## Input Data

- Public cases: `data/tc_public/*/input.blif`
- Anonymous case-name stress: `data/tc_public_anon_r7b_stress/*/input.blif`
- Random case-name stress: `data/tc_public_rand_r7b_stress/*/input.blif`
- Anonymous map: `results_candidate/r7b_anon_stress/anon_case_map.csv`
- Random map: `results_candidate/r7b_random_name_stress/random_case_map.csv`
- Selector: `configs/final_selector_r7b_candidate.yaml`
- Pipelines: `configs/pipelines_r7b_pure_candidate.yaml`

## Results

CLI smoke:

- cases: `3`
- node mismatches versus full R8 public run: `0`
- level mismatches: `0`
- chosen-variant mismatches: `0`
- optimizer-reported CEC pass: `3/3`
- direct ABC CEC equivalence: `3/3`

Anonymous case-name stress:

- total nodes: `43775`
- max level: `21`
- runner CEC: `30/30`
- independent CEC: `30/30`
- fallback/inner fallback/original-CEC-fail: `0/0/0`

Random case-name stress:

- total nodes: `43775`
- max level: `21`
- runner CEC: `30/30`
- independent CEC: `30/30`
- fallback/inner fallback/original-CEC-fail: `0/0/0`

Combined clean-vs-stress comparison across anonymous and random sets:

- comparison rows: `60`
- clean total nodes: `43775`
- anonymous total nodes: `43775`
- random total nodes: `43775`
- node mismatches: `0`
- level mismatches: `0`
- chosen-variant mismatches: `0`
- selected-pipeline mismatches: `0`
- CEC pass in stress metrics: `60/60`
- fallback/inner fallback/original-CEC-fail: `0/0/0`

## Correctness

The CLI smoke output and both renamed-path output sets were independently
checked by ABC CEC. The CEC logs may contain optional `abc.rc` startup messages,
but there are no `NOT EQUIVALENT`, `passed=False`, `failed`, or `Error`
diagnostics in the checked logs.

## Risk

This hardening reduces filename, directory-name, and command-line-entry risk.
It does not by itself generate a formal release package. Runtime remains the
main R8 tradeoff: the candidate evaluates four deterministic variants per input
and relies on local CEC/metrics to choose the output.

## Selector Eligibility

Strengthened. The single-case CLI uses `case-label input` and fixed
`variant-index 1`, and the full anonymous/random case-name stresses reproduced
the clean public R8 result exactly. This supports the claim that the R8
candidate does not select by public case names, directory names, or public
discovery order.

## Conclusion

Decision: `promote-to-candidate`

R8 remains stronger than R7b and now has direct CLI, anonymous case-name, and
random case-name hardening evidence. It is still not merged into the formal
final and no submit archive has been generated.

## Next Action

Ask for approval before formal integration. If approved, merge R7b ABC support
and the R8 single-case policy into a release branch, then run the formal
candidate reproduction and packaging gates.
