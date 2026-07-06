# R28 Release MT Formal Packaging Preflight Checklist

## Objective

Record the current formal-packaging readiness of the R28 gated R27 candidate
without overwriting `submit/` or `submit_sharecone.zip`.

## Candidate State

- Candidate branch: `candidate/r28-gated-r27`
- Candidate indexed tag:
  `candidate_r28_release_mt_packagedryrun_indexed_20260625`
- Candidate indexed commit:
  `2915634c6e3b1fae5fc830b092b7a8a4c01535e6`
- Baseline: `final_selector_v5_20260624`
- Baseline commit: `2722491e9079052e63073344c69eb5c2e10d50a4`

## Evidence Reviewed

- Release ABC reproduction:
  `reports/r28_release_mt_abc_reproduction.md`
- Release metrics:
  `reports/r28_release_mt_full_public_metrics.csv`
- Same-binary v5 comparison:
  `reports/r28_v5_release_mt_full_public_metrics.csv`
- Independent CEC:
  `logs/r28_release_mt_full_public_cec.log`
- Package dry run:
  `reports/r28_release_mt_package_dryrun.md`
- Package dry-run summary:
  `reports/r28_release_mt_package_dryrun_summary.json`
- Guarded release helper plan:
  `reports/r28_release_package_helper_plan.json`
- Guarded release helper formal plan:
  `reports/r28_release_package_helper_formal_plan.json`
- Guarded release helper dry-run summary:
  `reports/r28_release_package_helper_summary.json`
- Formal release draft:
  `reports/r28_formal_release_draft.md`
- Formal manifest draft:
  `reports/r28_formal_manifest_draft.json`
- Formal helper refusal audit:
  `reports/r28_release_helper_refusal_audit.md`
- Research index:
  `docs/research_index.md`

## Gate Checklist

