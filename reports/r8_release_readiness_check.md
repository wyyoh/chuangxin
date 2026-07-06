---
research_id: R8-READINESS-CHECK
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
  - reports/r8_release_readiness_check.json
---

# R8 Release Readiness Check

## Objective

Run a repeatable pre-release checker over the R8 candidate evidence without generating `submit/` or `submit_sharecone.zip`.

## Baseline

- Formal baseline: `final_selector_v2_20260526`
- R8 expected public metrics: `43775` nodes, max level `21`, CEC `30/30`, fallback `0`

## Commands

```powershell
python tools\check_r8_release_readiness.py --json-out reports\r8_release_readiness_check.json --md-out reports\r8_release_readiness_check.md
```

## Input Data

- Metrics: `reports\r8_formal_names_preflight_metrics.csv`
- CEC log: `logs\r8_formal_names_preflight_cec.log`
- ABC: `C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe`

## Results

- Checks passed: `25/25`

| Check | Status | Detail |
| --- | --- | --- |
| `abc_exists` | `PASS` | C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe |
| `metrics_exists` | `PASS` | reports\r8_formal_names_preflight_metrics.csv |
| `cec_log_exists` | `PASS` | logs\r8_formal_names_preflight_cec.log |
| `explicit_cec_log_exists` | `PASS` | logs\r8_packaging_explicit_reports_cec.log |
| `failure_cases_exists` | `PASS` | reports\r8_packaging_failure_cases.md |
| `scoreboard_exists` | `PASS` | reports\r8_packaging_final_scoreboard.xlsx |
| `selector_exists` | `PASS` | configs\final_selector.yaml |
| `pipelines_exists` | `PASS` | configs\pipelines.yaml |
| `package_script_exists` | `PASS` | tools\package_submit.py |
| `metrics_rows` | `PASS` | 30 expected 30 |
| `metrics_nodes` | `PASS` | 43775 expected 43775 |
| `metrics_max_level` | `PASS` | 21 expected 21 |
| `metrics_cec_pass` | `PASS` | 30 expected 30 |
| `metrics_fallback` | `PASS` | 0 expected 0 |
| `metrics_inner_fallback` | `PASS` | 0 expected 0 |
| `formal_name_cec_30` | `PASS` | {'equivalent': 30, 'not_equivalent': 0, 'non_rc_cannot_open': 0} |
| `explicit_package_cec_30` | `PASS` | {'equivalent': 30, 'not_equivalent': 0, 'non_rc_cannot_open': 0} |
| `abc_hash` | `PASS` | 85F59E6291A1C4B10B757BF163D14D2152EAA974B21BC6F4E13F44EC49969805 |
| `abc_r7win_help` | `PASS` | returncode=0; has_usage=True |
| `failure_cases_clean` | `PASS` | unresolved=0 fallback=0 |
| `scoreboard_nonempty` | `PASS` | bytes=8916 |
| `selector_coarse_r8_rule` | `PASS` | active rules contain r7b_eligible and no tc_public/hash tokens |
| `pipelines_r7win_present` | `PASS` | r7b_r7win_fraig_high present |
| `package_submit_explicit_args` | `PASS` | all explicit report args present |
| `release_preflight_old_zip_unchanged` | `PASS` | F2D23DF5CE280304EA3C18F8C713AFBF06577A31E2BA8B3E11E5D2C2B00B8FAD |

## Correctness

The checker is read-only. It validates already-generated metrics, CEC logs, hashes, and packaging-script arguments.

## Risk

A passing readiness check does not replace the official release phase. The protected `submit/` directory and `submit_sharecone.zip` still require explicit user approval.

## Selector Eligibility

The check confirms that the R8 selector/pipeline files still contain the expected coarse `r7b_eligible` and `r7win` release-preflight entries.

## Conclusion

Decision: `promote-to-candidate`

## Next Action

Ask the user for explicit approval before official `submit/` regeneration and `submit_sharecone.zip` creation.
