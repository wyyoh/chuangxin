---
research_id: R8-PACKAGING-DRY-RUN
status: active
baseline_tag: final_selector_v2_20260526
baseline_commit: 0b0edf4890283e36fac943166a8c84a148c120b8
branch: release/r8-preflight
created: 2026-06-22
updated: 2026-06-22
affects_final: false
supersedes: []
superseded_by: []
primary_data:
  - reports/r8_release_gate_audit.md
  - reports/r8_formal_names_preflight_metrics.csv
  - reports/r8_formal_names_preflight_vs_formal.csv
  - logs/r8_formal_names_preflight_cec.log
  - tools/package_submit.py
  - tools/reproduce_submit.py
---

# R8 Packaging Readiness Dry Run

## Objective

Audit the release packaging prerequisites for R8 without modifying the formal
main worktree, regenerating `submit/`, overwriting `submit_sharecone.zip`, or
creating a new submit archive. This document is a readiness checklist for the
user-approved release phase.

## Baseline

- Formal baseline tag: `final_selector_v2_20260526`
- Formal commit: `0b0edf4890283e36fac943166a8c84a148c120b8`
- Formal public result: `45870` selected AIG nodes, max level `25`
- Formal correctness: CEC `30/30`, fallback `0`
- User-declared formal submit SHA256:
  `f2d23df5ce280304ea3c18f8c713afbf06577a31e2ba8b3e11e5d2c2b00b8fad`
- Main worktree observed `submit_sharecone.zip` SHA256:
  `7b6c53463b2095b828dbcc1161fb403c737543448ea603f8ad6f7f8d60d151da`

The main-worktree archive hash mismatch is a release-management conflict that
must be acknowledged before packaging. It was not modified during this dry run.

## Commands

Read release packaging policy:

```powershell
Get-Content AGENTS.md | Select-Object -Skip 180 -First 170
```

Inspect current submit/package artifacts:

```powershell
Get-FileHash submit_sharecone.zip -Algorithm SHA256
Get-Content submit_sharecone.zip.sha256
Get-FileHash submit\bin\abc.exe -Algorithm SHA256
Get-FileHash C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe -Algorithm SHA256
```

Check old versus candidate ABC command support:

```powershell
C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe -c "r7win -h"
submit\bin\abc.exe -c "r7win -h"
```

Check scripts without generating output:

```powershell
C:\Users\yy257\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m py_compile tools\optimize_one.py tools\optimize_one_r8_order_choosebest.py tools\eval_public_optimize_one.py tools\extract_r7b_features.py tools\r7b_port_order_stress.py tools\package_submit.py tools\reproduce_submit.py tools\verify_all_cec.py
C:\Users\yy257\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe tools\package_submit.py --help
C:\Users\yy257\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe tools\reproduce_submit.py --help
```

## Input Data

- Candidate worktree: `C:\Users\yy257\cpipc_r8_release_preflight`
- Candidate commit at start of dry run:
  `2adaea8e074a47a13f4e72023a4633073e3ee2b0`
- Candidate tag: `candidate_r8_release_gate_audit_20260622`
- Candidate ABC: `C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe`
- Candidate ABC SHA256:
  `85F59E6291A1C4B10B757BF163D14D2152EAA974B21BC6F4E13F44EC49969805`
- Existing packaged ABC SHA256:
  `89E2ED2D2630E668717FBA334C547B3D482D4EEF9A601A2792E64ADDE00FA89A`
- Existing release-preflight `submit_sharecone.zip` SHA256:
  `f2d23df5ce280304ea3c18f8c713afbf06577a31e2ba8b3e11e5d2c2b00b8fad`

## Results

R8 candidate evidence remains release-worthy:

| Metric | Formal v2 | R8 candidate |
| --- | ---: | ---: |
| selected nodes | `45870` | `43775` |
| node gain |  | `2095` |
| max level | `25` | `21` |
| CEC | `30/30` | `30/30` |
| fallback | `0` | `0` |
| wins/ties/losses |  | `11/19/0` |
| gain excluding best/top2 |  | `737/122` |

Packaging-readiness observations:

