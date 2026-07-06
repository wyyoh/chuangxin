---
research_id: R18-R11S-HELPER-DRYRUN
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
  - reports/r18_r11s_helper_dryrun_summary.json
  - logs/r18_r11s_helper_dryrun_full_cec.log
  - logs/r18_r11s_helper_dryrun_zip_extract_cec.log
  - logs/r18_r11s_helper_dryrun_zip_extract_inside_cec.log
---

# R18 R11S Release Helper Dry Run

## Objective

Validate that `tools/r11s_release_package.py` can execute the full default
dry-run packaging flow end to end without touching protected formal artifacts.

## Baseline

- Formal baseline: `final_selector_v3_20260622`
- Formal public metrics: `43775` nodes, max level `21`, CEC `30/30`,
  fallback `0`
- Protected formal archive SHA256 after this dry run:
  `4B6236AF057009318EA50E39FFC43FFA3A74708B49A07C2F08FD386AB6D1AF8A`

## Commands

Full helper dry run:

```powershell
python tools\r11s_release_package.py --cases local_data\tc_public
```

The helper wrote only under:

```text
scratch\r11s_release_package_dryrun
```

## Input Data

- Public input copy: `local_data\tc_public`
- Selector: `configs/final_selector.yaml`
- Pipelines: `configs/pipelines.yaml`
- Scoreboard source: `reports/r11s_packaging_dryrun_scoreboard.xlsx`

## Results

| Metric | Value |
| --- | ---: |
| Selected nodes | 41004 |
| Max level | 20 |
| Total levels | 285 |
| Evaluator CEC pass count | 30 |
| Fallback cases | 0 |
| Bad entries | 0 |
| Helper dry-run zip SHA256 | `37DF7E39033191FA00055A2351314FD7823656F48E0DD5D4D5B4B3D581173F96` |
| Full-output CEC | 30/30 |
| Extracted-zip CEC from root | 30/30 |
| Extracted-zip CEC from package-local layout | 30/30 |

Copied evidence logs:

- `logs/r18_r11s_helper_dryrun_full_cec.log`
- `logs/r18_r11s_helper_dryrun_zip_extract_cec.log`
- `logs/r18_r11s_helper_dryrun_zip_extract_inside_cec.log`

## Correctness

The helper reproduced the R11S public metrics and verified equivalence through
all three CEC layers. It also exercised `package_submit.py`, `Compress-Archive`,
`Expand-Archive`, and package-local CEC paths.

ABC printed the usual missing `abc.rc` startup notices in the CEC logs, but all
three logs contain `30` `passed=True` entries and no `NOT EQUIVALENT`, `failed`,
or `Error` markers.

## Risk

This remains a dry run. The formal `submit/` directory and
`submit_sharecone.zip` were not overwritten. Formal mode still requires
`--confirm-overwrite-submit`.

## Selector Eligibility

Unchanged. This run does not alter selector rules.

## Conclusion

promote-to-candidate

The guarded release helper is validated end to end in dry-run mode. R11S is
ready for the explicit formal release packaging phase.

## Next Action

Run formal packaging only when overwriting protected artifacts is approved:

```powershell
python tools\r11s_release_package.py --mode formal --cases local_data\tc_public --confirm-overwrite-submit
```
