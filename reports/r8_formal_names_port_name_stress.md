---
research_id: R8-PORT-ORDER
status: candidate-ready
baseline_tag: final_selector_v2_20260526
baseline_commit: 0b0edf4890283e36fac943166a8c84a148c120b8
branch: release/r8-preflight
created: 2026-06-22
updated: 2026-06-22
affects_final: false
supersedes: []
superseded_by: []
primary_data:
  - reports/r8_formal_names_port_name_map.csv
  - reports/r8_formal_names_port_name_stress_metrics.csv
  - reports/r8_formal_names_port_name_stress_compare.csv
  - logs/r8_formal_names_port_name_stress_cec.log
---

# R8 Formal-Names Port-Name Stress

## Objective

Verify that the R8 release-preflight layout does not depend on primary
input/output symbol names or port-name combinations. The stress run renames
every public-case PI/PO symbol to deterministic neutral names, then reruns
public 30 through the formal config filenames.

## Baseline

- Formal baseline tag: `final_selector_v2_20260526`
- Formal public result: `45870` nodes, max level `25`, CEC `30/30`,
  fallback `0`
- R8 formal-name preflight: `43775` nodes, max level `21`, CEC `30/30`,
  fallback `0`

## Commands

Generate deterministic PI/PO-renamed inputs:

```powershell
python tools\r7b_port_name_stress.py generate --cases <main-workspace>\data\tc_public --out stress_data\r8_port_name_stress\cases --map-csv reports\r8_formal_names_port_name_map.csv --seed 20260622 --clean
```

Run the stress:

```powershell
python tools\eval_public_optimize_one.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --cases stress_data\r8_port_name_stress\cases --selector configs\final_selector.yaml --pipelines configs\pipelines.yaml --out results_candidate\r8_formal_names_port_name_stress\public30 --csv reports\r8_formal_names_port_name_stress_metrics.csv --opt-timeout 300 --cec-timeout 300 --stats-timeout 120
```

Independent CEC:

```powershell
python tools\verify_all_cec.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --cases stress_data\r8_port_name_stress\cases --outputs results_candidate\r8_formal_names_port_name_stress\public30 --log logs\r8_formal_names_port_name_stress_cec.log --timeout 300
```

## Input Data

The stress input generator renames only primary input/output symbols in
`.inputs`, `.outputs`, `.names`, and `.latch` records. Internal nodes and logic
are preserved. The deterministic mapping is recorded in
`reports/r8_formal_names_port_name_map.csv`. The temporary stress input copy was
not committed after the run.

## Results

| Metric | R8 formal-name clean | R8 port-name stress |
| --- | ---: | ---: |
| selected nodes | `43775` | `43775` |
| max level | `21` | `21` |
| CEC pass | `30/30` | `30/30` |
| fallback | `0` | `0` |
| inner fallback | `0` | `0` |
| bad entry/ABC return code | `0` | `0` |
| total opt runtime | `428.36s` | `438.05s` |
| max opt runtime | `135.46s` | `158.15s` |
| max peak RSS | `52.14 MB` | `52.11 MB` |

Comparison against the clean formal-name preflight:

- node mismatches: `0/30`
- level mismatches: `0/30`
- chosen variant mismatches: `0/30`
- selected pipeline mismatches: `0/30`

## Correctness

The stress evaluator reports `cec_pass=True` for all 30 PI/PO-renamed cases.
The independent verifier reports all checks passed and wrote
`logs/r8_formal_names_port_name_stress_cec.log`. No `NOT EQUIVALENT`,
output-open error, crash, timeout, fallback, or bad return code was found.

## Risk

This stress reduces public-fingerprint risk related to exact PI/PO names and
port-name combinations. It does not replace final packaged-submit verification.
No submit archive was generated, and `submit_sharecone.zip` was not modified.

## Selector Eligibility

The result supports selector eligibility: the same node/level/variant/pipeline
choices are obtained after every primary input/output symbol is renamed. The
selector still uses coarse structural features and online CEC/node/level
choose-best only.

## Conclusion

Decision: `promote-to-candidate`

R8 formal-name preflight is robust to PI/PO port-name renaming: full public 30
remains `43775` nodes, max level `21`, CEC `30/30`, fallback `0`, and exactly
matches the clean formal-name preflight per case.

## Next Action

Ask the user before merging into the formal final or generating a submit
archive. The remaining work is release packaging and packaged CEC reproduction
after explicit approval.
