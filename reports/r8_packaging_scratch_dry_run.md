---
research_id: R8-PACKAGING-SCRATCH-CEC
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
  - reports/r8_packaging_scratch_dry_run_manifest.csv
  - logs/r8_packaging_scratch_dry_run_cec.log
  - reports/r8_formal_names_preflight_metrics.csv
---

# R8 Scratch Package CEC Dry Run

## Objective

Verify that `tools/package_submit.py` can assemble the R8 runtime into a
non-formal scratch package directory and that the resulting packaged
`tools/verify_all_cec.py` plus packaged `bin/abc.exe` can reproduce public CEC.
This dry run intentionally avoids the protected `submit/` directory and does
not create or overwrite `submit_sharecone.zip`.

## Baseline

- Formal baseline tag: `final_selector_v2_20260526`
- Formal public result: `45870` selected AIG nodes, max level `25`
- Formal CEC: `30/30`
- R8 candidate evidence: `43775` selected AIG nodes, max level `21`, CEC
  `30/30`, fallback `0`

## Commands

Create a temporary ASCII public-case copy:

```powershell
New-Item -ItemType Directory -Force local_data | Out-Null
Copy-Item -Recurse -LiteralPath E:\...\data\tc_public -Destination local_data\tc_public
```

Create the non-formal scratch package:

```powershell
C:\Users\yy257\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe tools\package_submit.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --config configs\final_selector.yaml --pipelines configs\pipelines.yaml --results results_candidate\r8_formal_names_preflight\public30 --out results_candidate\r8_packaging_scratch_dry_run_20260622\submit_like
```

Run packaged CEC through the scratch package:

```powershell
C:\Users\yy257\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe tools\reproduce_submit.py --submit results_candidate\r8_packaging_scratch_dry_run_20260622\submit_like --cases local_data\tc_public --abc results_candidate\r8_packaging_scratch_dry_run_20260622\submit_like\bin\abc.exe --log results_candidate\r8_packaging_scratch_dry_run_20260622\submit_like\logs\reproduce_cec.log
```

Persist compact evidence and clean temporary bulk data:

```powershell
Copy-Item results_candidate\r8_packaging_scratch_dry_run_20260622\submit_like\logs\reproduce_cec.log logs\r8_packaging_scratch_dry_run_cec.log
Remove-Item -Recurse -Force local_data
Remove-Item -Recurse -Force results_candidate\r8_packaging_scratch_dry_run_20260622
```

## Input Data

- Candidate worktree: `C:\Users\yy257\cpipc_r8_release_preflight`
- Scratch package path used during run:
  `results_candidate/r8_packaging_scratch_dry_run_20260622/submit_like`
- Candidate ABC SHA256:
  `85F59E6291A1C4B10B757BF163D14D2152EAA974B21BC6F4E13F44EC49969805`
- Packaged scratch ABC SHA256:
  `85F59E6291A1C4B10B757BF163D14D2152EAA974B21BC6F4E13F44EC49969805`
- Packaged selector SHA256 equals candidate selector SHA256:
  `06F2B70FBA7F6E1528B8FA291C88AFB31382D85635EA2FD9D427247F4744BF8F`
- Packaged pipelines SHA256 equals candidate pipelines SHA256:
  `1E77CB18374559E8AC56EBCD6644427A908AE1A0926D609653F6CD1D3DF0F22B`

## Results

| Check | Result |
| --- | ---: |
| scratch package files | `1732` |
| scratch package bytes | `70576239` |
| packaged output cases | `30` |
| packaged CEC equivalent count | `30` |
| packaged CEC NOT EQUIVALENT count | `0` |
| packaged non-`abc.rc` Cannot open count | `0` |
| R8 source metrics cases | `30` |
| R8 source metrics nodes | `43775` |
| R8 source metrics max level | `21` |
| R8 source metrics CEC pass | `30/30` |
| R8 source metrics fallback | `0` |

The scratch package was not retained in Git because it duplicated the R8
outputs and included a copied ABC binary. The persistent evidence is the copied
CEC log plus `reports/r8_packaging_scratch_dry_run_manifest.csv`.

## Correctness

The packaged CEC command returned success and printed:

```text
all CEC checks passed; wrote results_candidate\r8_packaging_scratch_dry_run_20260622\submit_like\logs\reproduce_cec.log
```

The persisted log `logs/r8_packaging_scratch_dry_run_cec.log` contains `30`
`Networks are equivalent` lines, `0` `NOT EQUIVALENT` lines, and `0`
non-`abc.rc` `Cannot open` messages.

## Risk

This dry run proves the package runtime shape can reproduce CEC, but it is not
a final release package:

- The protected `submit/` directory was not modified.
- `submit_sharecone.zip` was not generated or overwritten.
- The scratch package copied the current formal report files, and those report
  files are still old v2 (`45870` nodes, max level `25`).
- A real release still must replace `reports/final_metrics.csv`,
  `logs/final_cec.log`, `reports/failure_cases.md`, and
  `reports/final_scoreboard.xlsx` with R8 final evidence before packaging.

## Selector Eligibility

No new selector risk was introduced. The scratch package used the same R8
formal-name selector and pipelines that already passed case-name and PI/PO
port-name stress tests.

## Conclusion

Decision: `promote-to-candidate`

R8 now has a non-formal packaged-runtime CEC dry run: `package_submit.py` can
assemble the R8 runtime into a scratch package and the packaged verifier plus
packaged ABC reproduce public CEC `30/30`. This strengthens the release case,
but it still does not replace the required user-approved formal packaging
phase.

## Next Action

Ask the user for explicit approval to perform the formal release packaging
sequence. If approved, regenerate formal R8 reports, package into the protected
`submit/` directory, verify packaged CEC, create one new `submit_sharecone.zip`,
record its SHA256, and tag the release.
