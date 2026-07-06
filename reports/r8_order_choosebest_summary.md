---
research_id: R8-PORT-ORDER
status: research-only
baseline_tag: final_selector_v2_20260526
baseline_commit: 0b0edf4890283e36fac943166a8c84a148c120b8
branch: candidate/r7b-pure
created: 2026-06-22
updated: 2026-06-22
affects_final: false
primary_data:
  - reports/r8_order_choosebest_metrics.csv
  - reports/r8_port_order_feasibility.csv
  - logs/r8_order_choosebest_cec.log
---

# R8 Order Choose-Best Feasibility Summary

## Objective

Evaluate whether the port-order sensitivity found in R7b stress testing can become a real optimization direction without using filenames, hashes, or public case IDs.

## Baseline

- Formal baseline: `final_selector_v2_20260526`
- Formal nodes: `45870`
- Formal max level: `25`
- Formal CEC: `30/30`
- Clean pure R7b candidate: `44559` nodes, max level `21`, CEC `30/30`, fallback `0`

## Commands

```powershell
python tools\r7b_port_order_stress.py generate --cases data\tc_public --out data\tc_public_portorder_r7b_stress --map-csv results_candidate\r7b_port_order_stress\port_order_map.csv --seed 20260622 --mode both --clean
python tools\r7b_port_order_stress.py generate --cases data\tc_public --out data\tc_public_portorder_inputs_r7b_stress --map-csv results_candidate\r7b_port_order_inputs_stress\port_order_map.csv --seed 20260622 --mode inputs --clean
python tools\r7b_port_order_stress.py generate --cases data\tc_public --out data\tc_public_portorder_outputs_r7b_stress --map-csv results_candidate\r7b_port_order_outputs_stress\port_order_map.csv --seed 20260622 --mode outputs --clean

python tools\build_r8_order_choosebest.py --variant inputs reports\r7b_port_order_inputs_stress_metrics.csv results_candidate\r7b_port_order_inputs_stress\public30 --variant outputs reports\r7b_port_order_outputs_stress_metrics.csv results_candidate\r7b_port_order_outputs_stress\public30 --variant both reports\r7b_port_order_stress_metrics.csv results_candidate\r7b_port_order_stress\public30 --out results_candidate\r8_order_choosebest\public30 --csv reports\r8_order_choosebest_metrics.csv
python tools\verify_all_cec.py --abc C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe --cases data\tc_public --outputs results_candidate\r8_order_choosebest\public30 --log logs\r8_order_choosebest_cec.log --timeout 300
```

## Input Data

- Clean candidate metrics: `reports/r7b_pure_clean_metrics.csv`
- Formal comparison: `reports/r7b_pure_clean_diff.csv`
- Order-stress metrics:
  - `reports/r7b_port_order_stress_metrics.csv`
  - `reports/r7b_port_order_inputs_stress_metrics.csv`
  - `reports/r7b_port_order_outputs_stress_metrics.csv`

## Results

Raw order variants versus clean pure R7b:

| Variant | Nodes | Gain vs Clean | Max Level | W/T/L | Gain Ex Best | Gain Ex Top2 | CEC Fail | Fallback |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| both | 44365 | 194 | 21 | 5/20/5 | 9 | -22 | 0 | 0 |
| inputs | 44395 | 164 | 21 | 6/23/1 | 87 | 48 | 0 | 0 |
| outputs | 44453 | 106 | 20 | 4/22/4 | -32 | -67 | 0 | 0 |

Research-only choose-best across clean, inputs, outputs, and both:

- total nodes: `44267`
- gain versus clean R7b: `292`
- gain versus formal v2: `1603`
- max level: `21`
- wins/ties/losses versus formal v2: `10/20/0`
- gain excluding best/top2 versus formal v2: `277/92`
- gain excluding best/top2 versus clean R7b: `107/68`
- chosen non-clean variants: `8` cases

Chosen non-clean cases:

| Case | Variant | Clean Nodes | Chosen Nodes | Gain | Clean Level | Chosen Level |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tc_public_14` | outputs | 2223 | 2188 | 35 | 17 | 17 |
| `tc_public_18` | outputs | 498 | 495 | 3 | 12 | 12 |
| `tc_public_20` | inputs | 5538 | 5526 | 12 | 20 | 20 |
| `tc_public_21` | inputs | 5556 | 5544 | 12 | 20 | 20 |
| `tc_public_22` | inputs | 11049 | 11010 | 39 | 20 | 20 |
| `tc_public_3` | both | 109 | 107 | 2 | 8 | 8 |
| `tc_public_30` | both | 5421 | 5236 | 185 | 21 | 21 |
| `tc_public_4` | inputs | 69 | 65 | 4 | 8 | 7 |

## Correctness

All raw order variants passed evaluator CEC and independent CEC on `30/30` public cases with fallback `0`. The combined choose-best output set was re-verified against the original, unmodified `data/tc_public` inputs and passed independent CEC `30/30` in `logs/r8_order_choosebest_cec.log`.

## Risk

This is not yet a final candidate. The current choose-best set is assembled from already-generated public variant outputs, so it is an upper-bound feasibility proof. A promotable candidate must implement the same idea online inside the wrapper: generate deterministic order variants, run the selected pipeline on each, CEC every candidate against the original input, and accept only node-improving, level-safe outputs. Runtime will increase because multiple variants are evaluated.

## Selector Eligibility

The direction is potentially selector-eligible only as a guarded runtime choose-best mechanism. It must not select variants by filename, public case ID, hash, or exact fingerprints. A valid implementation would use the same deterministic variant generation for every hidden case or for broad structural buckets, then let local CEC and metrics choose the result.

## Conclusion

continue

## Next Action

Implement an R8 candidate-only online order choose-best runner and rerun full public 30. Do not promote this assembled output set directly, and do not generate a submit archive.
