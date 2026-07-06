---
research_id: R8-PACKAGING-EXPLICIT-REPORTS
status: candidate-ready
baseline_tag: final_selector_v2_20260526
baseline_commit: 0b0edf4890283e36fac943166a8c84a148c120b8
branch: release/r8-preflight
created: 2026-06-22
updated: 2026-06-22
affects_final: false
supersedes:
  - reports/r8_packaging_scratch_dry_run.md
superseded_by: []
primary_data:
  - reports/r8_packaging_explicit_reports_manifest.csv
  - logs/r8_packaging_explicit_reports_cec.log
  - reports/r8_formal_names_preflight_metrics.csv
  - reports/r8_packaging_failure_cases.md
  - reports/r8_packaging_final_scoreboard.xlsx
---

# R8 Explicit-Report Package Dry Run

## Objective

Remove the last known scratch-packaging mismatch: the previous package dry run
proved packaged CEC, but `tools/package_submit.py` copied old formal report
paths by default, so the scratch package contained old `45870/25` report files.
This dry run updates the candidate packaging script to accept explicit report
inputs, then verifies a non-formal scratch package whose runtime and report
files are both R8.

No official `submit/` directory or `submit_sharecone.zip` was generated or
overwritten.

## Baseline

- Formal baseline tag: `final_selector_v2_20260526`
- Formal public result: `45870` nodes, max level `25`, CEC `30/30`,
  fallback `0`
- R8 candidate result: `43775` nodes, max level `21`, CEC `30/30`,
  fallback `0`

## Commands

Generate R8 failure report:

```powershell
C:\Users\yy257\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe tools\generate_failure_cases.py --metrics reports\r8_formal_names_preflight_metrics.csv --out reports\r8_packaging_failure_cases.md
```

Generate R8 scoreboard:

```powershell
# xlsxwriter-based workbook generated from reports\r8_formal_names_preflight_metrics.csv
# output: reports\r8_packaging_final_scoreboard.xlsx
```

Create scratch package with explicit R8 reports:

```powershell
C:\Users\yy257\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe tools\package_submit.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --config configs\final_selector.yaml --pipelines configs\pipelines.yaml --results results_candidate\r8_formal_names_preflight\public30 --metrics reports\r8_formal_names_preflight_metrics.csv --scoreboard reports\r8_packaging_final_scoreboard.xlsx --cec-log logs\r8_formal_names_preflight_cec.log --failure-cases reports\r8_packaging_failure_cases.md --out results_candidate\r8_packaging_explicit_reports_dry_run_20260622\submit_like
```

Run packaged CEC:

```powershell
C:\Users\yy257\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe tools\reproduce_submit.py --submit results_candidate\r8_packaging_explicit_reports_dry_run_20260622\submit_like --cases local_data\tc_public --abc results_candidate\r8_packaging_explicit_reports_dry_run_20260622\submit_like\bin\abc.exe --log results_candidate\r8_packaging_explicit_reports_dry_run_20260622\submit_like\logs\reproduce_cec.log
```

Persist compact evidence and remove bulk scratch data:

```powershell
Copy-Item results_candidate\r8_packaging_explicit_reports_dry_run_20260622\submit_like\logs\reproduce_cec.log logs\r8_packaging_explicit_reports_cec.log
Remove-Item -Recurse -Force local_data
Remove-Item -Recurse -Force results_candidate\r8_packaging_explicit_reports_dry_run_20260622
```

## Input Data

- Candidate ABC SHA256:
  `85F59E6291A1C4B10B757BF163D14D2152EAA974B21BC6F4E13F44EC49969805`
- R8 metrics SHA256:
  `0AFA2CF60837A09B58FD2C5E1AEB9711DD2930936D9EE8A701D42FB9928C4BFF`
- R8 CEC log SHA256:
  `C3C6CB3372EC87F2EC871A247ABF70986E0EE553B54CF1B3034C72BEA63C2C5D`
- R8 failure report SHA256:
  `AEEB8E27436CD54252AE025D958B8F21BC4926AA108FABB0A39F57F0EED95545`
- R8 scoreboard SHA256:
  `D42FA539055F5B97DA377CAB2CD07F06B22BAB6242940F6D2C0FAE773FA8B26C`

## Results

`tools/package_submit.py` now supports these optional explicit report inputs:

- `--metrics`
- `--scoreboard`
- `--cec-log`
- `--failure-cases`

Defaults remain the old formal paths for backward compatibility.

| Check | Result |
| --- | ---: |
| scratch package files | `1732` |
| scratch package bytes | `70586973` |
| packaged output cases | `30` |
| packaged final metrics rows | `30` |
| packaged final metrics nodes | `43775` |
| packaged final metrics max level | `21` |
| packaged final metrics CEC pass | `30/30` |
| packaged final metrics fallback | `0` |
| packaged final scoreboard bytes | `8916` |
| packaged CEC equivalent count | `30` |
| packaged CEC NOT EQUIVALENT count | `0` |
| packaged non-`abc.rc` Cannot open count | `0` |

Hash checks confirm the scratch package copied the intended R8 artifacts:

- packaged ABC hash equals candidate ABC hash
- packaged final metrics hash equals R8 metrics hash
- packaged final CEC log hash equals R8 CEC log hash
- packaged failure report hash equals R8 failure report hash
- packaged scoreboard hash equals R8 scoreboard hash

## Correctness

The packaged CEC command returned success:

```text
all CEC checks passed; wrote results_candidate\r8_packaging_explicit_reports_dry_run_20260622\submit_like\logs\reproduce_cec.log
```

The persisted log `logs/r8_packaging_explicit_reports_cec.log` contains `30`
`Networks are equivalent` lines, `0` `NOT EQUIVALENT` lines, and `0`
non-`abc.rc` `Cannot open` messages.

## Risk

This dry run resolves the report-consistency risk found in the earlier scratch
package dry run. The remaining risks are only the protected release actions:

- official `submit/` has not been regenerated
- official `submit_sharecone.zip` has not been generated
- final SHA256 has not been computed
- final release tag has not been created

## Selector Eligibility

No selector logic changed. R8 still uses coarse structural predicates and
CEC-guarded declaration-order variants. The packaging change only affects which
already-verified report artifacts are copied into the package.

## Conclusion

Decision: `promote-to-candidate`

R8 now has a clean non-formal package dry run with both runtime correctness and
report consistency: package assembly works, packaged CEC is `30/30`, and the
package's `final_metrics.csv` reports R8's `43775` nodes and max level `21`.
This is the strongest pre-release evidence so far.

## Next Action

Ask the user for explicit approval to perform the official release packaging
sequence. If approved, use the explicit report arguments added here, generate
the protected `submit/`, verify packaged CEC, create one new
`submit_sharecone.zip`, record SHA256, and tag the final release.
