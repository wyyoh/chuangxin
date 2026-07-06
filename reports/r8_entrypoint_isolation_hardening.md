---
research_id: R8-PORT-ORDER
status: candidate-ready
baseline_tag: final_selector_v2_20260526
baseline_commit: 0b0edf4890283e36fac943166a8c84a148c120b8
branch: candidate/r8-integration
created: 2026-06-22
updated: 2026-06-22
affects_final: false
supersedes: []
superseded_by: []
primary_data:
  - reports/r8_entrypoint_isolation_smoke.csv
  - results_candidate/r8_entrypoint_isolation/logs/mini_runtime_cec.log
  - results_candidate/r8_entrypoint_isolation/logs/verify_all_cec_driver.log
---

# R8 Entrypoint Isolation Hardening

## Objective

Verify that the R8 candidate single-case optimizer can run from a minimal
package-style runtime using default `configs/final_selector.yaml` and
`configs/pipelines.yaml` names, without creating a submit archive or modifying
the formal main worktree.

## Baseline

- Formal baseline tag: `final_selector_v2_20260526`
- Formal public nodes: `45870`
- Formal max level: `25`
- Formal CEC: `30/30`
- Current R8 release-like candidate: `43775` nodes, max level `21`, CEC
  `30/30`, fallback `0`
- Candidate integration tag before this hardening: `candidate_r8_release_like_20260622`

## Commands

Dependency closure audit:

```powershell
python - <<'PY'
# AST audit over tools/optimize_one.py local imports and package_submit.py SCRIPT_NAMES.
PY
```

Mini-runtime smoke:

```powershell
python <inline harness>  # copies candidate scripts/configs into results_candidate/r8_entrypoint_isolation/runtime
```

The mini runtime contains only the candidate runtime files needed for a
single-case run:

- `tools/optimize_one.py`
- `tools/optimize_one_r8_order_choosebest.py`
- `tools/run_abc_case.py`
- `tools/parse_abc_stats.py`
- `tools/eval_public.py`
- `tools/extract_blif_features.py`
- `tools/extract_r7b_features.py`
- `tools/r7b_port_order_stress.py`
- `tools/select_pipeline.py`
- `tools/verify_all_cec.py`
- `configs/final_selector.yaml` copied from `configs/final_selector_r8_candidate.yaml`
- `configs/pipelines.yaml` copied from `configs/pipelines_r8_candidate.yaml`

## Input Data

Smoke cases were copied into the mini runtime under an ASCII path:

- `tc_public_1`: clean/SOP control
- `tc_public_14`: R7b/r7win high-overlap winner
- `tc_public_22`: high-effort large case and `both` variant winner
- `tc_public_30`: large near-AIG control and `both` variant winner

ABC executable:
`C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe`

ABC SHA256:
`85F59E6291A1C4B10B757BF163D14D2152EAA974B21BC6F4E13F44EC49969805`

## Results

Dependency audit:

- entry closure:
  `eval_public`, `extract_blif_features`, `extract_r7b_features`,
  `optimize_one`, `optimize_one_r8_order_choosebest`, `parse_abc_stats`,
  `r7b_port_order_stress`, `run_abc_case`, `select_pipeline`
- packaged scripts:
  `optimize_one.py`, `optimize_one_r8_order_choosebest.py`,
  `run_abc_case.py`, `parse_abc_stats.py`, `eval_public.py`,
  `extract_blif_features.py`, `extract_r7b_features.py`,
  `r7b_port_order_stress.py`, `select_pipeline.py`, `verify_all_cec.py`
- missing runtime dependencies from package list: none
- extra packaged script: `verify_all_cec.py`

Mini-runtime smoke:

| case | return code | CEC | status | nodes | levels | pipeline | variant |
| --- | ---: | --- | --- | ---: | ---: | --- | --- |
| `tc_public_1` | `0` | true | `selected_candidate` | `103` | `10` | `sop_fx` | `clean` |
| `tc_public_14` | `0` | true | `selected_candidate` | `2156` | `16` | `r7b_r7win_fraig_high` | `outputs` |
| `tc_public_22` | `0` | true | `selected_candidate` | `11001` | `20` | `high_aig_three_round` | `both` |
| `tc_public_30` | `0` | true | `selected_candidate` | `4806` | `21` | `high_aig_three_round` | `both` |

Aggregate smoke status:

- CEC: `4/4`
- fallback: `0`
- inner fallback: `0`
- original-input CEC failures: `0`
- bad entry return codes: `0`
- independent CEC: passed for all 4 outputs

## Correctness

The mini-runtime runs used default config names and did not pass
`--selector` or `--pipelines`. This proves the candidate layout can work when
the R8 selector and pipeline files are installed as `configs/final_selector.yaml`
and `configs/pipelines.yaml`.

The independent CEC driver reported all checks passed and wrote
`results_candidate/r8_entrypoint_isolation/logs/mini_runtime_cec.log`.

## Risk

Remaining risks are release-process risks, not algorithmic blockers:

- The real release branch still has to install the R8 candidate configs under
  formal names.
- The final ABC binary must be the no-pthread build that contains `r7win`.
- A submit archive has not been generated or verified, by policy.

The non-ASCII public-case path issue observed in the earlier release-like run
is avoided by using an ASCII local runtime path. This should remain part of the
release reproducibility checklist.

## Selector Eligibility

The mini-runtime uses the same coarse R8/R7b selector policy already reviewed:
`r7b_eligible` is generated from `r7win -profile -diag` and deterministic
variant choose-best is accepted only after CEC and level checks. No filename,
hash, public case ID, exact public fingerprint, or port-name selector condition
is used.

## Conclusion

Decision: `promote-to-candidate`

R8 passes an additional package-style entrypoint hardening smoke. The formal
single-case entry and dependency closure are ready for a user-approved release
integration phase.

## Next Action

Ask the user before merging R8 into the formal main/release branch or generating
a submit archive. If approved, create a release branch, install R8 configs under
formal names, ensure the no-pthread ABC binary contains `r7win`, then run full
public and packaged CEC gates before packaging.
