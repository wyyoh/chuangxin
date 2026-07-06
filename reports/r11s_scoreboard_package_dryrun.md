# R11S Scoreboard Package Dry Run

Date: 2026-06-23

Branch: `release/r11-preflight`

Base commit at start of this check: `12890df3adc40b97d6d412b77906a5814845abbf`

## Objective

Close the remaining R11S packaging-preflight gap: the earlier scratch package dry
run used a placeholder copy of the old final scoreboard. This check creates an
R11S-specific scoreboard workbook, packages to a scratch directory, and verifies
the scratch package by CEC without overwriting `submit_sharecone.zip`.

## Inputs

- Selector: `configs/final_selector.yaml`
- Pipelines: `configs/pipelines.yaml`
- Public inputs: `local_data/tc_public`
- Full 30 outputs: `results_candidate/r11s_packaging_dryrun_full30`
- Metrics: `reports/r11s_packaging_dryrun_full30_metrics.csv`
- Scoreboard: `reports/r11s_packaging_dryrun_scoreboard.xlsx`
- Scoreboard SHA256:
  `C3DDFA8A13FF0ADEBAAB182BA14469E3DBF08D480301214B2FC8F06F4DAD7D3B`

## Metrics Check

The regenerated full-public metrics preserve the R11S selected result:

| Metric | Value |
| --- | ---: |
| Cases | 30 |
| Selected nodes | 41004 |
| Max level | 20 |
| CSV CEC pass count | 30 |
| Fallback cases | 0 |
| Error cases | 0 |
| Scoreboard formula errors | 0 |

The metrics CSV diff against the previous dry-run record is runtime-only; node,
level, selected pipeline, and correctness fields are unchanged.

## Commands

The commands below are written with the canonical `python` launcher. In this
worktree shell, they were executed with the bundled Codex Python runtime because
`python` was not on `PATH`.

Independent CEC on regenerated full-public outputs:

```powershell
python tools\verify_all_cec.py `
  --abc submit\bin\abc.exe `
  --cases local_data\tc_public `
  --outputs results_candidate\r11s_packaging_dryrun_full30 `
  --log logs\r11s_packaging_dryrun_scoreboard_full30_cec.log `
  --timeout 300
```

Scratch package dry run with the R11S scoreboard:

```powershell
python tools\package_submit.py `
  --abc submit\bin\abc.exe `
  --config configs\final_selector.yaml `
  --pipelines configs\pipelines.yaml `
  --results results_candidate\r11s_packaging_dryrun_full30 `
  --metrics reports\r11s_packaging_dryrun_full30_metrics.csv `
  --scoreboard reports\r11s_packaging_dryrun_scoreboard.xlsx `
  --cec-log logs\r11s_packaging_dryrun_scoreboard_full30_cec.log `
  --failure-cases reports\r11s_packaging_dryrun_failure_cases.md `
  --out scratch\r11s_submit_dryrun_scoreboard
```

Packaged CEC from the repository root:

```powershell
python tools\verify_all_cec.py `
  --abc scratch\r11s_submit_dryrun_scoreboard\bin\abc.exe `
  --cases local_data\tc_public `
  --outputs scratch\r11s_submit_dryrun_scoreboard\results\final_public `
  --log scratch\r11s_submit_dryrun_scoreboard\logs\dryrun_scoreboard_reproduce_cec.log `
  --timeout 300
```

Packaged CEC from inside the scratch package:

```powershell
python tools\verify_all_cec.py `
  --abc bin\abc.exe `
  --cases ..\..\local_data\tc_public `
  --outputs results\final_public `
  --log logs\dryrun_scoreboard_reproduce_cec_inside.log `
  --timeout 300
```

## Results

| Check | Result |
| --- | --- |
| Independent full-public CEC | 30/30 pass |
| Scratch package creation | pass |
| Root-view packaged CEC | 30/30 pass |
| Inside-package packaged CEC | 30/30 pass |
| Source scoreboard hash equals packaged `final_scoreboard.xlsx` hash | pass |
| Formal `submit_sharecone.zip` overwritten | no |

Copied evidence logs:

- `logs/r11s_packaging_dryrun_scoreboard_full30_cec.log`
- `logs/r11s_scoreboard_package_reproduce_cec.log`
- `logs/r11s_scoreboard_package_reproduce_cec_inside.log`

The formal submit archive remains unchanged:

```text
submit_sharecone.zip SHA256 =
4B6236AF057009318EA50E39FFC43FFA3A74708B49A07C2F08FD386AB6D1AF8A
```

## Conclusion

The R11S release-preflight evidence now includes a real R11S scoreboard workbook
and a scratch package that reproduces CEC 30/30 from both root and package-local
paths. This is still a dry run only; no final submit archive was generated.

Next action: if the user approves a release packaging phase, generate the formal
archive once, compute SHA256, verify packaged CEC from `submit/`, and tag the new
formal final.
