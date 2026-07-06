---
research_id: R21-R11S-FORMAL-PACKAGING-GUARD
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
  - reports/r21_formal_plan_only.json
  - reports/r21_dryrun_plan_only.json
  - reports/r21_release_guard_summary.json
  - reports/r21_cases_source_check.json
---

# R21 R11S Formal Packaging Plan Guard

## Objective

Reduce the remaining formal-release risk without overwriting protected
artifacts. This audit records the exact formal packaging write plan and verifies
that formal mode still refuses to run without the explicit overwrite flag.

## Baseline

- Formal baseline: `final_selector_v3_20260622`
- Formal public metrics: `43775` nodes, max level `21`, CEC `30/30`,
  fallback `0`
- Current release-ready candidate: R11S
- R11S expected formal metrics: `41004` nodes, max level `20`, CEC `30/30`,
  fallback `0`
- Protected submit archive hash after this audit:
  `4B6236AF057009318EA50E39FFC43FFA3A74708B49A07C2F08FD386AB6D1AF8A`

## Commands

```powershell
py -3 tools\r11s_release_package.py --mode formal --plan-only
py -3 tools\r11s_release_package.py --mode dry-run --plan-only
py -3 tools\r11s_release_package.py --mode formal
py -3 tools\check_r11s_release_readiness.py
Get-FileHash .\submit_sharecone.zip -Algorithm SHA256
```

The final formal command intentionally omits
`--confirm-overwrite-submit`; it is expected to fail before any write.

## Input Data

- `tools/r11s_release_package.py`
- `reports/r21_formal_plan_only.json`
- `reports/r21_dryrun_plan_only.json`
- `reports/r21_release_guard_summary.json`
- `reports/r21_cases_source_check.json`

## Results

Plan-only results:

| Check | Result |
| --- | --- |
| formal `--plan-only` exit | `0` |
| dry-run `--plan-only` exit | `0` |
| formal without confirmation exit | `1` |
| formal without confirmation rejected | `true` |
| readiness checker | `32/32 pass` |
| protected submit hash after audit | `4B6236AF057009318EA50E39FFC43FFA3A74708B49A07C2F08FD386AB6D1AF8A` |
| local `local_data/tc_public` present | `false` |
| ASCII external cases source | `C:\Users\yy257\cpipc_r9_large_smallpo\local_data\tc_public`, `30` case dirs |

Formal mode plans to write these protected or release-check paths:

- `results/final_public`
- `reports/final_metrics.csv`
- `logs/final_cec.log`
- `reports/failure_cases.md`
- `reports/final_scoreboard.xlsx`
- `submit`
- `submit_sharecone.zip`
- `scratch/r11s_formal_zip_extract_check`
- `logs/r11s_formal_zip_extract_cec.log`
- `logs/r11s_formal_zip_extract_inside_cec.log`

The helper prints the formal plan before rejecting a no-confirmation formal
run. This is useful for auditability and did not write protected artifacts.

## Correctness

This audit did not rerun full public optimization or CEC. It re-used the R11S
readiness checker, which still reports `32/32 pass`. Prior R18 evidence remains
the package-flow correctness proof: full outputs `30/30`, extracted zip root
`30/30`, and extracted zip package-local `30/30`.

## Risk

Risk is now limited to the explicit formal packaging action itself. The guard
behavior remains intact:

- default mode is non-destructive;
- formal plan-only is read-only;
- formal execution requires `--confirm-overwrite-submit`;
- formal execution also requires a clean worktree unless `--allow-dirty` is
  passed.

## Selector Eligibility

Unchanged. R11S remains the release-ready candidate and this audit does not
change selector rules.

## Conclusion

promote-to-candidate

R11S is still ready for the explicit formal release packaging phase. The helper
records the destructive plan and refuses formal execution without the overwrite
confirmation flag. Protected artifacts were not modified in this audit.

## Next Action

When protected artifact overwrite is explicitly approved, run the formal helper
from the clean `release/r11-preflight` worktree. Either restore
`local_data/tc_public` first or pass the existing ASCII cases source directly:

```powershell
py -3 tools\r11s_release_package.py --mode formal --cases C:\Users\yy257\cpipc_r9_large_smallpo\local_data\tc_public --confirm-overwrite-submit
```

Do not route the release through stale `master`; R20 showed that trunk sync must
be handled separately.
