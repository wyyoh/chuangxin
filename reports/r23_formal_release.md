---
research_id: R23-R11S-FORMAL-RELEASE
status: promoted
baseline_tag: final_selector_v3_20260622
baseline_commit: 7b20c8c4904682cd905f7afb68d5a4a822c4f8d6
branch: release/r11-preflight
created: 2026-06-23
updated: 2026-06-23
affects_final: true
supersedes:
  - R11S-GIA-DISTILLED-STABLE
  - R21-R11S-FORMAL-PACKAGING-GUARD
  - R22-R11S-EXTERNAL-CASES-DRYRUN
superseded_by: []
primary_data:
  - current_final_manifest.json
  - reports/r23_formal_release_summary.json
  - reports/final_metrics.csv
  - reports/final_scoreboard.xlsx
  - reports/failure_cases.md
  - logs/final_cec.log
  - logs/r23_formal_initial_failure_stdout.log
  - logs/r23_formal_initial_failure_stderr.log
  - logs/r23_formal_recovery_stdout.log
  - logs/r11s_formal_zip_extract_cec.log
  - logs/r11s_formal_zip_extract_inside_cec.log
  - submit/logs/reproduce_cec.log
  - submit/logs/reproduce_cec_inside.log
  - logs/r23_final_zip_extract_cec.log
  - logs/r23_final_zip_extract_inside_cec.log
---

# R23 R11S Formal Release

## Objective

Promote the R11S candidate to the new formal CPIPC Problem 10 submission by
overwriting `submit/` and `submit_sharecone.zip`, then verify the packaged
archive from multiple layouts.

The user explicitly approved this protected-artifact overwrite.

## Baseline

- Previous formal tag: `final_selector_v3_20260622`
- Previous formal commit: `7b20c8c4904682cd905f7afb68d5a4a822c4f8d6`
- Previous metrics: `43775` nodes, max level `21`, CEC `30/30`, fallback `0`
- Previous submit SHA256:
  `4B6236AF057009318EA50E39FFC43FFA3A74708B49A07C2F08FD386AB6D1AF8A`

## Commands

Initial formal attempt:

```powershell
py -3 tools\r11s_release_package.py --mode formal --cases C:\Users\yy257\cpipc_r9_large_smallpo\local_data\tc_public --confirm-overwrite-submit
```

That attempt failed because formal mode rebuilds `submit/`, while the default
ABC path was `submit\bin\abc.exe`.

Successful recovery:

```powershell
py -3 tools\r11s_release_package.py --mode formal --cases C:\Users\yy257\cpipc_r9_large_smallpo\local_data\tc_public --abc C:\Users\yy257\cpipc_r9_large_smallpo\submit\bin\abc.exe --confirm-overwrite-submit --allow-dirty
```

The dirty worktree allowance was used only after the failed first attempt had
already removed formal paths. The recovery reran the full public evaluation and
packaging flow from scratch.

Additional package-local verification:

```powershell
py -3 submit\tools\verify_all_cec.py --abc submit\bin\abc.exe --cases C:\Users\yy257\cpipc_r9_large_smallpo\local_data\tc_public --outputs submit\results\final_public --log submit\logs\reproduce_cec.log --timeout 300
```

From inside `submit/`:

```powershell
py -3 tools\verify_all_cec.py --abc bin\abc.exe --cases C:\Users\yy257\cpipc_r9_large_smallpo\local_data\tc_public --outputs results\final_public --log logs\reproduce_cec_inside.log --timeout 300
```

The archive was recompressed once after adding the submit-local reproduce logs.

## Input Data

- Cases:
  `C:\Users\yy257\cpipc_r9_large_smallpo\local_data\tc_public`
- External ABC used for formal evaluation:
  `C:\Users\yy257\cpipc_r9_large_smallpo\submit\bin\abc.exe`
- Selector: `configs/final_selector.yaml`
- Pipelines: `configs/pipelines.yaml`

## Results

| Metric | Value |
| --- | ---: |
| Selected nodes | 41004 |
| Max selected level | 20 |
| Total selected levels | 285 |
| Public CEC | 30/30 |
| Fallback count | 0 |
| Inner fallback count | 0 |
| Bad entry count | 0 |
| Node gain vs v3 | 2771 |
| Max level delta vs v3 | -1 |
| Wins/ties/losses vs v3 | 16/14/0 |
| Gain excluding best case | 818 |
| Gain excluding top two cases | 557 |

Final archive:

```text
submit_sharecone.zip
SHA256: 35BE0138E0B132E39118F4E0466B27AA2F9FA54291091094CB6076D79E54287D
```

## Correctness

| Verification | Result |
| --- | ---: |
| `logs/final_cec.log` | 30/30 |
| `submit/logs/reproduce_cec.log` | 30/30 |
| `submit/logs/reproduce_cec_inside.log` | 30/30 |
| `logs/r23_final_zip_extract_cec.log` | 30/30 |
| `logs/r23_final_zip_extract_inside_cec.log` | 30/30 |

All checked logs have `30` `passed=True` entries and zero
`NOT EQUIVALENT`, `failed`, or `Error` markers.

`reports/failure_cases.md` reports zero unresolved CEC failures and zero
fallback-selected cases.

## Risk

The formal release did overwrite protected artifacts as approved. The first
formal attempt exposed a helper default-path bug: formal mode deletes `submit/`
before using the default packaged ABC. The successful recovery used an external
ABC path and reran the complete flow.

This issue is release-process only. The packaged output and final zip were
verified after recovery and after the final recompression.

## Selector Eligibility

R11S uses coarse structural selector features and CEC-backed rollback. It does
not use filenames, hashes, public case IDs, exact public-set fingerprints,
directory names, or port-name predicates.

## Conclusion

promote-to-candidate

R11S is now promoted to the formal final release package. The new formal tag
will be `final_selector_v4_20260623` after committing this release state.

## Next Action

Commit the release artifacts and tag:

```powershell
git tag final_selector_v4_20260623
```

Use `submit_sharecone.zip` with SHA256
`35BE0138E0B132E39118F4E0466B27AA2F9FA54291091094CB6076D79E54287D` as the
current formal submission archive.