| Gate | Status | Evidence |
| --- | --- | --- |
| Candidate status indexed | PASS | `docs/research_index.md` lists `R28-GATED-R27-RELEASE-MT` as `candidate-ready`. |
| Release ABC is non-Debug | PASS | SHA256 `C21C9F2B28F2669D8F99D7587CBBC496672F5D01E45248D7D028B37FDFFF2E3F`, no Debug CRT or dynamic VC CRT strings. |
| Full public rows | PASS | `30` rows in `reports/r28_release_mt_full_public_metrics.csv`. |
| Full public nodes | PASS | `37464` selected AIG nodes. |
| Max level | PASS | Max level `20`. |
| Full public CEC | PASS | `30/30`, bad lines `0`. |
| Fallback | PASS | `0` fallback rows. |
| Runtime warning | PASS | Sum opt runtime `76.225724s`, max per-case opt runtime `20.505702s`. |
| RSS warning | PASS | Peak RSS `47.309 MB`. |
| Same-binary v5 comparison | PASS | v5 Release ABC baseline: `37568` nodes, max level `20`. |
| Total gain versus v5 Release ABC | PASS | `104` nodes. |
| Wins / ties / losses | PASS | `4 / 26 / 0`. |
| Gain excluding best case | PASS | `21` nodes. |
| Gain excluding top two cases | PASS | `10` nodes. |
| At least three stable gains | PASS | Wins on four cases: `tc_public_14`, `tc_public_15`, `tc_public_26`, `tc_public_30`. |
| Package dry-run root CEC | PASS | `30/30`, bad lines `0`. |
| Package dry-run inside CEC | PASS | `30/30`, bad lines `0`. |
| Zip extract root CEC | PASS | `30/30`, bad lines `0`. |
| Zip extract inside CEC | PASS | `30/30`, bad lines `0`. |
| Hidden-entry smoke from extracted zip | PASS | `tc_public_14` accepted R28 post-pass, selected `2073` nodes, level `15`, CEC equivalent. |
| R28 wrapper packaged | PASS | `tools/optimize_one_r28_gated_r27_candidate.py` present in dry-run package. |
| R28 post-pass config packaged | PASS | `configs/pipelines_r28_gated_r27.yaml` present in dry-run package. |
| Reproduce document R28 wording | PASS | `scratch\r28_release_mt_reproduce_doc_check\reproduce.md` describes `/MT Release` ABC, the R28 guarded post-pass, and the accept-only-if CEC/nodes/level policy. |
| Guarded release helper plan-only | PASS | `reports\r28_release_package_helper_plan.json` validates evidence and defaults to `destructive=false`. |
| Guarded release helper formal plan-only | PASS | `reports\r28_release_package_helper_formal_plan.json` validates evidence, marks formal mode `destructive=true`, and requires token `R28_RELEASE_MT_FORMAL_20260625`. |
| Guarded release helper dry-run package CEC | PASS | `logs\r28_release_package_helper_root_cec.log` and `logs\r28_release_package_helper_inside_cec.log` are both `30/30`, bad lines `0`. |
| Guarded release helper zip CEC | PASS | `logs\r28_release_package_helper_zip_extract_cec.log` and `logs\r28_release_package_helper_zip_extract_inside_cec.log` are both `30/30`, bad lines `0`. |
| Guarded release helper hidden smoke | PASS | `logs\r28_release_package_helper_zip_hidden_smoke_tc_public_14_cec.log` is equivalent, bad lines `0`; metrics show R28 accepted with `2073` nodes and level `15`. |
| Formal release notes draft | PASS | `reports\r28_formal_release_draft.md` records metrics, same-binary delta, ABC SHA, stop conditions, and formal fields still marked `TBD_AFTER_FORMAL_PACKAGING`. |
| Formal manifest draft | PASS | `reports\r28_formal_manifest_draft.json` is marked `draft=true` and keeps formal SHA/tag verification fields as `TBD_AFTER_FORMAL_PACKAGING`. |
| Formal helper confirmation-token guard | PASS | `reports\r28_release_helper_refuse_no_token.log` exits `1` before packaging and reports the required token. |
| Formal helper dirty-worktree guard | PASS | `reports\r28_release_helper_refuse_dirty.log` exits `1` before packaging and requires a clean worktree or explicit `--allow-dirty`. |
| Formal submit overwritten | NOT DONE | Dry run reports `formal_submit_overwritten=false`. |
| Formal zip overwritten | NOT DONE | Dry run reports `formal_zip_overwritten=false`. |
| Formal SHA256 computed | NOT DONE | Requires explicit formal packaging approval. |
| Formal package CEC from final `submit/` | NOT DONE | Requires explicit formal packaging approval. |
| Formal release tag | NOT DONE | Requires explicit formal packaging approval and successful package verification. |

## Current Decision

Decision label: `promote-to-candidate`.

R28 Release MT is ready to enter formal packaging, but it has not yet become a
formal final. The formal `submit/` directory and `submit_sharecone.zip` remain
untouched by this preflight.

## Formal Packaging Instructions After Approval

After explicit approval to overwrite formal artifacts:

1. Run the guarded helper in formal mode:

   ```powershell
   py -3 tools\r28_release_package.py --mode formal --execute --confirm-overwrite-submit R28_RELEASE_MT_FORMAL_20260625
   ```

2. Verify the helper summary in `reports\r28_formal_release_summary.json`.
3. Update final manifest/release notes with tag, commit, metrics, CEC, fallback,
   SHA256, and package verification logs.
4. Commit release artifacts and tag the new formal release.

## Stop Conditions

Stop formal promotion if any formal packaging check differs from dry-run
evidence:

- formal zip CEC less than `30/30`
- any fallback, crash, timeout, or CEC failure
- missing R28 wrapper or post-pass config in the package
- packaged ABC SHA256 differs from
  `C21C9F2B28F2669D8F99D7587CBBC496672F5D01E45248D7D028B37FDFFF2E3F`
- formal zip SHA256 cannot be reproduced or recorded
