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
  - reports/r29_release_readiness_summary.json
  - reports/r29_candidate_entry_candidate_config_summary.json
  - reports/r29_candidate_entry_full_public_candidate_config.csv
  - logs/r29_candidate_entry_full_public_candidate_config_cec.log
---

# R29 Release Readiness Preflight

## Objective

Check whether the R29 guarded post-pass candidate is ready to enter release
packaging, without modifying `submit/`, `submit_sharecone.zip`, or the formal
selector/config files.

## Baseline

| Item | Value |
| --- | --- |
| Formal baseline | `final_selector_v6_20260626` |
| Formal commit | `ffd327f5013e5bef4913750579a99dacf0c4dcfb` |
| Formal nodes | `37464` |
| Formal level sum | `278` |
| Formal max level | `20` |
| Formal CEC | `30/30` |
| Formal fallback | `0` |
| Current formal zip SHA256 | `EF7638BC06771F86485588A16786EAD760550CA86EFAD858B93EE1D808AA4E7F` |

## Candidate

| Item | Value |
| --- | --- |
| Branch | `candidate/r29-postpass-entry` |
| Commit | `43329a7178dfc5c93ba901821b23a3cba1b3dabe` |
| Entrypoint | `tools/optimize_one.py` wrapping `tools/optimize_one_r29_postpass_candidate.py` |
| Candidate selector | `configs/final_selector_candidate.yaml` |
| Candidate pipelines | `configs/pipelines_candidate.yaml` |
| R29 post-pass config | `configs/pipelines_r29_postpass_candidate.yaml` |
| R29 post-pass | `mfs; strash; dc2; rewrite -z; balance` |

The candidate first runs the v6 entrypoint, then attempts R29 only on coarse
selector buckets. A post-pass result is accepted only when it passes CEC,
reduces nodes, and does not increase level.

## Commands

Candidate full public:

```powershell
py -3 tools\eval_public_optimize_one.py --abc submit\bin\abc.exe --cases C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public --selector configs\final_selector_candidate.yaml --pipelines configs\pipelines_candidate.yaml --out results_candidate\r29_postpass_entry_full_public_candidate_config --csv reports\r29_candidate_entry_full_public_candidate_config.csv
```

Independent CEC:

```powershell
py -3 tools\verify_all_cec.py --abc submit\bin\abc.exe --cases C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public --outputs results_candidate\r29_postpass_entry_full_public_candidate_config --log logs\r29_candidate_entry_full_public_candidate_config_cec.log --timeout 300
```

Preflight summary:

```powershell
py -3 <inline preflight summary script>
```

## Input Data

- `reports/final_metrics.csv`
- `reports/r29_candidate_entry_full_public_candidate_config.csv`
- `reports/r29_candidate_entry_candidate_config_summary.json`
- `logs/r29_candidate_entry_full_public_candidate_config_cec.log`
- `reports/r29_release_readiness_summary.json`

## Results

| Metric | v6 formal | R29 candidate | Delta |
| --- | ---: | ---: | ---: |
| Total nodes | `37464` | `37260` | `-204` |
| Level sum | `278` | `277` | `-1` |
| Max level | `20` | `20` | `0` |
| CEC | `30/30` | `30/30` | `0` |
| Fallback | `0` | `0` | `0` |
| Bad entry | `0` | `0` | `0` |
| Inner fallback | `0` | `0` | `0` |
| Wins/ties/losses | n/a | `9/21/0` | n/a |
| Gain excluding best | n/a | `147` | n/a |
| Gain excluding top two | n/a | `111` | n/a |
| Total opt time | `76.225724s` | `105.041315s` | `+28.815591s` |
| Total CEC time | `55.517710s` | `64.621365s` | `+9.103655s` |
| Total stats time | `12.622708s` | `13.825113s` | `+1.202405s` |
| Peak RSS | `47.309 MB` | `47.184 MB` | `-0.125 MB` |

## Correctness

The candidate satisfies the release-preflight correctness checks:

- Candidate full public CEC: `30/30`.
- Independent CEC log contains `30` equivalent markers.
- Independent CEC log contains no `NOT EQUIVALENT`, `Error:`, `Traceback`,
  `Debug Assertion`, or timeout marker.
- Fallback, bad entry, and inner fallback are all `0`.
- Candidate outputs improve nodes in `9` cases, tie in `21` cases, and lose in
  `0` cases versus v6.

## Risk

The candidate's main release risk is runtime. It adds about `39.121651s` public
opt+CEC+stats time versus v6. The post-pass itself is conservative and
case-local: failed, non-improving, or level-regressing attempts are rejected and
the v6 output is kept.

## Selector Eligibility

The candidate is selector-eligible:

- It uses coarse selector reasons, not filenames, hashes, public case IDs, or
  exact public fingerprints.
- Gains remain positive after excluding the best and top two cases.
- At least three cases improve.
- Max level remains `20`, below the accepted `25` cap.

## Packaging Gate

Release packaging is not performed in this preflight. The current formal zip
remains:

```text
submit_sharecone.zip
SHA256 EF7638BC06771F86485588A16786EAD760550CA86EFAD858B93EE1D808AA4E7F
```

The remaining gate is explicit user approval to overwrite `submit/` and
`submit_sharecone.zip`.

## Conclusion

Decision label: `promote-to-candidate`.

R29 is release-ready pending explicit packaging approval. It should not be
treated as the new formal final until release packaging regenerates the submit
archive, verifies packaged CEC from `submit/`, records the new SHA256, and tags
the formal release.

## Next Action

Wait for explicit release-packaging approval. After approval, create a release
worktree from `candidate/r29-postpass-entry`, promote candidate files to formal
paths, regenerate `submit/` and `submit_sharecone.zip` once, run packaged CEC,
write the formal release report, and tag the next final.
