# R28 Release MT Package Dry Run

## Objective

Validate that the R28 `/MT Release` ABC candidate can be assembled into a
submit-like package without overwriting the formal `submit/` directory or
`submit_sharecone.zip`.

## Baseline

- Candidate tag before dry run: `candidate_r28_release_mt_20260625`
- Candidate commit before dry run: `b55335d241c5909f695bb42a9f0819bdab511cae`
- R28 Release ABC: `C:\Users\yy257\abc_r7b_candidate_release_r28_20260625\abc.exe`
- R28 Release ABC SHA256:
  `C21C9F2B28F2669D8F99D7587CBBC496672F5D01E45248D7D028B37FDFFF2E3F`

## Commands

Failure report:

```powershell
py -3 tools\generate_failure_cases.py --metrics reports\r28_release_mt_full_public_metrics.csv --out reports\r28_release_mt_failure_cases.md
```

Scratch package:

```powershell
py -3 tools\package_submit.py --abc C:\Users\yy257\abc_r7b_candidate_release_r28_20260625\abc.exe --config configs\final_selector.yaml --pipelines configs\pipelines.yaml --results results_candidate\r28_release_mt_full_public --metrics reports\r28_release_mt_full_public_metrics.csv --scoreboard reports\r28_release_mt_scoreboard.xlsx --cec-log logs\r28_release_mt_full_public_cec.log --failure-cases reports\r28_release_mt_failure_cases.md --out scratch\r28_release_mt_submit_dryrun
```

Scratch package CEC:

```powershell
py -3 tools\verify_all_cec.py --abc scratch\r28_release_mt_submit_dryrun\bin\abc.exe --cases C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public --outputs scratch\r28_release_mt_submit_dryrun\results\final_public --log scratch\r28_release_mt_submit_dryrun\logs\dryrun_reproduce_cec.log --timeout 300
py -3 tools\verify_all_cec.py --abc bin\abc.exe --cases C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public --outputs results\final_public --log logs\dryrun_reproduce_cec_inside.log --timeout 300
```

Zip dry run:

```powershell
Compress-Archive -Path scratch\r28_release_mt_submit_dryrun\* -DestinationPath scratch\r28_release_mt_submit_dryrun.zip -Force
Expand-Archive -Path scratch\r28_release_mt_submit_dryrun.zip -DestinationPath scratch\r28_release_mt_zip_extract -Force
py -3 tools\verify_all_cec.py --abc scratch\r28_release_mt_zip_extract\bin\abc.exe --cases C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public --outputs scratch\r28_release_mt_zip_extract\results\final_public --log scratch\r28_release_mt_zip_extract\logs\zip_extract_cec.log --timeout 300
py -3 tools\verify_all_cec.py --abc bin\abc.exe --cases C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public --outputs results\final_public --log logs\zip_extract_inside_cec.log --timeout 300
```

Hidden-entry smoke from extracted zip:

```powershell
py -3 tools\optimize_one.py --abc bin\abc.exe --input C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public\tc_public_14\input.blif --output logs\zip_hidden_smoke_tc_public_14\output.blif --selector configs\final_selector.yaml --pipelines configs\pipelines.yaml --work-dir logs\zip_hidden_smoke_tc_public_14\work --metrics-json logs\zip_hidden_smoke_tc_public_14\metrics.json --case-label tc_public_14 --opt-timeout 300 --cec-timeout 300 --stats-timeout 120
bin\abc.exe -c "cec C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public\tc_public_14\input.blif logs\zip_hidden_smoke_tc_public_14\output.blif"
```

## Input Data

- Metrics: `reports\r28_release_mt_full_public_metrics.csv`
- Scoreboard: `reports\r28_release_mt_scoreboard.xlsx`
- Failure report: `reports\r28_release_mt_failure_cases.md`
- Full public outputs: `results_candidate\r28_release_mt_full_public`

Archived dry-run evidence copies:

- Scratch root CEC: `logs\r28_release_mt_package_dryrun_root_cec.log`
- Scratch inside CEC: `logs\r28_release_mt_package_dryrun_inside_cec.log`
- Zip extract root CEC: `logs\r28_release_mt_package_dryrun_zip_extract_cec.log`
- Zip extract inside CEC:
  `logs\r28_release_mt_package_dryrun_zip_extract_inside_cec.log`
- Zip hidden smoke CEC:
  `logs\r28_release_mt_package_dryrun_zip_hidden_smoke_tc_public_14_cec.log`
- Zip hidden smoke metrics:
  `reports\r28_release_mt_package_dryrun_zip_hidden_smoke_tc_public_14_metrics.json`

## Results

Scratch package:

- Submit-like dir: `scratch\r28_release_mt_submit_dryrun`
- Zip dry run: `scratch\r28_release_mt_submit_dryrun.zip`
- Zip dry-run SHA256:
  `ADF5749A5B1EA168B89C1AA03D15669A37576601226D649B2850267E1405DC16`
- Packaged ABC SHA256:
  `C21C9F2B28F2669D8F99D7587CBBC496672F5D01E45248D7D028B37FDFFF2E3F`
- Packaged R28 wrapper present:
  `tools\optimize_one_r28_gated_r27_candidate.py`
- Packaged R28 post-pass config present:
  `configs\pipelines_r28_gated_r27.yaml`

Verification:

| Check | Result |
| --- | --- |
| Scratch package root CEC | `30/30`, bad lines `0` |
| Scratch package inside CEC | `30/30`, bad lines `0` |
| Zip extract root CEC | `30/30`, bad lines `0` |
| Zip extract inside CEC | `30/30`, bad lines `0` |
| Zip hidden smoke `tc_public_14` | R28 status `accepted`, nodes `2073`, level `15`, CEC pass |

## Correctness

All public outputs in the scratch package and extracted zip passed CEC. The
hidden-entry smoke from the extracted zip successfully loaded the packaged R28
wrapper and `configs\pipelines_r28_gated_r27.yaml`, accepted the R28 post-pass
on `tc_public_14`, and passed CEC.

## Risk

This is still a dry run. The formal `submit/` directory and
`submit_sharecone.zip` were not overwritten. The dry-run zip SHA256 above is
not the formal submit hash.

The packaging script was updated to include the R28 wrapper and post-pass
pipeline config. Without this update, packaged public-output CEC could still
pass, but the hidden single-case interface would be incomplete.

## Selector Eligibility

No selector rule was changed in this dry run. The packaged selector remains the
coarse v5/R28 candidate selector and does not use filenames, hashes, public case
IDs, exact public fingerprints, or port names.

## Conclusion

Decision label: `promote-to-candidate`.

The R28 `/MT Release` candidate is package-dry-run ready. It has validated
public outputs, a runnable non-Debug packaged ABC, packaged R28 entrypoint
dependencies, zip-extract CEC, and hidden-entry smoke coverage.

## Next Action

Request explicit formal packaging approval before overwriting `submit/` and
`submit_sharecone.zip`. If approved, repeat the same packaging flow against the
formal release paths, compute the formal zip SHA256, rerun packaged CEC, and tag
the release.
