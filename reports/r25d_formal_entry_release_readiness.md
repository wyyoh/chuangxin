---
research_id: R25D-FORMAL-ENTRY
status: candidate-ready
baseline_tag: final_selector_v4_20260623
baseline_commit: 6291a398b22d573d88350d2c46fe2a8c79218897
branch: release/r25d-formal-entry
created: 2026-06-24
updated: 2026-06-24
affects_final: false
supersedes: []
superseded_by: []
primary_data:
  - reports/r25d_formal_entry_full_public_metrics.csv
  - reports/r25d_formal_entry_comparison.csv
  - reports/r25d_formal_entry_summary.json
  - logs/r25d_formal_entry_full_public_cec.log
---

# R25D Formal Entrypoint Release Readiness

## Objective

Integrate R25D from candidate-only wrapper into the root formal entrypoint and config on a release branch, then rerun full public 30 plus independent CEC. This is not a submit packaging phase: `submit/`, `submit_sharecone.zip`, and formal final artifacts are not overwritten.

## Baseline

- Formal baseline tag: `final_selector_v4_20260623`
- Formal baseline commit: `6291a398b22d573d88350d2c46fe2a8c79218897`
- Formal baseline public metrics: `41004` nodes, max level `20`, CEC `30/30`, fallback `0`
- Formal submit SHA256 remains `35BE0138E0B132E39118F4E0466B27AA2F9FA54291091094CB6076D79E54287D`

## Commands

```powershell
git worktree add -b release/r25d-formal-entry C:\Users\yy257\cpipc_r25d_release final_selector_v4_20260623
py -3 tools\eval_public_optimize_one.py --abc submit\bin\abc.exe --cases C:\Users\yy257\cpipc_r9_large_smallpo\local_data\tc_public --selector configs\final_selector.yaml --pipelines configs\pipelines.yaml --out results_release\r25d_formal_entry\full_public_v1 --csv reports\r25d_formal_entry_full_public_metrics.csv --opt-timeout 300 --cec-timeout 300 --stats-timeout 120
py -3 tools\verify_all_cec.py --abc submit\bin\abc.exe --cases C:\Users\yy257\cpipc_r9_large_smallpo\local_data\tc_public --outputs results_release\r25d_formal_entry\full_public_v1 --log logs\r25d_formal_entry_full_public_cec.log
```

## Input Data

- Root selector: `configs/final_selector.yaml`
- Root pipelines: `configs/pipelines.yaml`
- Root entrypoint: `tools/optimize_one.py`
- R25D feature module: `tools/r25_route_d_divisor_profile.py`
- Output directory: `results_release/r25d_formal_entry/full_public_v1`

## Results

| Metric | Formal v4 | R25D formal entry | Delta |
| --- | ---: | ---: | ---: |
| Total nodes | `41004` | `37708` | `-3296` |
| Max level | `20` | `20` | `0` |
| CEC pass | `30/30` | `30/30` | `0` |
| Fallback | `0` | `0` | `0` |
| Inner fallback | `0` | `0` | `0` |
| Entry failure | `0` | `0` | `0` |
| Runtime warnings >300s | `0` | `0` | `0` |
| RSS warnings >256 MB | `0` | `0` | `0` |

Winning cases versus v4:

| Case | v4 Nodes | R25D Nodes | Gain | v4 Level | R25D Level | Rule |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `tc_public_30` | `2853` | `403` | `2450` | `18` | `13` | `r25_dsd_large_tiny_pi_small_po_shared` |
| `tc_public_26` | `1034` | `450` | `584` | `10` | `10` | `r25_dsd_medium_small_pi_medium_po_shared` |
| `tc_public_28` | `520` | `258` | `262` | `7` | `8` | `r25_dsd_small_small_pi_small_po_shared_dup` |


Aggregate gates:

- Node reduction vs v4: `3296` nodes (`8.04%`)
- Wins/ties/losses: `3/27/0`
- Gain excluding best/top2: `846/262`
- R25D selected cases: `tc_public_26;tc_public_28;tc_public_30`
- Total measured eval runtime: `526.252743s`
- Max peak RSS: `52.211 MB`

## Correctness

Independent CEC log summary:

- `Networks are equivalent`: `30`
- `NOT EQUIVALENT`: `0`
- `failed`: `0`
- `Error`: `0`
- `Cannot open` for `abc.rc`: `90`
- `Cannot open` for non-`abc.rc` files: `0`

`verify_all_cec.py` exited successfully.

## Risk

Residual risks match the candidate review: R25D wins only three public cases, and one small-bucket case has local level `+1` while global max remains `20`. The formal-entry integration reproduces the candidate result exactly, so remaining risk is release-policy judgment rather than an implementation mismatch.

## Selector Eligibility

The promoted root selector uses the same coarse R25D predicates validated in the candidate branch: scale/runtime bins, PI/PO bins, near-two-input-AIG/high-fanin-SOP flags, shared-node threshold, and TFI duplication ratio. It does not use filenames, hashes, `tc_public_xx`, port names, output order fingerprints, or exact public-case fingerprints.

## Conclusion

promote-to-candidate

R25D has been integrated into the root formal entrypoint/config and reproduces the candidate result on full public 30 with independent CEC clean. It is ready for user-approved release packaging, but it is not yet a new formal final because `submit/`, `submit_sharecone.zip`, final reports, and formal tag remain untouched.

## Next Action

Wait for explicit approval for the packaging phase. The next phase may overwrite `submit/` and `submit_sharecone.zip`, update final reports/manifest, compute SHA256, run packaged CEC, and create the new formal tag.
