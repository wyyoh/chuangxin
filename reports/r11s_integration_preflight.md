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
  - reports/r11s_integration_full30_metrics.csv
  - reports/r11s_integration_vs_v3.csv
  - reports/r11s_integration_vs_v3_summary.json
  - logs/r11s_integration_full30_cec.log
---

# R11S Integration Preflight

## Objective

Promote the R11 distilled GIA/deepsyn idea into a cleaner candidate integration
form using the formal config filenames, while avoiding the unstable public
bucket observed during integration reproduction.

## Baseline

- Formal baseline: `final_selector_v3_20260622`
- Formal commit: `7b20c8c4904682cd905f7afb68d5a4a822c4f8d6`
- Formal public result: `43775` nodes, max level `21`, total levels `293`,
  CEC `30/30`, fallback `0`
- Formal submit archive remains unchanged.

## Commands

Full public 30 through formal config filenames:

```powershell
python tools\eval_public_optimize_one.py --abc submit\bin\abc.exe --cases local_data\tc_public --selector configs\final_selector.yaml --pipelines configs\pipelines.yaml --out results_candidate\r11s_integration_full30 --csv reports\r11s_integration_full30_metrics.csv --opt-timeout 300 --cec-timeout 300 --stats-timeout 120
```

Independent CEC:

```powershell
python tools\verify_all_cec.py --abc submit\bin\abc.exe --cases local_data\tc_public --outputs results_candidate\r11s_integration_full30 --log logs\r11s_integration_full30_cec.log --timeout 300
```

## Input Data

- `configs/final_selector.yaml`
- `configs/pipelines.yaml`
- `reports/final_metrics.csv`
- `reports/r11s_integration_full30_metrics.csv`
- `reports/r11s_integration_vs_v3.csv`
- `logs/r11s_integration_full30_cec.log`

## Results

R11S candidate:

- nodes: `41004`
- max level: `20`
- total levels: `285`
- CEC/fallback/inner fallback/bad entry: `30/30`, `0/0/0`
- wins/ties/losses versus formal v3: `16/14/0`
- node gain versus formal v3: `2771`
- node reduction versus formal v3: `6.3301%`
- gain excluding best/top2: `818/557`
- opt runtime: `490.283s` versus formal `428.362s`
- CEC runtime: `132.468s` versus formal `203.138s`
- RSS field: `0.0` in this runner and not used as a positive memory claim

The largest retained gain is `tc_public_30`: `4806 -> 2853` nodes and level
`21 -> 18`.

## Correctness

Full public evaluator CEC passed `30/30`. Independent CEC also passed all 30
cases. Logs include ABC startup messages for missing `abc.rc`, but no
`NOT EQUIVALENT`, failed, or error markers were found.

## Risk

The original R11 research run recorded `40940` nodes. During clean integration,
the same R11 selector reproduced as `40963` because the
`r11_deepsyn_small_small_pi_medium_po` bucket produced a worse `tc_public_15`
result in one full run. A repeated single-case probe showed this bucket was not
worth adding a runtime-heavy repeat mechanism.

R11S therefore refines that bucket with `cubes_bin_in: [cubes_tiny]`, preserving
the stable `tc_public_10` gain and routing `tc_public_15` back to the verified
R7b path. It also removes the `small_large_pi_small_po` deepsyn bucket, which
only gave `13` nodes on `tc_public_13` while increasing level and runtime.

One local level regression remains:

- `tc_public_12`: `+1` level, `15` node gain

Global max level still improves from `21` to `20`, and total levels improve
from `293` to `285`.

## Selector Eligibility

The candidate selector uses coarse structural bins only: scale grade, runtime
size bin, PI/PO bins, cube bins, max fanin bins, two-input ratio bins,
`near_two_input_aig`, `high_fanin_sop`, and R7b eligibility. It does not use
filenames, hashes, public case IDs, exact line counts, exact public-set
fingerprints, port names, or directory names.

## Conclusion

promote-to-candidate

R11S is weaker than the best one-off R11 research number by `64` nodes, but it
is the better integration candidate: it is reproduced through formal config
filenames, keeps the major official-score gains, removes an unstable bucket,
improves max and total levels, and passes independent CEC.

## Next Action

Commit the candidate integration evidence. Do not generate or overwrite
`submit_sharecone.zip` until a separate release packaging phase is explicitly
approved.
