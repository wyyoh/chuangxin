---
research_id: R11S-GIA-DISTILLED-STABLE
status: candidate-ready
baseline_tag: final_selector_v3_20260622
baseline_commit: 7b20c8c4904682cd905f7afb68d5a4a822c4f8d6
branch: candidate/r11-integration
created: 2026-06-23
updated: 2026-06-23
affects_final: false
supersedes:
  - R11-GIA-DISTILLED
superseded_by: []
primary_data:
  - reports/r11s_integration_preflight.md
  - reports/r11s_integration_full30_metrics.csv
  - reports/r11s_integration_vs_v3_summary.json
  - reports/r11s_release_smoke_metrics.csv
  - logs/r11s_release_smoke_cec.log
---

# R11S Release Readiness

## Objective

Audit whether the R11S candidate is ready for a later release packaging phase
without generating or overwriting `submit_sharecone.zip`.

## Baseline

- Current formal final: `final_selector_v3_20260622`
- Commit: `7b20c8c4904682cd905f7afb68d5a4a822c4f8d6`
- Formal public metrics: `43775` nodes, max level `21`, total levels `293`
- Formal correctness: CEC `30/30`, fallback `0`
- R11S candidate commit: `d6056f80a62764dfd52744547ed0b81f6cdb3dd5`
- R11S candidate tag: `candidate_r11s_gia_distilled_20260623`

## Commands

Full public preflight was run before this readiness audit:

```powershell
python tools\eval_public_optimize_one.py --abc submit\bin\abc.exe --cases local_data\tc_public --selector configs\final_selector.yaml --pipelines configs\pipelines.yaml --out results_candidate\r11s_integration_full30 --csv reports\r11s_integration_full30_metrics.csv --opt-timeout 300 --cec-timeout 300 --stats-timeout 120
python tools\verify_all_cec.py --abc submit\bin\abc.exe --cases local_data\tc_public --outputs results_candidate\r11s_integration_full30 --log logs\r11s_integration_full30_cec.log --timeout 300
```

Release-entry smoke after packaging-plumbing text updates:

```powershell
python tools\eval_public_optimize_one.py --abc submit\bin\abc.exe --cases local_data\tc_public --case-list reports\r11s_release_smoke_cases.txt --selector configs\final_selector.yaml --pipelines configs\pipelines.yaml --out results_candidate\r11s_release_smoke --csv reports\r11s_release_smoke_metrics.csv --opt-timeout 300 --cec-timeout 300 --stats-timeout 120
python tools\verify_all_cec.py --abc submit\bin\abc.exe --cases local_data\tc_public --outputs results_candidate\r11s_release_smoke --log logs\r11s_release_smoke_cec.log --timeout 300
```

## Input Data

- `configs/final_selector.yaml`
- `configs/pipelines.yaml`
- `tools/optimize_one.py`
- `tools/package_submit.py`
- `reports/r11s_integration_full30_metrics.csv`
- `reports/r11s_integration_vs_v3_summary.json`
- `reports/r11s_release_smoke_metrics.csv`
- `logs/r11s_integration_full30_cec.log`
- `logs/r11s_release_smoke_cec.log`

## Results

R11S full public result:

- nodes: `41004`
- max level: `20`
- total levels: `285`
- CEC/fallback/inner fallback/bad entry: `30/30`, `0/0/0`
- wins/ties/losses versus formal v3: `16/14/0`
- node gain versus formal v3: `2771`
- gain excluding best/top2: `818/557`
- opt runtime: `490.283s` versus formal `428.362s`

Release-entry smoke covered four distinct selector paths:

| Case | Path | Nodes | Levels | CEC |
| --- | --- | ---: | ---: | --- |
| `tc_public_10` | `r11_gia_deepsyn_tiny@clean` | 101 | 4 | pass |
| `tc_public_12` | `r10_medium_fraig_cleanup@clean` | 1370 | 14 | pass |
| `tc_public_14` | `r7b_r7win_fraig_high@outputs` | 2156 | 16 | pass |
| `tc_public_22` | `r9_dc2_fraig_cleanup@both` | 10740 | 20 | pass |

Independent smoke CEC also passed.

## Correctness

R11S has full public evaluator CEC `30/30` and independent full public CEC
`30/30`. The release-entry smoke has evaluator CEC `4/4` and independent CEC
`4/4`.

`package_submit.py` already includes all Python scripts needed by the R11S
runtime path:

- `optimize_one.py`
- `optimize_one_r8_order_choosebest.py`
- `run_abc_case.py`
- `parse_abc_stats.py`
- `eval_public.py`
- `extract_blif_features.py`
- `extract_r7b_features.py`
- `r7b_port_order_stress.py`
- `select_pipeline.py`
- `verify_all_cec.py`

R11S adds no new ABC source dependency beyond the packaged binary already used
for R8/R7b plus standard ABC `&deepsyn` support observed in preflight.

## Risk

- `submit/` and `submit_sharecone.zip` are still the old formal v3 release
  artifacts in this worktree. They were not regenerated in this phase.
- The runner's `peak_mem_mb` field is unreliable for R11S because several
  values report `0.0`; official memory should be treated as externally measured
  during release review.
- One local level regression remains on `tc_public_12`, but global max level
  improves from `21` to `20` and total levels improve from `293` to `285`.
- The R11S selector uses narrow but still coarse structural buckets. It has no
  filename, directory, hash, public ID, exact line count, exact fingerprint, or
  port-name condition.

## Selector Eligibility

Eligible for release packaging preflight. The selector uses only coarse
structural predicates and online CEC-backed choose-best behavior. It avoids
public-case identity rules.

## Conclusion

promote-to-candidate

R11S is release-ready as a candidate: the formal config filenames reproduce a
public result that is materially better than formal v3 under the official score
direction, all checked outputs pass CEC, and package script dependencies cover
the runtime path. It is not yet a packaged formal final because no new submit
archive has been generated or verified.

## Next Action

Start a separate release packaging phase only when archive generation is
explicitly approved. That phase should copy the R11S full-public outputs into
`submit/results/final_public`, update final reports, run packaged CEC from
inside `submit/`, compute the new SHA256, and create a new final tag.
