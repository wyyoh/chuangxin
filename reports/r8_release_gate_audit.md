---
research_id: R8-RELEASE-GATE-AUDIT
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
  - reports/r8_formal_names_preflight_metrics.csv
  - reports/r8_formal_names_preflight_vs_formal.csv
  - reports/r8_formal_names_preflight_compare.csv
  - logs/r8_formal_names_preflight_cec.log
  - reports/r8_formal_names_random_case_stress_metrics.csv
  - reports/r8_formal_names_random_case_stress_compare.csv
  - logs/r8_formal_names_random_case_stress_cec.log
  - reports/r8_formal_names_port_name_stress_metrics.csv
  - reports/r8_formal_names_port_name_stress_compare.csv
  - logs/r8_formal_names_port_name_stress_cec.log
---

# R8 Release Gate Audit

## Objective

Audit whether the R8 formal-name preflight candidate is ready to ask for user
approval to merge into the formal final and enter release packaging. This audit
does not modify the main formal final and does not generate a submit archive.

## Baseline

- Formal baseline tag: `final_selector_v2_20260526`
- Formal commit: `0b0edf4890283e36fac943166a8c84a148c120b8`
- Formal public result: `45870` selected AIG nodes, max level `25`
- Formal correctness: CEC `30/30`
- Formal safety: fallback `0`, crash/timeout/CEC fail `0/0/0`
- Formal submit SHA256:
  `f2d23df5ce280304ea3c18f8c713afbf06577a31e2ba8b3e11e5d2c2b00b8fad`

## Commands

Formal-name public 30:

```powershell
python tools\eval_public_optimize_one.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --cases local_data\tc_public --selector configs\final_selector.yaml --pipelines configs\pipelines.yaml --out results_candidate\r8_formal_names_preflight\public30 --csv reports\r8_formal_names_preflight_metrics.csv --opt-timeout 300 --cec-timeout 300 --stats-timeout 120
```

Formal-name independent CEC:

```powershell
python tools\verify_all_cec.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --cases local_data\tc_public --outputs results_candidate\r8_formal_names_preflight\public30 --log logs\r8_formal_names_preflight_cec.log --timeout 300
```

Hidden-style robustness checks:

```powershell
python tools\eval_public_optimize_one.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --cases stress_data\r8_random_case_names\cases --selector configs\final_selector.yaml --pipelines configs\pipelines.yaml --out results_candidate\r8_formal_names_random_case_stress\public30 --csv reports\r8_formal_names_random_case_stress_metrics.csv --opt-timeout 300 --cec-timeout 300 --stats-timeout 120
python tools\verify_all_cec.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --cases stress_data\r8_random_case_names\cases --outputs results_candidate\r8_formal_names_random_case_stress\public30 --log logs\r8_formal_names_random_case_stress_cec.log --timeout 300

python tools\r7b_port_name_stress.py generate --cases <main-workspace>\data\tc_public --out stress_data\r8_port_name_stress\cases --map-csv reports\r8_formal_names_port_name_map.csv --seed 20260622 --clean
python tools\eval_public_optimize_one.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --cases stress_data\r8_port_name_stress\cases --selector configs\final_selector.yaml --pipelines configs\pipelines.yaml --out results_candidate\r8_formal_names_port_name_stress\public30 --csv reports\r8_formal_names_port_name_stress_metrics.csv --opt-timeout 300 --cec-timeout 300 --stats-timeout 120
python tools\verify_all_cec.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --cases stress_data\r8_port_name_stress\cases --outputs results_candidate\r8_formal_names_port_name_stress\public30 --log logs\r8_formal_names_port_name_stress_cec.log --timeout 300
```

## Input Data

- Candidate worktree: `C:\Users\yy257\cpipc_r8_release_preflight`
- Candidate commit: `4dec903590f2d36a10b7249895cf16ed86c76617`
- Candidate tag: `candidate_r8_port_name_stress_20260622`
- ABC executable: `C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe`
- ABC SHA256:
  `85F59E6291A1C4B10B757BF163D14D2152EAA974B21BC6F4E13F44EC49969805`
- Formal-name selector: `configs/final_selector.yaml`
- Formal-name pipelines: `configs/pipelines.yaml`

## Results

