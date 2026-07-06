---
research_id: R7b
status: candidate-ready
baseline_tag: final_selector_v2_20260526
baseline_commit: 0b0edf4890283e36fac943166a8c84a148c120b8
branch: candidate/r7b-pure
created: 2026-06-22
updated: 2026-06-22
affects_final: false
primary_data:
  - reports/r30b_release_port_name_compare.csv
  - reports/r30b_release_port_name_metrics.csv
---

# R7b Port-Name Randomization Stress Summary

## Objective

Check whether the pure R7b candidate depends on primary input/output port names by rerunning full public 30 after deterministic PI/PO renaming.

## Baseline

The comparator is the clean R7b candidate reproduction in `reports/r7b_pure_clean_metrics.csv`: 44559 nodes, max level 21, CEC 30/30, fallback 0.

## Commands

```powershell
python tools\r7b_port_name_stress.py generate --cases data\tc_public --out data\tc_public_portname_r7b_stress --map-csv results_candidate\r7b_port_name_stress\port_rename_map.csv --seed 20260622 --clean
python tools\extract_blif_features.py --cases data\tc_public_portname_r7b_stress --csv results_candidate\r7b_port_name_stress\base_features.csv
python tools\extract_r7b_features.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --cases data\tc_public_portname_r7b_stress --base-features results_candidate\r7b_port_name_stress\base_features.csv --csv results_candidate\r7b_port_name_stress\features.csv --work-dir results_candidate\r7b_port_name_stress\feature_profile --timeout 120
python tools\eval_public.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --cases data\tc_public_portname_r7b_stress --selector configs\final_selector_r7b_candidate.yaml --features results_candidate\r7b_port_name_stress\features.csv --pipelines configs\pipelines_r7b_pure_candidate.yaml --out results_candidate\r7b_port_name_stress\public30 --csv reports\r7b_port_name_stress_metrics.csv --opt-timeout 300 --cec-timeout 300 --stats-timeout 120
python tools\verify_all_cec.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --cases data\tc_public_portname_r7b_stress --outputs results_candidate\r7b_port_name_stress\public30 --log logs\r7b_port_name_stress_cec.log --timeout 300
python tools\r7b_port_name_stress.py compare --clean-csv reports\r7b_pure_clean_metrics.csv --stress-csv reports\r7b_port_name_stress_metrics.csv --out-csv reports\r7b_port_name_stress_compare.csv --report reports\r7b_port_name_stress_summary.md
```

## Input Data

- Original cases: `data/tc_public/*/input.blif`
- Renamed cases: `data/tc_public_portname_r7b_stress/*/input.blif`
- Port map: `results_candidate/r7b_port_name_stress/port_rename_map.csv`

## Results

- Stress total nodes: `37097`
- Clean total nodes: `37097`
- Stress max level: `20`
- Clean max level: `20`
- Pipeline mismatches: `0`
- Node mismatches: `0`
- Level mismatches: `0`
- Stress CEC failures in evaluator CSV: `0`
- Stress fallback count: `0`

## Correctness

Each stress output is CEC-checked against its renamed input inside the evaluator; the independent CEC log is `logs/r7b_port_name_stress_cec.log`.

## Risk

This stress isolates PI/PO symbol changes while preserving case directories. It complements, rather than replaces, the earlier anonymized and randomized case-name stresses.

## Selector Eligibility

Strengthened if all mismatches are zero: R7b remains selected by generated structural overlap features, not primary port names or output names.

## Conclusion

promote-to-candidate

## Next Action

Stop at the user approval point before formal merge or submit packaging.
