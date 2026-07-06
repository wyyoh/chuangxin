---
research_id: R8-PORT-ORDER
status: candidate-ready
baseline_tag: final_selector_v2_20260526
baseline_commit: 0b0edf4890283e36fac943166a8c84a148c120b8
branch: candidate/r7b-pure
created: 2026-06-22
updated: 2026-06-22
affects_final: false
supersedes:
  - reports/r8_order_choosebest_online_summary.md
superseded_by: []
primary_data:
  - reports/r8_order_choosebest_singlecase_metrics.csv
  - reports/r8_order_choosebest_singlecase_compare.csv
  - reports/r8_order_choosebest_singlecase_portname_metrics.csv
  - reports/r8_order_choosebest_singlecase_portname_compare.csv
  - logs/r8_order_choosebest_singlecase_cec.log
  - logs/r8_order_choosebest_singlecase_portname_cec.log
---

# R8 Single-Case Order Choose-Best Candidate Summary

## Objective

Validate R8 as a candidate-level online strategy: for each input BLIF, generate
deterministic PI/PO declaration-order variants, optimize each with the same
selector-selected pipeline, CEC every output against the original input, and
choose the lowest-node level-safe result. This must not use filenames, public
case IDs, public ordering, hashes, exact fingerprints, or precomputed public
outputs.

## Baseline

- Formal baseline: `final_selector_v2_20260526`
- Formal nodes: `45870`
- Formal max level: `25`
- Formal CEC: `30/30`
- Formal fallback: `0`
- Clean R7b candidate: `44559` nodes, max level `21`, CEC `30/30`,
  fallback `0`

## Commands

Syntax check:

```powershell
python -m py_compile tools\optimize_one_r8_order_choosebest.py tools\eval_public_r8_order_choosebest_singlecase.py
```

Structure-diverse smoke:

```powershell
python tools\select_smoke_subset.py --features results_candidate\r7b_pure_clean\features.csv --final reports\r7b_rerun_20260622_metrics.csv --out results_candidate\r8_order_choosebest_singlecase\smoke_cases.csv
python tools\eval_public_r8_order_choosebest_singlecase.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --cases data\tc_public --case-list results_candidate\r8_order_choosebest_singlecase\smoke_cases.txt --selector configs\final_selector_r7b_candidate.yaml --pipelines configs\pipelines_r7b_pure_candidate.yaml --out results_candidate\r8_order_choosebest_singlecase\smoke_public --csv reports\r8_order_choosebest_singlecase_smoke_metrics.csv --opt-timeout 300 --cec-timeout 300 --stats-timeout 120
```

Full public 30 through the single-case interface:

```powershell
python tools\eval_public_r8_order_choosebest_singlecase.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --cases data\tc_public --selector configs\final_selector_r7b_candidate.yaml --pipelines configs\pipelines_r7b_pure_candidate.yaml --out results_candidate\r8_order_choosebest_singlecase\public30 --csv reports\r8_order_choosebest_singlecase_metrics.csv --opt-timeout 300 --cec-timeout 300 --stats-timeout 120
python tools\verify_all_cec.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --cases data\tc_public --outputs results_candidate\r8_order_choosebest_singlecase\public30 --log logs\r8_order_choosebest_singlecase_cec.log --timeout 300
```

Port-name stress:

```powershell
python tools\eval_public_r8_order_choosebest_singlecase.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --cases data\tc_public_portname_r7b_stress --selector configs\final_selector_r7b_candidate.yaml --pipelines configs\pipelines_r7b_pure_candidate.yaml --out results_candidate\r8_order_choosebest_singlecase_portname\public30 --csv reports\r8_order_choosebest_singlecase_portname_metrics.csv --opt-timeout 300 --cec-timeout 300 --stats-timeout 120
python tools\verify_all_cec.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --cases data\tc_public_portname_r7b_stress --outputs results_candidate\r8_order_choosebest_singlecase_portname\public30 --log logs\r8_order_choosebest_singlecase_portname_cec.log --timeout 300
```

The local shell used the bundled Codex Python executable because `python` was
not on this PowerShell PATH.

## Input Data

- Public cases: `data/tc_public/*/input.blif`
- Port-name stress cases: `data/tc_public_portname_r7b_stress/*/input.blif`
- Selector: `configs/final_selector_r7b_candidate.yaml`
- Pipelines: `configs/pipelines_r7b_pure_candidate.yaml`
- ABC executable: `C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe`
- ABC SHA256:
  `85F59E6291A1C4B10B757BF163D14D2152EAA974B21BC6F4E13F44EC49969805`

