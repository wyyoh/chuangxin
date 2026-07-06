---
research_id: R8-FINAL-RELEASE
status: promoted
baseline_tag: final_selector_v2_20260526
baseline_commit: 0b0edf4890283e36fac943166a8c84a148c120b8
branch: release/r8-preflight
created: 2026-06-22
updated: 2026-06-22
affects_final: true
supersedes:
  - R8-READINESS-CHECK
superseded_by: []
primary_data:
  - reports/final_metrics.csv
  - logs/final_cec.log
  - submit/logs/reproduce_cec.log
  - submit/logs/reproduce_cec_inside.log
  - logs/r8_zip_extract_reproduce_cec.log
  - r8_final_manifest.json
---

# R8 Final Release Packaging

## Objective

Promote the R8 candidate to an official release package after explicit user approval, without moving any existing final tag.

## Baseline

- Previous formal final: `final_selector_v2_20260526`
- Previous commit: `0b0edf4890283e36fac943166a8c84a148c120b8`
- Previous public metrics: `45870` nodes, max level `25`, CEC `30/30`, fallback `0`
- Previous submit SHA256: `f2d23df5ce280304ea3c18f8c713afbf06577a31e2ba8b3e11e5d2c2b00b8fad`

## Commands

```powershell
python tools\check_r8_release_readiness.py --json-out reports\r8_release_readiness_check_final_prepackage.json --md-out reports\r8_release_readiness_check_final_prepackage.md
python tools\package_submit.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --config configs\final_selector.yaml --pipelines configs\pipelines.yaml --results results_candidate\r8_formal_names_preflight\public30 --metrics reports\final_metrics.csv --scoreboard reports\final_scoreboard.xlsx --cec-log logs\final_cec.log --failure-cases reports\failure_cases.md --out submit
python tools\reproduce_submit.py --submit submit --cases local_data\tc_public --abc submit\bin\abc.exe --log submit\logs\reproduce_cec.log
Push-Location submit
python tools\verify_all_cec.py --abc bin\abc.exe --cases ..\local_data\tc_public --outputs results\final_public --log logs\reproduce_cec_inside.log
Pop-Location
Compress-Archive -Path submit\* -DestinationPath submit_sharecone.zip -Force
Get-FileHash submit_sharecone.zip -Algorithm SHA256
```

An additional zip-extract CEC check was run from the freshly generated `submit_sharecone.zip` contents and logged at `logs/r8_zip_extract_reproduce_cec.log`.

## Input Data

- Formal metrics source: `reports/r8_formal_names_preflight_metrics.csv`
- Formal CEC source: `logs/r8_formal_names_preflight_cec.log`
- Failure report source: `reports/r8_packaging_failure_cases.md`
- Scoreboard source: `reports/r8_packaging_final_scoreboard.xlsx`
- Packaged ABC source: `C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe`

## Results

| Item | Value |
| --- | ---: |
| Public cases | 30 |
| Selected nodes | 43775 |
| Max selected level | 21 |
| CEC pass | 30/30 |
| Fallback | 0 |
| Inner fallback | 0 |
| Bad return code | 0 |
| Node gain vs v2 | 2095 |
| Wins/ties/losses vs v2 | 11/19/0 |
| Gain excluding best case | 737 |
| Gain excluding top two cases | 122 |
| Total opt time sec | 428.362053 |
| Total CEC time sec | 203.138462 |
| Peak RSS MB | 52.137 |
| ABC SHA256 | `85f59e6291a1c4b10b757bf163d14d2152eaa974b21bc6f4e13f44ec49969805` |
| submit_sharecone.zip SHA256 | `4b6236af057009318ea50e39ffc43ffa3a74708b49a07c2f08fd386ab6d1af8a` |

## Correctness

- Final metrics CEC: `30/30`.
- Package root CEC: `30/30`, log `submit/logs/reproduce_cec.log`.
- Package inside-`submit/` CEC: `30/30`, log `submit/logs/reproduce_cec_inside.log`.
- Zip-extract CEC: `30/30`, log `logs/r8_zip_extract_reproduce_cec.log`.
- No NOT EQUIVALENT, failed, or Error lines were present in the three package reproduction logs.
- ABC `Cannot open abc.rc` startup messages are present and benign; all CEC comparisons still report equivalence.

## Risk

The release replaces the prior formal archive with R8 evidence. Rollback remains possible through `final_selector_v2_20260526` and the previous SHA256 recorded above.

## Selector Eligibility

The R8 final selector uses the coarse `r7b_eligible` feature and does not use filenames, hashes, public case IDs, exact public-set fingerprints, or exact port-name combinations as selector conditions.

## Conclusion

Decision: `promote-to-candidate` completed, then released after explicit user approval. After tagging, use `final_selector_v3_20260622` as the formal final tag.

## Next Action

After this report is committed, tag the release as `final_selector_v3_20260622`, update `docs/research_index.md` in the main workspace, and preserve `final_selector_v2_20260526` as rollback.
