---
research_id: R8-PORT-ORDER
status: candidate-ready
baseline_tag: final_selector_v2_20260526
baseline_commit: 0b0edf4890283e36fac943166a8c84a148c120b8
branch: candidate/r8-integration
created: 2026-06-22
updated: 2026-06-22
affects_final: false
supersedes:
  - reports/r8_release_integration_readiness.md
superseded_by: []
primary_data:
  - reports/r8_release_like_ascii_metrics.csv
  - reports/r8_release_like_ascii_compare.csv
  - reports/r8_release_like_ascii_vs_formal.csv
  - logs/r8_release_like_ascii_cec.log
---

# R8 Release-Like Reproduction

## Objective

Integrate the R8 single-case order choose-best policy into the formal
`tools/optimize_one.py` entrypoint on a candidate integration branch, then
verify public 30 without modifying the formal main worktree, generating submit,
or overwriting `submit_sharecone.zip`.

## Baseline

- Formal baseline tag: `final_selector_v2_20260526`
- Formal commit: `0b0edf4890283e36fac943166a8c84a148c120b8`
- Formal public result: `45870` selected AIG nodes
- Formal max level: `25`
- Formal CEC: `30/30`
- Formal fallback: `0`

## Commands

Syntax checks:

```powershell
python -m py_compile tools\optimize_one.py tools\optimize_one_r8_order_choosebest.py tools\eval_public_optimize_one.py tools\eval_public_r8_order_choosebest_singlecase.py tools\extract_r7b_features.py tools\r7b_port_order_stress.py tools\package_submit.py
python tools\package_submit.py --help
```

Public 30 through the formal single-case entry:

```powershell
python tools\eval_public_optimize_one.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --cases local_data\tc_public --selector configs\final_selector_r8_candidate.yaml --pipelines configs\pipelines_r8_candidate.yaml --out results_candidate\r8_release_like_ascii\public30 --csv reports\r8_release_like_ascii_metrics.csv --opt-timeout 300 --cec-timeout 300 --stats-timeout 120
```

Independent CEC:

```powershell
python tools\verify_all_cec.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --cases local_data\tc_public --outputs results_candidate\r8_release_like_ascii\public30 --log logs\r8_release_like_ascii_cec.log --timeout 300
```

## Input Data

- Public cases copied to ASCII local path: `local_data/tc_public`
- ABC executable:
  `C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe`
- ABC SHA256:
  `85F59E6291A1C4B10B757BF163D14D2152EAA974B21BC6F4E13F44EC49969805`
- Candidate selector: `configs/final_selector_r8_candidate.yaml`
- Candidate pipelines: `configs/pipelines_r8_candidate.yaml`
- Candidate single-case entry: `tools/optimize_one.py`

An earlier attempt that referenced the public cases through the non-ASCII main
workspace path was terminated by the outer tool timeout while CEC was still
running. The final decision-grade run above uses the ASCII local copy and
completed normally.

## Results

| Metric | Formal v2 | R8 release-like |
| --- | ---: | ---: |
| selected nodes | `45870` | `43775` |
| node gain |  | `2095` |
| max level | `25` | `21` |
| CEC pass | `30/30` | `30/30` |
| fallback | `0` | `0` |
| inner fallback |  | `0` |
| bad entry/ABC return code |  | `0` |
| wins/ties/losses |  | `11/19/0` |
| gain excluding best case |  | `737` |
| gain excluding top two cases |  | `122` |
| total opt runtime |  | `343.45s` |
| max opt runtime |  | `121.79s` |
| max peak RSS |  | `52.19 MB` |

The release-like run exactly matched the previous R8 single-case candidate
evidence:

- node mismatches: `0/30`
- level mismatches: `0/30`
- chosen variant mismatches: `0/30`
- selected pipeline mismatches: `0/30`

Improving cases versus formal v2:

| case | formal nodes | release-like nodes | node delta | formal level | release-like level | chosen variant |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `tc_public_13` | `1058` | `1043` | `-15` | `13` | `13` | `clean` |
| `tc_public_14` | `3514` | `2156` | `-1358` | `25` | `16` | `outputs` |
| `tc_public_15` | `927` | `922` | `-5` | `11` | `11` | `clean` |
| `tc_public_18` | `498` | `495` | `-3` | `12` | `12` | `inputs` |
| `tc_public_19` | `5277` | `5268` | `-9` | `18` | `18` | `both` |
| `tc_public_20` | `5538` | `5523` | `-15` | `20` | `20` | `inputs` |
| `tc_public_21` | `5556` | `5532` | `-24` | `20` | `20` | `both` |
| `tc_public_22` | `11049` | `11001` | `-48` | `20` | `20` | `both` |
| `tc_public_26` | `1048` | `1046` | `-2` | `10` | `10` | `outputs` |
| `tc_public_3` | `109` | `108` | `-1` | `8` | `8` | `outputs` |
| `tc_public_30` | `5421` | `4806` | `-615` | `21` | `21` | `both` |

## Correctness

The release-like evaluator reports `cec_pass=True` for all 30 cases. The
independent verifier reports all CEC checks passed and wrote
`logs/r8_release_like_ascii_cec.log`. No `NOT EQUIVALENT`, output-open error,
crash, timeout, fallback, or bad return code was found in the decision-grade
run.

The candidate branch did not generate a submit archive. `submit/` and
`submit_sharecone.zip` are present from the base worktree, but they are not
modified in this candidate integration diff.

## Risk

Low remaining risk:

- The formal single-case entry now exercises the R8 policy directly.
- Package dependency gaps are addressed by including the R8 helper modules.
- The package script can copy a candidate pipeline file through `--pipelines`.

Medium remaining risk:

- A release branch still must merge the ABC `r7win` source delta and build the
  final no-pthread ABC binary.
- The final formal config names should only be replaced during an approved
  release phase.
- A packaged submit archive still needs separate reproduction from inside
  `submit/`.

## Selector Eligibility

R8 remains selector-eligible. It uses coarse structural `r7b_eligible`
diagnostics produced by `r7win -profile -diag` plus online CEC/node/level
choose-best among deterministic declaration-order variants. It does not use
file names, directory names, hashes, public case IDs, exact public fingerprints,
exact port names, or public discovery order as selector conditions.

## Conclusion

Decision: `promote-to-candidate`

R8 now passes release-like candidate reproduction through the formal
`tools/optimize_one.py` entrypoint: `43775` nodes, max level `21`, public CEC
`30/30`, fallback `0`, no broad losses, and exact agreement with prior
single-case R8 evidence.

## Next Action

Do not generate submit yet. The next step is to update the research index and
commit/tag this candidate integration evidence. After that, ask the user before
merging into the formal main/release branch or packaging a new submit archive.
