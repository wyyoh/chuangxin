---
research_id: R22-R11S-EXTERNAL-CASES-DRYRUN
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
  - reports/r22_external_cases_dryrun_summary.json
  - reports/r22_external_cases_dryrun_metrics.csv
  - reports/r22_external_cases_dryrun_failure_cases.md
  - logs/r22_external_cases_dryrun_full_cec.log
  - logs/r22_external_cases_dryrun_zip_extract_cec.log
  - logs/r22_external_cases_dryrun_zip_extract_inside_cec.log
---

# R22 R11S External Cases Dry Run

## Objective

Validate the exact ASCII public-cases source path intended for formal R11S
packaging, without overwriting protected formal artifacts.

R21 showed that this worktree does not currently contain `local_data/tc_public`.
This run verifies that using
`C:\Users\yy257\cpipc_r9_large_smallpo\local_data\tc_public` directly is safe
for the full helper flow.

## Baseline

- Formal baseline: `final_selector_v3_20260622`
- Formal public metrics: `43775` nodes, max level `21`, CEC `30/30`,
  fallback `0`
- R11S expected metrics: `41004` nodes, max level `20`, CEC `30/30`,
  fallback `0`
- Protected formal archive hash after this dry run:
  `4B6236AF057009318EA50E39FFC43FFA3A74708B49A07C2F08FD386AB6D1AF8A`

## Commands

```powershell
py -3 tools\r11s_release_package.py --cases C:\Users\yy257\cpipc_r9_large_smallpo\local_data\tc_public --work-root scratch\r22_r11s_external_cases_dryrun
```

The command used the default helper mode, `dry-run`, so all generated package
artifacts stayed under:

```text
scratch\r22_r11s_external_cases_dryrun
```

## Input Data

- Cases source:
  `C:\Users\yy257\cpipc_r9_large_smallpo\local_data\tc_public`
- Case directories found: `30`
- Selector: `configs/final_selector.yaml`
- Pipelines: `configs/pipelines.yaml`
- ABC binary used by packaged flow: `submit/bin/abc.exe`

## Results

| Metric | Value |
| --- | ---: |
| Selected nodes | 41004 |
| Max level | 20 |
| Total levels | 285 |
| Evaluator CEC pass count | 30/30 |
| Fallback cases | 0 |
| Inner fallback count | 0 |
| Bad entries | 0 |
| Dry-run zip SHA256 | `410C6D249A34F6B65062A430DC1D3F936990D816BEEB0838D66226A77071A11A` |
| Formal zip SHA256 after run | `4B6236AF057009318EA50E39FFC43FFA3A74708B49A07C2F08FD386AB6D1AF8A` |

CEC layers:

| Layer | Passed entries | Bad markers |
| --- | ---: | ---: |
| full output CEC | 30 | 0 |
| extracted zip CEC from root | 30 | 0 |
| extracted zip CEC from package-local layout | 30 | 0 |

Copied evidence:

- `reports/r22_external_cases_dryrun_summary.json`
- `reports/r22_external_cases_dryrun_metrics.csv`
- `reports/r22_external_cases_dryrun_failure_cases.md`
- `logs/r22_external_cases_dryrun_full_cec.log`
- `logs/r22_external_cases_dryrun_zip_extract_cec.log`
- `logs/r22_external_cases_dryrun_zip_extract_inside_cec.log`

## Correctness

The dry-run helper reproduced the R11S metrics and passed all three CEC layers.
No fallback, bad entry, or CEC failure was recorded. The generated failure-case
report states that there are no unresolved CEC failures and no fallback-selected
cases.

ABC may print normal missing `abc.rc` startup notices in CEC logs; these were
not counted as bad markers. The audited bad-marker search found no
`NOT EQUIVALENT`, `failed`, or `Error` markers.

## Risk

This was still non-destructive. It created a scratch dry-run zip but did not
overwrite `submit/` or `submit_sharecone.zip`.

The remaining release risk is now limited to the explicit formal overwrite
operation itself.

## Selector Eligibility

Unchanged. This run validates release mechanics and input-path readiness only;
it does not change selector rules.

## Conclusion

promote-to-candidate

R11S remains release-ready. The exact external ASCII cases path works for the
full package dry-run flow and reproduces the expected metrics and CEC results.

## Next Action

If protected artifact overwrite is explicitly approved, the formal command can
use the validated cases path:

```powershell
py -3 tools\r11s_release_package.py --mode formal --cases C:\Users\yy257\cpipc_r9_large_smallpo\local_data\tc_public --confirm-overwrite-submit
```

Do not use stale `master` for the release path; R20 already stopped that route.
