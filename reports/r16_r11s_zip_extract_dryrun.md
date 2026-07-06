---
research_id: R16-R11S-ZIP-EXTRACT-DRYRUN
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
  - reports/r16_r11s_zip_full30_metrics.csv
  - logs/r16_r11s_zip_full30_cec.log
  - logs/r16_r11s_zip_extract_cec.log
  - logs/r16_r11s_zip_extract_inside_cec.log
  - reports/r16_r11s_zip_extract_dryrun_summary.json
---

# R16 R11S Zip Extract Dry Run

## Objective

Verify the final archive mechanics without overwriting the protected formal
`submit_sharecone.zip`: regenerate R11S full-public outputs, package to a
scratch submit directory, compress that directory to a temporary zip, extract
it, and run CEC against the extracted contents.

## Baseline

- Formal baseline: `final_selector_v3_20260622`
- Formal public metrics: `43775` nodes, max level `21`, CEC `30/30`,
  fallback `0`
- Protected formal archive SHA256 before and after this dry run:
  `4B6236AF057009318EA50E39FFC43FFA3A74708B49A07C2F08FD386AB6D1AF8A`

## Commands

Full public regeneration:

```powershell
python tools\eval_public_optimize_one.py `
  --abc submit\bin\abc.exe `
  --cases local_data\tc_public `
  --selector configs\final_selector.yaml `
  --pipelines configs\pipelines.yaml `
  --out results_candidate\r16_r11s_zip_full30 `
  --csv reports\r16_r11s_zip_full30_metrics.csv `
  --opt-timeout 300 `
  --cec-timeout 300 `
  --stats-timeout 120
```

Independent full-public CEC:

```powershell
python tools\verify_all_cec.py `
  --abc submit\bin\abc.exe `
  --cases local_data\tc_public `
  --outputs results_candidate\r16_r11s_zip_full30 `
  --log logs\r16_r11s_zip_full30_cec.log `
  --timeout 300
```

Scratch package and temporary zip:

```powershell
python tools\generate_failure_cases.py `
  --metrics reports\r16_r11s_zip_full30_metrics.csv `
  --out reports\r16_r11s_zip_failure_cases.md

python tools\package_submit.py `
  --abc submit\bin\abc.exe `
  --config configs\final_selector.yaml `
  --pipelines configs\pipelines.yaml `
  --results results_candidate\r16_r11s_zip_full30 `
  --metrics reports\r16_r11s_zip_full30_metrics.csv `
  --scoreboard reports\r11s_packaging_dryrun_scoreboard.xlsx `
  --cec-log logs\r16_r11s_zip_full30_cec.log `
  --failure-cases reports\r16_r11s_zip_failure_cases.md `
  --out scratch\r16_r11s_submit_zipdryrun

Compress-Archive `
  -Path scratch\r16_r11s_submit_zipdryrun\* `
  -DestinationPath scratch\r16_submit_sharecone_dryrun.zip `
  -Force

Expand-Archive `
  -Path scratch\r16_submit_sharecone_dryrun.zip `
  -DestinationPath scratch\r16_zip_extract `
  -Force
```

Extracted-zip CEC:

```powershell
python scratch\r16_zip_extract\tools\verify_all_cec.py `
  --abc scratch\r16_zip_extract\bin\abc.exe `
  --cases local_data\tc_public `
  --outputs scratch\r16_zip_extract\results\final_public `
  --log logs\r16_r11s_zip_extract_cec.log `
  --timeout 300

cd scratch\r16_zip_extract

python tools\verify_all_cec.py `
  --abc bin\abc.exe `
  --cases ..\..\local_data\tc_public `
  --outputs results\final_public `
  --log logs\r16_zip_extract_inside_cec.log `
  --timeout 300
```

## Input Data

- Public input copy: `local_data\tc_public`
- Selector: `configs/final_selector.yaml`
- Pipelines: `configs/pipelines.yaml`
- R11S scoreboard: `reports/r11s_packaging_dryrun_scoreboard.xlsx`

## Results

| Metric | Value |
| --- | ---: |
| Selected nodes | 41004 |
| Max level | 20 |
| Total levels | 285 |
| Evaluator CEC pass count | 30 |
| Fallback cases | 0 |
| Bad entries | 0 |
| Full-public opt runtime | 501.974s |
| Temporary zip SHA256 | `E405F7C9E1DF63F1FC1EA59E48C49C06399371E8BD15DBBDDCDFF7F8B562E57E` |
| Extracted-zip root-view CEC | 30/30 |
| Extracted-zip inside-package CEC | 30/30 |

The temporary zip is a scratch artifact only. It is not the formal
`submit_sharecone.zip`.

## Correctness

Three independent CEC layers passed:

- regenerated full-public outputs: `30/30`
- extracted zip from repository root: `30/30`
- extracted zip from inside package layout: `30/30`

## Risk

No formal submit archive was produced. The protected `submit_sharecone.zip`
still has the old formal v3 hash. The remaining release step is intentionally
destructive and must be performed only during the explicit packaging phase.

## Selector Eligibility

Unchanged. R11S uses coarse structural predicates and online CEC-backed
rollback; no public identity or port-name predicate is used.

## Conclusion

promote-to-candidate

R11S has now passed a full zip/extract dry run. Archive mechanics are ready for
the formal release phase.

## Next Action

When release packaging is explicitly approved, repeat the same flow against the
protected `submit/` directory, create the formal `submit_sharecone.zip`, compute
its SHA256, verify CEC from the final package, and tag the new formal release.
