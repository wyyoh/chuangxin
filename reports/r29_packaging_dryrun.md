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
  - reports/r29_packaging_dryrun_summary.json
  - reports/r29_candidate_scoreboard.xlsx
  - reports/r29_candidate_failure_cases.md
  - logs/r29_packaging_dryrun_submit_cec.log
  - logs/r29_packaging_dryrun_submit_inside_cec.log
  - logs/r29_packaging_dryrun_zip_extract_cec.log
  - logs/r29_packaging_dryrun_zip_extract_inside_cec.log
  - logs/r29_packaging_dryrun_hidden_smoke_cec.log
---

# R29 Packaging Dry-Run

## Objective

Validate that the R29 candidate can be packaged from candidate artifacts into an
isolated scratch submit archive, with all runtime dependencies present, without
overwriting the formal `submit/` directory or `submit_sharecone.zip`.

## Baseline

| Item | Value |
| --- | --- |
| Formal baseline | `final_selector_v6_20260626` |
| Formal commit | `ffd327f5013e5bef4913750579a99dacf0c4dcfb` |
| Formal nodes | `37464` |
| Formal max level | `20` |
| Formal zip SHA256 before dry-run | `EF7638BC06771F86485588A16786EAD760550CA86EFAD858B93EE1D808AA4E7F` |

## Commands

Generate candidate supporting reports:

```powershell
py -3 tools\generate_failure_cases.py --metrics reports\r29_candidate_entry_full_public_candidate_config.csv --out reports\r29_candidate_failure_cases.md
py -3 <openpyxl scoreboard script>
```

Plan-only release helper:

```powershell
py -3 tools\r29_release_package.py --plan-only
```

Isolated dry-run package:

```powershell
py -3 tools\r29_release_package.py --execute
```

The helper packaged into `scratch/r29_release_package_helper_dryrun` and the
scratch tree was removed after copying stable evidence into `reports/` and
`logs/`.

## Input Data

- Candidate metrics: `reports/r29_candidate_entry_full_public_candidate_config.csv`
- Candidate outputs: `results_candidate/r29_postpass_entry_full_public_candidate_config`
- Candidate selector: `configs/final_selector_candidate.yaml`
- Candidate pipelines: `configs/pipelines_candidate.yaml`
- R29 post-pass config: `configs/pipelines_r29_postpass_candidate.yaml`
- ABC binary: `submit/bin/abc.exe`

## Results

| Metric | Value |
| --- | ---: |
| Candidate nodes | `37260` |
| Level sum | `277` |
| Max level | `20` |
| Candidate CEC evidence | `30/30` |
| Fallback / bad entry / inner fallback | `0 / 0 / 0` |
| Wins/ties/losses vs v6 | `9/21/0` |
| Gain vs v6 | `204` |
| Gain excluding best/top2 | `147 / 111` |
| Dry-run zip SHA256 | `8062E6A5FA49AAE20CEE988AFBC5F0ED1DC050BF870551DAD4AD1CF45BD289D4` |
| Packaged ABC SHA256 | `C21C9F2B28F2669D8F99D7587CBBC496672F5D01E45248D7D028B37FDFFF2E3F` |

Packaged runtime dependency checks:

| Dependency | Present |
| --- | --- |
| `tools/optimize_one_r28_gated_r27_candidate.py` | yes |
| `tools/optimize_one_r29_postpass_candidate.py` | yes |
| `configs/pipelines_r28_gated_r27.yaml` | yes |
| `configs/pipelines_r29_postpass_candidate.yaml` | yes |

## Correctness

Dry-run package verification passed:

| Check | Equivalent | Bad markers |
| --- | ---: | ---: |
| Scratch submit root CEC | `30` | `0` |
| Scratch submit inside CEC | `30` | `0` |
| Scratch zip extract root CEC | `30` | `0` |
| Scratch zip extract inside CEC | `30` | `0` |
| Hidden/single-case smoke CEC | `1` | `0` |

The hidden/single-case smoke used `tc_public_14` through the packaged
`tools/optimize_one.py` interface and selected:

```text
r7b_r7win_fraig_high@outputs+r28_r27_mfs_fraig_dc2_bal+r29_mfs_strash_dc2_rwz_bal
```

The smoke output had `2044` nodes, level `14`, and CEC passed.

## Risk

The package mechanics are now validated, including R29 runtime dependencies.
The remaining risk is still the runtime tradeoff documented in
`reports/r29_release_readiness.md`: about `39.121651s` extra public
opt+CEC+stats time versus v6.

## Selector Eligibility

No new selector rule was added in the packaging dry-run. R29 remains gated by
coarse selector reasons and online accept/reject checks. No file names, hashes,
public case IDs, or exact fingerprints are used as selector conditions.

## Conclusion

Decision label: `promote-to-candidate`.

R29 passes isolated packaging dry-run and is ready for formal release packaging
after explicit approval. This dry-run did not overwrite the formal submit
archive.

## Next Action

Wait for explicit approval to enter formal release packaging. Formal packaging
should run `tools/r29_release_package.py --mode formal --execute
--confirm-overwrite-submit R29_RELEASE_FORMAL_20260626`, then write the formal
release report, compute the new `submit_sharecone.zip` SHA256, verify packaged
CEC, and tag the next final.
