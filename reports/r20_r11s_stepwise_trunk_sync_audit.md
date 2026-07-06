---
research_id: R20-R11S-STEPWISE-TRUNK-SYNC
status: stopped
baseline_tag: final_selector_v3_20260622
baseline_commit: 7b20c8c4904682cd905f7afb68d5a4a822c4f8d6
branch: release/r11-preflight
created: 2026-06-23
updated: 2026-06-23
affects_final: false
supersedes:
  - R19-R11S-TRUNK-IMPACT
superseded_by: []
primary_data:
  - reports/r20_merge_tree_summary.json
  - reports/r20_merge_tree_conflict_summary.csv
  - reports/r20_merge_tree_conflicts.csv
  - reports/r20_merge_tree_master_to_v3.txt
  - reports/r20_merge_tree_v3_to_r11s.txt
  - reports/r20_merge_tree_master_to_r11s_direct.txt
---

# R20 R11S Stepwise Trunk Sync Audit

## Objective

After R19 stopped a direct merge from `release/r11-preflight` into stale
`master`, evaluate a safer non-destructive sync path:

1. `master` -> `final_selector_v3_20260622`
2. `final_selector_v3_20260622` -> `release/r11-preflight`

The audit uses `git merge-tree` only. It does not update any branch, working
tree, selector, submit directory, or submit zip.

## Baseline

- Current `master`: `ec9b0ea343d9a9f480b8f02dcfe84f0b4cc114d3`
- Formal v3: `7b20c8c4904682cd905f7afb68d5a4a822c4f8d6`
- R11S release-preflight: `7cb403622fdcb52268d6047570c05c128a790a64`
- Formal v3 metrics: `43775` nodes, max level `21`, CEC `30/30`,
  fallback `0`
- R11S metrics: `41004` nodes, max level `20`, CEC `30/30`, fallback `0`

## Commands

```powershell
git merge-tree --write-tree --messages master final_selector_v3_20260622
git merge-tree --write-tree --messages final_selector_v3_20260622 release/r11-preflight
git merge-tree --write-tree --messages master release/r11-preflight
git rev-list --left-right --count master...final_selector_v3_20260622
git rev-list --left-right --count final_selector_v3_20260622...release/r11-preflight
git rev-list --left-right --count master...release/r11-preflight
```

## Input Data

Primary evidence files:

- `reports/r20_merge_tree_summary.json`
- `reports/r20_merge_tree_conflict_summary.csv`
- `reports/r20_merge_tree_conflicts.csv`
- `reports/r20_merge_tree_master_to_v3.txt`
- `reports/r20_merge_tree_v3_to_r11s.txt`
- `reports/r20_merge_tree_master_to_r11s_direct.txt`

## Results

Commit distance:

| Path | Left / right commits |
| --- | ---: |
| `master...final_selector_v3_20260622` | `9 / 22` |
| `final_selector_v3_20260622...release/r11-preflight` | `0 / 11` |
| `master...release/r11-preflight` | `9 / 33` |

`merge-tree` feasibility:

| Merge | Exit code | Conflict markers | Result |
| --- | ---: | ---: | --- |
| `master` + formal v3 | 1 | 317 | blocked |
| formal v3 + R11S | 0 | 0 | clean |
| `master` + R11S direct | 1 | 317 | blocked |

Conflict categories:

| Scenario | Category | Conflicts |
| --- | --- | ---: |
| `master_to_v3` | protected root release files | 9 |
| `master_to_v3` | protected `submit/` tree | 281 |
| `master_to_v3` | candidate results | 27 |
| `master_to_r11s_direct` | protected root release files | 9 |
| `master_to_r11s_direct` | protected `submit/` tree | 281 |
| `master_to_r11s_direct` | candidate results | 27 |

The clean `formal v3 -> R11S` merge-tree result proves that R11S is a linear
release-preflight continuation of formal v3. The blocked paths are caused by
`master` being stale relative to formal v3, not by R11S introducing a new merge
conflict class.

## Correctness

This audit did not rerun optimization. It relies on already-recorded R11S
correctness evidence:

- public full 30 CEC `30/30`
- fallback `0`
- crash/timeout/CEC fail `0/0/0`
- R18 release-helper dry-run CEC from full outputs `30/30`
- R18 extracted package CEC from root and package-local layouts `30/30`

The audit itself is non-mutating and therefore cannot improve or damage
correctness of the protected final.

## Risk

The direct `master` integration path remains high risk:

- It conflicts in protected root release files.
- It conflicts heavily in the protected `submit/` tree.
- It mixes old trunk catch-up with formal v3 and R11S promotion.
- It would make submit archive provenance hard to review.

The low-risk action is still to keep `release/r11-preflight` as the
authoritative R11S release worktree and perform formal packaging there only
after explicit protected-artifact overwrite approval.

## Selector Eligibility

Unchanged. R11S remains release-ready by candidate evidence. This audit only
rejects trunk-sync mechanics through stale `master`.

## Conclusion

stop

Do not use current `master` as the integration base for R11S. A clean
`formal v3 -> R11S` merge exists, but `master -> formal v3` is blocked by 317
merge-tree conflict markers, mostly in protected submit artifacts.

## Next Action

Highest-value next action remains formal release packaging from
`release/r11-preflight`, after explicit approval to overwrite protected
artifacts:

```powershell
py -3 tools\r11s_release_package.py --mode formal --cases local_data\tc_public --confirm-overwrite-submit
```

If trunk update is still required later, create a separate integration branch
that first resolves `master -> final_selector_v3_20260622` as a release-history
sync, then fast-forwards or merges the already-clean R11S release-preflight
continuation.
