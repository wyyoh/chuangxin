---
research_id: R19-R11S-TRUNK-IMPACT
status: superseded
baseline_tag: final_selector_v3_20260622
baseline_commit: 7b20c8c4904682cd905f7afb68d5a4a822c4f8d6
branch: release/r11-preflight
created: 2026-06-23
updated: 2026-06-23
affects_final: false
supersedes: []
superseded_by:
  - R20-R11S-STEPWISE-TRUNK-SYNC
primary_data:
  - reports/r11s_release_readiness.md
  - reports/r18_r11s_release_helper_dryrun.md
---

# R19 R11S Trunk Integration Impact Audit

## Objective

Decide whether the release-ready R11S candidate should be merged directly into
the current `master` trunk after R18 validated the guarded release helper.

## Baseline

- Formal baseline: `final_selector_v3_20260622`
- Formal commit: `7b20c8c4904682cd905f7afb68d5a4a822c4f8d6`
- Formal public metrics: `43775` nodes, max level `21`, CEC `30/30`,
  fallback `0`
- R11S candidate: `41004` nodes, max level `20`, CEC `30/30`, fallback `0`
- R11S release-helper dry run: extracted package CEC `30/30` from both root
  and package-local layouts

## Commands

```powershell
git status --short --branch
git branch --all --verbose --no-abbrev
git merge-base --is-ancestor final_selector_v3_20260622 master
git merge-base --is-ancestor master release/r11-preflight
git rev-list --left-right --count master...release/r11-preflight
git diff --name-status master..release/r11-preflight
```

## Input Data

- Current trunk branch: `master`
- Current candidate release branch: `release/r11-preflight`
- Current release candidate HEAD:
  `4038d53a843ca50acfaaaa95529b24a0b77a7806`
- Current formal tag: `final_selector_v3_20260622`

## Results

The current `master` branch is not on the formal-v3 lineage:

| Check | Result |
| --- | --- |
| `final_selector_v3_20260622` ancestor of `master` | no |
| `master` ancestor of `release/r11-preflight` | no |
| merge base of `master` and R11S | `0b0edf4890283e36fac943166a8c84a148c120b8` |
| merge base of `master` and formal v3 | `0b0edf4890283e36fac943166a8c84a148c120b8` |
| `master...release/r11-preflight` left/right commits | `9 / 32` |

The raw diff from `master` to `release/r11-preflight` is broad:

| Status | Count |
| --- | ---: |
| Added | 7441 |
| Modified | 87 |
| Deleted | 325 |

The diff includes protected release artifacts or release-zone files:

- `configs/final_selector.yaml`
- `configs/pipelines.yaml`
- `logs/final_cec.log`
- `reports/failure_cases.md`
- `reports/final_metrics.csv`
- `reports/final_scoreboard.xlsx`
- `submit/`
- `submit_sharecone.zip`
- `submit_sharecone.zip.sha256`

This does not mean R11S itself is unsafe. It means the current `master` branch
is older than formal v3, so a direct merge would mix old trunk catch-up, formal
v3 packaging, and R11S candidate promotion in one large operation.

## Correctness

R11S correctness remains supported by the existing candidate evidence:

- R11S selected metrics: `41004` nodes, max level `20`
- Public CEC: `30/30`
- Fallback: `0`
- Crash/timeout/CEC fail: `0/0/0`
- R18 helper dry-run CEC layers: full output `30/30`, extracted zip root
  `30/30`, extracted zip package-local `30/30`

This audit did not rerun optimization or CEC. It only inspected branch
relationships and merge impact.

## Risk

Directly merging `release/r11-preflight` into the current `master` is too
coarse to be a clean promotion step:

- It would combine multiple release eras in one merge.
- It would touch protected `submit/` and `submit_sharecone.zip` paths.
- It would make release provenance harder to audit.
- It could hide unrelated trunk conflicts behind the R11S promotion.

The low-risk path is still the guarded formal release helper in the R11S
release worktree, after explicit approval to overwrite protected artifacts.

## Selector Eligibility

R11S selector eligibility is unchanged. The candidate remains stronger than
formal v3 under the documented public metrics and identity stress evidence.

This report only rejects direct `master` merge as a release-management path. It
does not reject R11S as the best current candidate.

## Conclusion

stop

Do not directly merge `release/r11-preflight` into the current `master`. The
candidate is good; the trunk relationship is not clean enough for a broad merge.
Keep R11S as the release-ready candidate and use the guarded release packaging
flow when protected artifact overwrite is explicitly approved.

## Next Action

Proceed in this order:

1. Keep `release/r11-preflight` as the authoritative R11S release worktree.
2. If formal release is approved, run:

   ```powershell
   py -3 tools\r11s_release_package.py --mode formal --cases local_data\tc_public --confirm-overwrite-submit
   ```

3. After formal packaging passes, tag a new final release from the release
   branch rather than doing a broad direct merge into stale `master`.
4. If `master` must be updated later, create a separate clean integration branch
   and merge release history in controlled steps: old master to formal v3, then
   formal v3 to the new final.
