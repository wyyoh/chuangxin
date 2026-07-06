---
research_id: R7b
status: candidate-ready
baseline_tag: final_selector_v2_20260526
baseline_commit: 0b0edf4890283e36fac943166a8c84a148c120b8
branch: candidate/r7b-pure
created: 2026-06-22
updated: 2026-06-22
affects_final: false
primary_data:
  - reports/r7b_command_robustness_audit.csv
---

# R7b r7win Command Robustness Audit

## Objective

Audit the candidate-only ABC command `r7win` on argument guards, network guards, profile no-op behavior, guarded FRAIG acceptance, rollback, and skip paths.

## Baseline

Formal baseline remains `final_selector_v2_20260526`: 45870 nodes, max level 25, CEC 30/30, fallback 0. This audit does not touch the formal selector or submit archive.

## Commands

- ABC: `C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe`
- Output directory: `results_candidate\r7b_command_robustness`
- CSV: `reports\r7b_command_robustness_audit.csv`

## Results

- Probe pass count: `16/16`
- Probe fail count: `0`
- CEC-covered outputs: `12/12`

| Probe | Case | Category | Result | Observed | CEC | Network changed | Skip reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| help |  | usage | pass | usage_shown |  |  |  |
| invalid_mode |  | argument_guard | pass | invalid_mode_rejected |  |  |  |
| missing_mode_arg |  | argument_guard | pass | missing_mode_rejected |  |  |  |
| non_strash_reject | tc_public_13 | network_guard | pass | non_strash_rejected |  |  |  |
| profile_noop_tc_public_1 | tc_public_1 | profile_noop | pass | profile_noop | True | 0 | no_high_overlap_pair |
| profile_noop_tc_public_12 | tc_public_12 | profile_noop | pass | profile_noop | True | 0 | po_count_gt_128 |
| profile_noop_tc_public_13 | tc_public_13 | profile_noop | pass | profile_noop | True | 0 |  |
| profile_noop_tc_public_14 | tc_public_14 | profile_noop | pass | profile_noop | True | 0 |  |
| profile_noop_tc_public_15 | tc_public_15 | profile_noop | pass | profile_noop | True | 0 |  |
| profile_noop_tc_public_30 | tc_public_30 | profile_noop | pass | profile_noop | True | 0 | cluster_potential_lt_70 |
| rewrite_accept_tc_public_13 | tc_public_13 | rewrite_accept | pass | accepted_fraig | True | 1 |  |
| rewrite_accept_tc_public_14 | tc_public_14 | rewrite_accept | pass | accepted_fraig | True | 1 |  |
| rewrite_rollback_tc_public_15 | tc_public_15 | rewrite_rollback | pass | rollback_no_gain | True | 0 |  |
| rewrite_skip_tc_public_1 | tc_public_1 | rewrite_skip | pass | no_high_overlap_pair | True | 0 | no_high_overlap_pair |
| rewrite_skip_tc_public_12 | tc_public_12 | rewrite_skip | pass | po_count_gt_128 | True | 0 | po_count_gt_128 |
| rewrite_skip_tc_public_30 | tc_public_30 | rewrite_skip | pass | cluster_potential_lt_70 | True | 0 | cluster_potential_lt_70 |

## Correctness

Every probe that writes BLIF is checked with ABC CEC against the original case input. Profile no-op probes additionally require `rewrite_status=profile_noop` and `network_changed=0`.

## Risk

ABC returns process code 0 even for some command-level argument errors, so this audit records both the process return code and the command text diagnostics. Promotion should keep using the explicit diagnostic checks rather than process return code alone for CLI misuse cases.

## Selector Eligibility

No selector rule is changed by this audit. R7b selection remains driven by generated coarse overlap features, not file names, hashes, or public case IDs.

## Conclusion

promote-to-candidate

## Next Action

Stop at the user approval point before formal merge or submit packaging.