| Item | Observation | Meaning |
| --- | --- | --- |
| `reports/final_metrics.csv` | current sum is `45870`, max level `25` | still old formal v2; must be replaced by R8 metrics during approved release |
| `logs/final_cec.log` | current log is old formal CEC | must be replaced by R8 CEC log during approved release |
| `reports/failure_cases.md` | references old `reports/final_metrics.csv` | must be regenerated after final metrics are replaced |
| `reports/final_scoreboard.xlsx` | current file predates R8 formal-name preflight | must be regenerated, likely with `tools/build_scoreboard.mjs` |
| `submit/configs/final_selector.yaml` | old selector v2, no `r7b_eligible` rule | current `submit/` is not R8 |
| `submit/configs/pipelines.yaml` | old selector-v2 pipelines | current `submit/` is not R8 |
| `submit/bin/abc.exe` | old binary SHA256 `89E2...FA89A` | current `submit/` does not contain the R8 ABC binary |
| candidate ABC | `r7win -h` prints command usage | candidate binary has the required R7b command |
| old packaged ABC | `r7win -h` returns `-1073741515` in this environment | old packaged binary must not be reused for R8 |
| `tools/package_submit.py` | includes R8 helper scripts in `SCRIPT_NAMES` | package script dependency list is ready |
| Python syntax | `py_compile` passed with bundled Python | scripts are syntactically ready |
| package/reproduce help | both help commands print expected arguments | script entrypoints are callable |

## Correctness

This dry run does not claim packaged correctness. It verifies only that the
candidate evidence and packaging scripts are ready for a user-approved release
phase.

The correctness already proven for the R8 candidate is:

- formal-name public 30: `43775` nodes, max level `21`, CEC `30/30`,
  fallback `0`
- independent CEC: `30/30`
- random case-name stress: exact per-case reproduction
- PI/PO port-name stress: exact per-case reproduction

The correctness not yet proven is:

- new `submit/` directory contains R8 artifacts
- new `submit_sharecone.zip` SHA256 is recorded
- packaged `submit/tools/optimize_one.py` runs against packaged `bin/abc.exe`
- packaged public CEC from inside `submit/` is `30/30`

## Risk

Low risk after approval:

- Copying R8 metrics and CEC logs into formal report paths on the release
  branch.
- Regenerating `failure_cases.md` from R8 metrics.
- Regenerating `final_scoreboard.xlsx` from R8 metrics.
- Running `package_submit.py` once with the R8 ABC binary and R8 public outputs.

Medium risk after approval:

- Ensuring the final packaged ABC is the intended no-pthread R8 binary.
- Ensuring `submit/` receives R8 configs and not old selector-v2 configs.
- Ensuring the generated archive is not confused with the old `f2d23...` or
  main-worktree `7b6c...` archives.

High risk without approval:

- Overwriting `submit/`.
- Overwriting `submit_sharecone.zip`.
- Replacing the formal final tag or main formal selector.

## Selector Eligibility

No selector-eligibility issue was found in this dry run. R8 remains based on
coarse structural predicates and CEC-guarded declaration-order variants. It
does not depend on file names, hashes, public case IDs, exact public
fingerprints, exact port names, or public discovery order.

## Conclusion

Decision: `continue`

R8 is ready for user-approved release packaging, but the current `submit/`
directory and current submit archives are not R8. Packaging must be a deliberate
release step: update formal reports, regenerate `submit/` from R8 outputs,
compute a new SHA256, and verify packaged CEC. Until that approval is given,
`final_selector_v2_20260526` remains the formal final and R8 remains
candidate-ready.

## Next Action

Ask the user for explicit approval to enter release packaging. If approved, the
safe sequence is:

1. Start from `release/r8-preflight` at the latest tagged R8 readiness commit.
2. Replace formal report paths with R8 evidence:
   `reports/final_metrics.csv`, `logs/final_cec.log`,
   `reports/failure_cases.md`, and `reports/final_scoreboard.xlsx`.
3. Run `tools/package_submit.py` with:
   - `--abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe`
   - `--config configs\final_selector.yaml`
   - `--pipelines configs\pipelines.yaml`
   - `--results results_candidate\r8_formal_names_preflight\public30`
   - `--out submit`
4. Verify CEC from inside `submit/`.
5. Compress once to a new `submit_sharecone.zip`.
6. Compute and record the new SHA256.
7. Tag the verified release.
