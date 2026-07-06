---
research_id: R29-POSTPASS-MATRIX-V6
status: candidate-ready
baseline_tag: final_selector_v6_20260626
baseline_commit: ffd327f5013e5bef4913750579a99dacf0c4dcfb
branch: candidate/r29-postpass-entry
created: 2026-06-26
updated: 2026-06-26
affects_final: false
supersedes: []
superseded_by: []
primary_data:
  - logs/r29_formal_plan_only.log
  - logs/r29_formal_missing_token_refusal.log
---

# R29 Formal Packaging Gate Preflight

## Objective

Verify that the R29 formal packaging helper exposes the intended destructive
paths in plan-only mode and refuses formal execution without the explicit
confirmation token. This preflight must not modify `submit/` or
`submit_sharecone.zip`.

## Baseline

- Formal baseline: `final_selector_v6_20260626`
- Formal commit: `ffd327f5013e5bef4913750579a99dacf0c4dcfb`
- Current formal zip SHA256:
  `EF7638BC06771F86485588A16786EAD760550CA86EFAD858B93EE1D808AA4E7F`

## Commands

Formal plan-only:

```powershell
py -3 tools\r29_release_package.py --mode formal --plan-only
```

Formal execute without confirmation token:

```powershell
py -3 tools\r29_release_package.py --mode formal --execute
```

## Input Data

- `tools/r29_release_package.py`
- `reports/r29_candidate_entry_full_public_candidate_config.csv`
- `logs/r29_candidate_entry_full_public_candidate_config_cec.log`
- `submit_sharecone.zip`

## Results

Formal plan-only completed successfully and reported destructive formal paths:

| Path role | Planned formal path |
| --- | --- |
| Submit directory | `submit` |
| Submit archive | `submit_sharecone.zip` |
| Formal summary | `reports/r29_formal_release_summary.json` |
| Root packaged CEC | `submit/logs/reproduce_cec.log` |
| Inside packaged CEC | `submit/logs/reproduce_cec_inside.log` |
| Zip extract CEC | `logs/r29_formal_zip_extract_cec.log` |

The plan-only evidence also rechecked candidate metrics:

| Metric | Value |
| --- | ---: |
| Nodes | `37260` |
| Level sum | `277` |
| Max level | `20` |
| CEC evidence | `30/30` |
| Fallback / bad entry / inner fallback | `0 / 0 / 0` |
| Gain vs v6 | `204` |

Formal execute without token failed as intended with exit code `1` and message:

```text
formal mode requires --confirm-overwrite-submit R29_RELEASE_FORMAL_20260626
```

The formal zip SHA256 after the refusal remained:

```text
EF7638BC06771F86485588A16786EAD760550CA86EFAD858B93EE1D808AA4E7F
```

## Correctness

This preflight proves the helper has a release guard:

- `--mode formal --plan-only` is read-only.
- `--mode formal --execute` cannot overwrite formal artifacts without the
  exact confirmation token.
- The current formal archive hash stayed unchanged after the refusal test.

## Risk

The remaining operation is intentionally destructive. Formal release packaging
will overwrite `submit/` and `submit_sharecone.zip`, so it still requires an
explicit user approval message.

## Selector Eligibility

No selector rule changed in this preflight.

## Conclusion

Decision label: `promote-to-candidate`.

R29 has passed candidate evaluation, release readiness, isolated packaging
dry-run, and formal packaging gate preflight. The only remaining gate is
explicit approval to run formal packaging with:

```powershell
py -3 tools\r29_release_package.py --mode formal --execute --confirm-overwrite-submit R29_RELEASE_FORMAL_20260626
```

## Next Action

Wait for explicit release packaging approval. Do not overwrite `submit/` or
`submit_sharecone.zip` before that approval.
