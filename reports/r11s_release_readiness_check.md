---
research_id: R11S-GIA-DISTILLED-STABLE
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
  - reports/r11s_release_readiness_check.json
---

# R11S Release Readiness Check

## Objective

Run a repeatable pre-release checker over R11S candidate evidence without regenerating `submit/` or `submit_sharecone.zip`.

## Baseline

- Formal baseline: `final_selector_v3_20260622`
- R11S expected public metrics: `41004` nodes, max level `20`, total levels `285`, CEC `30/30`, fallback `0`

## Commands

```powershell
python tools\check_r11s_release_readiness.py --json-out reports\r11s_release_readiness_check.json --md-out reports\r11s_release_readiness_check.md
```

## Input Data

- Metrics: `reports\r11s_packaging_dryrun_full30_metrics.csv`
- Full CEC log: `logs\r11s_packaging_dryrun_full30_cec.log`
- Packaged CEC log: `logs\r11s_packaging_dryrun_reproduce_cec.log`
- ABC: `submit\bin\abc.exe`

## Results

- Checks passed: `32/32`

| Check | Status | Detail |
| --- | --- | --- |
| `abc_exists` | `PASS` | submit\bin\abc.exe |
| `metrics_exists` | `PASS` | reports\r11s_packaging_dryrun_full30_metrics.csv |
| `cec_log_exists` | `PASS` | logs\r11s_packaging_dryrun_full30_cec.log |
| `packaged_cec_log_exists` | `PASS` | logs\r11s_packaging_dryrun_reproduce_cec.log |
| `packaged_cec_inside_log_exists` | `PASS` | logs\r11s_packaging_dryrun_reproduce_cec_inside.log |
| `packaged_singlecase_cec_log_exists` | `PASS` | logs\r11s_packaged_tc10_cec.log |
| `failure_cases_exists` | `PASS` | reports\r11s_packaging_dryrun_failure_cases.md |
| `scoreboard_exists` | `PASS` | reports\final_scoreboard.xlsx |
| `selector_exists` | `PASS` | configs\final_selector.yaml |
| `pipelines_exists` | `PASS` | configs\pipelines.yaml |
| `package_script_exists` | `PASS` | tools\package_submit.py |
| `metrics_rows` | `PASS` | 30 expected 30 |
| `metrics_nodes` | `PASS` | 41004 expected 41004 |
| `metrics_max_level` | `PASS` | 20 expected 20 |
| `metrics_total_levels` | `PASS` | 285 expected 285 |
| `metrics_cec_pass` | `PASS` | 30 expected 30 |
| `metrics_fallback` | `PASS` | 0 expected 0 |
| `metrics_inner_fallback` | `PASS` | 0 expected 0 |
| `metrics_bad_entry` | `PASS` | 0 expected 0 |
| `full_cec_equivalent` | `PASS` | {'equivalent': 30, 'not_equivalent': 0, 'non_rc_cannot_open': 0, 'failed': 0, 'error': 0} |
| `packaged_cec_equivalent` | `PASS` | {'equivalent': 30, 'not_equivalent': 0, 'non_rc_cannot_open': 0, 'failed': 0, 'error': 0} |
| `packaged_cec_inside_equivalent` | `PASS` | {'equivalent': 30, 'not_equivalent': 0, 'non_rc_cannot_open': 0, 'failed': 0, 'error': 0} |
| `packaged_singlecase_cec_equivalent` | `PASS` | {'equivalent': 1, 'not_equivalent': 0, 'non_rc_cannot_open': 0, 'failed': 0, 'error': 0} |
| `abc_hash` | `PASS` | 85F59E6291A1C4B10B757BF163D14D2152EAA974B21BC6F4E13F44EC49969805 |
| `abc_r7win_help` | `PASS` | returncode=0; has_expected=True |
| `abc_deepsyn_help` | `PASS` | returncode=0; has_expected=True |
| `failure_cases_clean` | `PASS` | unresolved=0 fallback=0 |
| `scoreboard_nonempty` | `PASS` | bytes=8916 |
| `selector_r11s_rules` | `PASS` | missing=[]; forbidden=[] |
| `pipelines_r11s_present` | `PASS` | missing=[] |
| `package_submit_runtime_deps` | `PASS` | missing=[] |
| `old_formal_zip_unchanged` | `PASS` | 4B6236AF057009318EA50E39FFC43FFA3A74708B49A07C2F08FD386AB6D1AF8A |

## Correctness

The checker is read-only. It validates generated metrics, CEC logs, hashes, package-script dependencies, and selector/pipeline contents.

## Risk

A passing readiness check does not create a final release. The protected `submit/` directory and `submit_sharecone.zip` still require an explicit release packaging phase.

## Selector Eligibility

The check confirms that the R11S selector/pipeline files contain the expected coarse GIA/deepsyn, R10, R9, and R7b entries without public case identity tokens.

## Conclusion

Decision: `promote-to-candidate`

## Next Action

If approved, run the final release packaging phase and verify the new archive from inside `submit/`.