| Metric | Formal v2 | R8 formal-name preflight |
| --- | ---: | ---: |
| selected nodes | `45870` | `43775` |
| node gain |  | `2095` |
| relative node reduction |  | `4.57%` |
| max level | `25` | `21` |
| CEC pass | `30/30` | `30/30` |
| fallback | `0` | `0` |
| inner fallback |  | `0` |
| bad optimize/CEC/entry return code |  | `0/0/0` |
| wins/ties/losses |  | `11/19/0` |
| gain excluding best case |  | `737` |
| gain excluding top two cases |  | `122` |
| local level regressions |  | `0` |
| total opt runtime |  | `428.36s` |
| max opt runtime |  | `135.46s` |
| max peak RSS |  | `52.14 MB` |

The winning cases are `tc_public_3`, `tc_public_13`, `tc_public_14`,
`tc_public_15`, `tc_public_18`, `tc_public_19`, `tc_public_20`,
`tc_public_21`, `tc_public_22`, `tc_public_26`, and `tc_public_30`. These names
are audit labels only; the selector does not use them.

| Robustness run | Nodes | Max level | CEC | Fallback | Inner fallback | Bad return code | Mismatch vs clean preflight |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean formal-name preflight | `43775` | `21` | `30/30` | `0` | `0` | `0` | reference |
| random case-name stress | `43775` | `21` | `30/30` | `0` | `0` | `0` | `0/30` nodes, levels, variants, pipelines |
| PI/PO port-name stress | `43775` | `21` | `30/30` | `0` | `0` | `0` | `0/30` nodes, levels, variants, pipelines |

## Correctness

All three independent CEC logs report `30` occurrences of `Networks are
equivalent`, `0` occurrences of `NOT EQUIVALENT`, and `0` non-`abc.rc`
`Cannot open` messages. ABC prints startup attempts to load `abc.rc`; these are
benign environment messages and not BLIF/output-open failures.

The formal-name evaluator CSV has `0` rows with failed CEC, nonzero optimize
return code, nonzero CEC return code, nonzero entry return code, inner fallback,
or fallback reason. No submit archive was generated, and the formal
`submit_sharecone.zip` was not modified.

## Risk

Release packaging is still pending by policy. The candidate has not yet been
merged into the main formal final, `submit/` has not been regenerated, and the
new `submit_sharecone.zip` SHA256 has not been computed. Packaged CEC from
inside `submit/` is therefore not yet proven.

The remaining risks are release-management risks rather than algorithmic public
set risks:

- verifying the exact no-pthread ABC binary to package
- creating the release branch from the approved candidate
- generating the submit archive exactly once
- computing and recording the new SHA256
- reproducing CEC from the packaged `submit/` layout

## Selector Eligibility

The formal-name selector uses coarse structural predicates only:
`r7b_eligible`, `scale_grade_in`, `high_fanin_sop`, `near_two_input_aig`, and
`runtime_size_bin_in`. It does not use file names, directory names, hashes,
`tc_public_xx`, exact public fingerprints, exact port names, or exact
PI/PO/name combinations.

The R8 choose-best layer uses deterministic declaration-order variants
(`clean`, `inputs`, `outputs`, `both`) and accepts a variant only after CEC
against the original input plus a level-safe node comparison. The public
evaluator passes a constant `--case-label input`; case names are kept only in
CSV/report rows for audit.

Random case-name stress and PI/PO port-name stress both reproduce the same
per-case node, level, variant, and pipeline choices as the clean formal-name
preflight, which directly supports hidden-set eligibility.

## Conclusion

Decision: `promote-to-candidate`

R8 has enough evidence to ask for explicit user approval to enter the formal
merge and release-packaging phase. It improves the current formal baseline by
`2095` nodes while lowering max level from `25` to `21`, keeps CEC at `30/30`,
has fallback `0`, has no public losses, keeps gains positive after excluding
the best and top two cases, and passes both case-name and PI/PO port-name
hidden-style stress tests.

R8 is not yet a new formal final because release packaging has not been
approved or executed.

## Next Action

Ask the user whether to promote R8 into the formal release branch and generate a
new submit package. If approval is not granted, keep
`final_selector_v2_20260526` as the formal final and keep R8 as the strongest
candidate-ready evidence line.
