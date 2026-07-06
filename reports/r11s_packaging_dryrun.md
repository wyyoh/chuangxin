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
  - reports/r11s_packaging_dryrun_full30_metrics.csv
  - logs/r11s_packaging_dryrun_full30_cec.log
  - logs/r11s_packaging_dryrun_reproduce_cec.log
  - logs/r11s_packaging_dryrun_reproduce_cec_inside.log
  - logs/r11s_packaged_tc10_cec.log
---

# R11S Packaging Dry Run

## Objective

Verify that the R11S candidate can be collected into a scratch package and
reproduced from packaged files, without modifying `submit/` or overwriting
`submit_sharecone.zip`.

## Baseline

- Formal baseline: `final_selector_v3_20260622`
- Formal submit SHA256 before and after dry run:
  `4B6236AF057009318EA50E39FFC43FFA3A74708B49A07C2F08FD386AB6D1AF8A`
- R11S candidate branch: `release/r11-preflight`
- R11S candidate tag: `candidate_r11s_release_ready_20260623`

## Commands

Full public regeneration for packaging dry run:

```powershell
python tools\eval_public_optimize_one.py --abc submit\bin\abc.exe --cases local_data\tc_public --selector configs\final_selector.yaml --pipelines configs\pipelines.yaml --out results_candidate\r11s_packaging_dryrun_full30 --csv reports\r11s_packaging_dryrun_full30_metrics.csv --opt-timeout 300 --cec-timeout 300 --stats-timeout 120
python tools\verify_all_cec.py --abc submit\bin\abc.exe --cases local_data\tc_public --outputs results_candidate\r11s_packaging_dryrun_full30 --log logs\r11s_packaging_dryrun_full30_cec.log --timeout 300
```

Scratch package generation:

```powershell
python tools\generate_failure_cases.py --metrics reports\r11s_packaging_dryrun_full30_metrics.csv --out reports\r11s_packaging_dryrun_failure_cases.md
python tools\package_submit.py --abc submit\bin\abc.exe --config configs\final_selector.yaml --pipelines configs\pipelines.yaml --results results_candidate\r11s_packaging_dryrun_full30 --metrics reports\r11s_packaging_dryrun_full30_metrics.csv --scoreboard reports\final_scoreboard.xlsx --cec-log logs\r11s_packaging_dryrun_full30_cec.log --failure-cases reports\r11s_packaging_dryrun_failure_cases.md --out scratch\r11s_submit_dryrun
```

Packaged reproduction:

```powershell
python tools\verify_all_cec.py --abc scratch\r11s_submit_dryrun\bin\abc.exe --cases local_data\tc_public --outputs scratch\r11s_submit_dryrun\results\final_public --log scratch\r11s_submit_dryrun\logs\dryrun_reproduce_cec.log --timeout 300

cd scratch\r11s_submit_dryrun
python tools\verify_all_cec.py --abc bin\abc.exe --cases ..\..\local_data\tc_public --outputs results\final_public --log logs\dryrun_reproduce_cec_inside.log --timeout 300
python tools\optimize_one.py --abc bin\abc.exe --input ..\..\local_data\tc_public\tc_public_10\input.blif --output logs\dryrun_tc10_output.blif --selector configs\final_selector.yaml --pipelines configs\pipelines.yaml --work-dir work\dryrun_tc10 --metrics-json logs\dryrun_tc10_metrics.json --opt-timeout 300 --cec-timeout 300 --stats-timeout 120
abc.exe -c "cec ..\..\local_data\tc_public\tc_public_10\input.blif logs\dryrun_tc10_output.blif"
```

## Input Data

- `configs/final_selector.yaml`
- `configs/pipelines.yaml`
- `results_candidate/r11s_packaging_dryrun_full30/`
- `reports/r11s_packaging_dryrun_full30_metrics.csv`
- `logs/r11s_packaging_dryrun_full30_cec.log`
- `reports/r11s_packaging_dryrun_failure_cases.md`

## Results

R11S regenerated full public metrics for this dry run:

- rows: `30`
- nodes: `41004`
- max level: `20`
- CEC: `30/30`
- fallback: `0`
- inner fallback: `0`
- bad entry: `0`
- opt time: `484.156s`
- CEC time: `131.312s`
- stats time: `29.223s`

Scratch package:

- path: `scratch/r11s_submit_dryrun`
- file count: `1797`
- packaged ABC SHA256:
  `85F59E6291A1C4B10B757BF163D14D2152EAA974B21BC6F4E13F44EC49969805`
- packaged full-public CEC from repository root: `30/30`
- packaged full-public CEC from inside scratch package: `30/30`
- packaged `tools/optimize_one.py` tc10 smoke: `101` nodes, level `4`, CEC pass

## Correctness

The dry-run package is internally reproducible. Both CEC logs contain 30
equivalent-network results:

- `logs/r11s_packaging_dryrun_reproduce_cec.log`
- `logs/r11s_packaging_dryrun_reproduce_cec_inside.log`

The packaged single-case entrypoint also produced an equivalent tc10 output:

- `logs/r11s_packaged_tc10_cec.log`

## Risk

This is not a final release package:

- `scratch/r11s_submit_dryrun` is a dry-run package directory only.
- `submit/` was not overwritten.
- `submit_sharecone.zip` was not regenerated or overwritten.
- `reports/final_scoreboard.xlsx` was reused as a placeholder because this
  repository has no standalone scoreboard generator. A real release package
  should refresh or explicitly validate the scoreboard artifact.

## Selector Eligibility

Unchanged from R11S release readiness. The selector uses coarse structural
features and does not use file names, hashes, public case IDs, exact line
counts, exact fingerprints, port names, or directory names.

## Conclusion

promote-to-candidate

R11S passed a scratch packaging dry run. The runtime files, configs, scripts,
ABC binary, outputs, and CEC logs are sufficient for packaged reproduction. It
is now ready for an explicit final release packaging phase, but the official
submit archive has not been changed.

## Next Action

If release packaging is approved, regenerate `submit/`, refresh final reports,
refresh or validate the scoreboard, compute the new `submit_sharecone.zip`
SHA256, verify packaged CEC from inside `submit/`, and create a new final tag.