## Results

| Metric | Formal v2 | Clean R7b | R8 single-case |
| --- | ---: | ---: | ---: |
| selected nodes | `45870` | `44559` | `43775` |
| max level | `25` | `21` | `21` |
| CEC pass | `30/30` | `30/30` | `30/30` |
| fallback | `0` | `0` | `0` |
| wins/ties/losses vs formal |  | `3/27/0` | `11/19/0` |
| gain vs formal |  | `1311` | `2095` |
| gain excluding best vs formal |  | `20` | `737` |
| gain excluding top two vs formal |  | `5` | `122` |
| wins/ties/losses vs R7b |  |  | `9/21/0` |
| gain vs R7b |  |  | `784` |
| gain excluding best vs R7b |  |  | `169` |
| gain excluding top two vs R7b |  |  | `102` |
| local level regressions vs formal |  | `0` | `0` |
| local level regressions vs R7b |  |  | `0` |
| total opt runtime |  | `94.92s` | `344.26s` |
| max opt runtime |  | `33.59s` | `120.78s` |
| max peak RSS |  | `34.93 MB` | `52.14 MB` |

R8 single-case also improves over the earlier public-order online runner:
`43775` nodes versus `44267`, a further `492` node reduction. The earlier
runner is superseded because it used public discovery order as part of variant
generation; the single-case runner uses the same fixed variant index for every
input and is therefore the decision-grade R8 evidence.

Node-improving cases versus clean R7b:

| case | R7b nodes | R8 nodes | gain | level | variant |
| --- | ---: | ---: | ---: | ---: | --- |
| `tc_public_14` | `2223` | `2156` | `67` | `16` | `outputs` |
| `tc_public_18` | `498` | `495` | `3` | `12` | `inputs` |
| `tc_public_19` | `5277` | `5268` | `9` | `18` | `both` |
| `tc_public_20` | `5538` | `5523` | `15` | `20` | `inputs` |
| `tc_public_21` | `5556` | `5532` | `24` | `20` | `both` |
| `tc_public_22` | `11049` | `11001` | `48` | `20` | `both` |
| `tc_public_26` | `1048` | `1046` | `2` | `10` | `outputs` |
| `tc_public_3` | `109` | `108` | `1` | `8` | `outputs` |
| `tc_public_30` | `5421` | `4806` | `615` | `21` | `both` |

Port-name stress reproduced the same selected result exactly:

- stress nodes: `43775`
- node mismatches: `0/30`
- level mismatches: `0/30`
- variant mismatches: `0/30`
- pipeline mismatches: `0/30`
- independent CEC: `30/30`
- fallback/inner fallback/original-CEC-fail: `0/0/0`

## Correctness

The R8 single-case runner CEC-checks every attempted non-clean variant back
against the original input before it can be selected, then runs a final CEC on
the chosen output. The independent CEC logs report 30 passed checks for both
the clean public set and the port-name stress set. The logs contain ABC startup
messages about optional `abc.rc` files being absent; there are no
`NOT EQUIVALENT`, `passed=False`, `failed`, or `Error` diagnostics.

## Risk

- Runtime increases because each input runs clean, input-order, output-order,
  and both-order variants. The observed max optimization runtime is `120.78s`,
  under the `300s` per-optimization timeout, and max RSS is `52.14 MB`.
- Release packaging still needs explicit approval because the formal
  `tools/optimize_one.py`, `configs/final_selector.yaml`,
  `configs/pipelines.yaml`, and `submit_sharecone.zip` were not modified.
- The strategy relies on local CEC and metrics for final selection, so release
  notes must describe the online choose-best policy clearly.

## Selector Eligibility

Eligible. R8 uses one fixed variant policy for every input and chooses only by
local CEC, node count, and level safety. It does not use filenames, directory
names, hashes, public case IDs, exact public fingerprints, exact port names, or
public discovery order. The port-name stress result confirms the selected
nodes, levels, variants, and pipelines are independent of PI/PO symbol names on
the public set.

## Conclusion

Decision: `promote-to-candidate`

R8 single-case order choose-best is stronger than pure R7b and satisfies the
candidate evidence gates on the public set: `43775` nodes, max level `21`, CEC
`30/30`, fallback `0`, no crashes/timeouts observed, no level regressions,
positive gains excluding best and top-two cases, and nine stable gains over
R7b without losses.

## Next Action

Ask before formal integration. If approved, the next release branch should merge
the R7b ABC command plus the R8 single-case optimizer path into the formal
submission interface, then regenerate and verify a new submit archive exactly
once.
