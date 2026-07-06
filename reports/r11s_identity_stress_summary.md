---
research_id: R11S-GIA-DISTILLED-STABLE
status: candidate-ready
baseline_tag: final_selector_v3_20260622
baseline_commit: 7b20c8c4904682cd905f7afb68d5a4a822c4f8d6
branch: release/r11-preflight
created: 2026-06-23
updated: 2026-06-23
affects_final: false
supersedes: []
superseded_by: []
primary_data:
  - reports/r11s_random_case_name_stress_metrics.csv
  - reports/r11s_random_case_name_stress_compare.csv
  - reports/r11s_random_case_name_stress_summary.json
  - logs/r11s_random_case_name_stress_cec.log
  - reports/r11s_port_name_stress_metrics.csv
  - reports/r11s_port_name_stress_compare.csv
  - logs/r11s_port_name_stress_cec.log
---

# R11S Identity Stress Summary

## Objective

Verify that the R11S release-preflight selector does not depend on public case
directory names or exact primary input/output names.

## Baseline

- Clean R11S comparator: `reports/r11s_packaging_dryrun_full30_metrics.csv`
- Clean public result: `41004` nodes, max level `20`, CEC `30/30`,
  fallback `0`

## Commands

Random case-name stress:

```powershell
python <inline harness>  # writes reports\r11s_random_case_name_map.csv
python tools\eval_public_optimize_one.py --abc submit\bin\abc.exe --cases stress_data\r11s_random_case_names\cases --selector configs\final_selector.yaml --pipelines configs\pipelines.yaml --out results_candidate\r11s_random_case_name_stress\public30 --csv reports\r11s_random_case_name_stress_metrics.csv --opt-timeout 300 --cec-timeout 300 --stats-timeout 120
python tools\verify_all_cec.py --abc submit\bin\abc.exe --cases stress_data\r11s_random_case_names\cases --outputs results_candidate\r11s_random_case_name_stress\public30 --log logs\r11s_random_case_name_stress_cec.log --timeout 300
```

PI/PO port-name stress:

```powershell
python tools\r7b_port_name_stress.py generate --cases local_data\tc_public --out stress_data\r11s_port_name_stress\cases --map-csv reports\r11s_port_name_map.csv --seed 20260623 --clean
python tools\eval_public_optimize_one.py --abc submit\bin\abc.exe --cases stress_data\r11s_port_name_stress\cases --selector configs\final_selector.yaml --pipelines configs\pipelines.yaml --out results_candidate\r11s_port_name_stress\public30 --csv reports\r11s_port_name_stress_metrics.csv --opt-timeout 300 --cec-timeout 300 --stats-timeout 120
python tools\verify_all_cec.py --abc submit\bin\abc.exe --cases stress_data\r11s_port_name_stress\cases --outputs results_candidate\r11s_port_name_stress\public30 --log logs\r11s_port_name_stress_cec.log --timeout 300
python tools\r7b_port_name_stress.py compare --clean-csv reports\r11s_packaging_dryrun_full30_metrics.csv --stress-csv reports\r11s_port_name_stress_metrics.csv --out-csv reports\r11s_port_name_stress_compare.csv --report reports\r11s_port_name_stress_summary_raw.md
```

## Input Data

- Original public inputs: `local_data/tc_public/*/input.blif`
- Random case-name mapping: `reports/r11s_random_case_name_map.csv`
- Port-name mapping: `reports/r11s_port_name_map.csv`

## Results

| Stress | Nodes | Max level | CEC | Fallback | Node mismatches | Level mismatches | Pipeline mismatches | Variant mismatches |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Clean R11S | 41004 | 20 | 30/30 | 0 |  |  |  |  |
| Random case names | 41004 | 20 | 30/30 | 0 | 0/30 | 0/30 | 0/30 | 0/30 |
| PI/PO port names | 41004 | 20 | 30/30 | 0 | 0/30 | 0/30 | 0/30 | 0/30 |

Random case-name stress summary:

- `node_mismatches`: `0`
- `level_mismatches`: `0`
- `pipeline_mismatches`: `0`
- `variant_mismatches`: `0`
- `cec_failures`: `0`
- `fallback_count`: `0`
- `bad_entry`: `0`

Port-name stress summary:

- pipeline/node/level mismatches: `0/0/0`
- CEC failures: `0`
- fallback: `0`

## Correctness

Both stress runs passed independent CEC `30/30`. The stress outputs are
equivalent to their corresponding renamed inputs, and the per-case selector
choices match the clean R11S run exactly.

## Risk

These tests reduce public-identity overfit risk for case directory names and
PI/PO names. They do not prove hidden-set generalization and do not replace
the final packaged-submit verification.

## Selector Eligibility

Strengthened. R11S uses coarse structural features and online CEC-backed
choose-best behavior; exact case names and exact PI/PO names are not used for
selector decisions.

## Conclusion

promote-to-candidate

R11S is robust to randomized case directory names and PI/PO port-name
renaming on the public set. It remains eligible for release packaging after
explicit approval.

## Next Action

Proceed only to explicit release packaging if approved; otherwise stop at this
candidate-ready preflight state.
