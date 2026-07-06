---
research_id: R15-R11S-RELEASE-GO-NO-GO
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
  - reports/r11s_packaging_dryrun_full30_metrics.csv
  - reports/r11s_packaging_dryrun_scoreboard.xlsx
  - reports/r11s_scoreboard_package_dryrun.md
  - reports/r11s_identity_stress_summary.md
---

# R15 R11S Release Go/No-Go

## Objective

Perform a final non-destructive release go/no-go audit for R11S. This audit
does not regenerate `submit/` and does not overwrite `submit_sharecone.zip`.

## Baseline

- Current formal baseline: `final_selector_v3_20260622`
- Formal baseline commit: `7b20c8c4904682cd905f7afb68d5a4a822c4f8d6`
- Formal public metrics: `43775` nodes, max level `21`, CEC `30/30`,
  fallback `0`
- Formal submit archive SHA256 still present in this worktree:
  `4B6236AF057009318EA50E39FFC43FFA3A74708B49A07C2F08FD386AB6D1AF8A`

R11S release candidate:

- Worktree: `C:\Users\yy257\cpipc_r11_integration`
- Branch: `release/r11-preflight`
- Commit audited: `e15cf933592f0c1d7780d281aacb704b186bcc6b`
- Latest candidate tag: `candidate_r11s_scoreboard_package_dryrun_20260623`

## Commands

Latest readiness checker:

```powershell
python tools\check_r11s_release_readiness.py
```

Observed output:

```json
{"passed": 32, "status": "pass", "total": 32}
```

The canonical final release commands, once archive overwrite is explicitly
approved, are recorded in `docs/reproduce.md`.

## Input Data

- `configs/final_selector.yaml`
- `configs/pipelines.yaml`
- `tools/package_submit.py`
- `tools/optimize_one.py`
- `reports/r11s_packaging_dryrun_full30_metrics.csv`
- `reports/r11s_packaging_dryrun_scoreboard.xlsx`
- `reports/r11s_packaging_dryrun_failure_cases.md`
- `logs/r11s_packaging_dryrun_full30_cec.log`
- `logs/r11s_packaging_dryrun_reproduce_cec.log`
- `logs/r11s_packaging_dryrun_reproduce_cec_inside.log`

## Results

Gate status:

| Gate / Requirement | Status | Evidence |
| --- | --- | --- |
| Candidate metrics beat formal v3 by nodes | GO | `41004` vs `43775` nodes |
| Max level acceptable | GO | R11S max level `20` vs formal v3 `21`, gate limit `25` |
| Full public CEC | GO | `logs/r11s_packaging_dryrun_full30_cec.log`, `30/30` equivalent |
| Fallback / crash / timeout / bad entry | GO | readiness checker `fallback=0`, `bad_entry=0`; no CEC/log errors |
| Gain excluding best/top2 | GO | R11S release readiness reports `818 / 557` |
| Selector identity safety | GO | random case-name and PI/PO-name stress both `30/30`, no mismatches |
| Package dry run | GO | scratch package CEC from root and inside package both `30/30` |
| R11S scoreboard | GO | `reports/r11s_packaging_dryrun_scoreboard.xlsx`, SHA256 `C3DDFA8A13FF0ADEBAAB182BA14469E3DBF08D480301214B2FC8F06F4DAD7D3B` |
| Runtime/RSS caveat documented | GO with caveat | local RSS incomplete; official environment measures memory externally |
| Formal submit archive already updated | NO-GO | current `submit_sharecone.zip` is still old formal v3 hash |
| Formal final tag created | NO-GO | no `final_selector_v4_20260623` tag yet |

## Correctness

R11S has independent CEC evidence in three forms:

- full public outputs: `30/30`
- scratch package from repository root: `30/30`
- scratch package from inside package layout: `30/30`

The R11S pre-release checker passes `32/32` checks.

## Risk

The only remaining blocking risk is release-management, not candidate quality:
the protected `submit/` directory and `submit_sharecone.zip` still represent
the previous formal v3 package. Merging R11S configs to `master` before release
packaging would create a mismatch between source/config and archive contents.

## Selector Eligibility

R11S remains eligible. The selector uses coarse structural predicates and
online CEC-backed choose-best behavior. It has no filename, directory, hash,
public case ID, exact line-count, exact public fingerprint, output-order, or
port-name predicate.

## Conclusion

promote-to-candidate

GO for explicit release packaging. NO-GO for more optimization research as the
next default action. NO-GO for merging to `master` before the formal archive is
regenerated and verified.

## Next Action

When release packaging is approved:

1. Regenerate R11S full-public outputs.
2. Copy final metrics, CEC log, failure report, and R11S scoreboard into final
   report paths.
3. Regenerate `submit/` with `tools/package_submit.py`.
4. Compress `submit/` once to `submit_sharecone.zip`.
5. Compute and record the new SHA256.
6. Verify packaged CEC from `submit/`.
7. Tag the release as the next formal final, for example
   `final_selector_v4_20260623`.
