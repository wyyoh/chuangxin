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
  - reports\r7b_port_order_stress_compare.csv
  - reports\r7b_port_order_inputs_stress_compare.csv
  - reports\r7b_port_order_outputs_stress_compare.csv
---

# R8 Port-Order Preconditioning Feasibility

## Objective

Evaluate whether PI/PO declaration-order changes discovered during R7b stress testing are a candidate-worthy optimization direction.

## Baseline

Comparator is the clean pure R7b candidate: 44559 nodes, max level 21, CEC 30/30, fallback 0.

## Commands

The three stress variants were generated with `tools/r7b_port_order_stress.py` using `--mode both`, `--mode inputs`, and `--mode outputs`, followed by feature extraction, full public 30 evaluation, independent CEC, and comparison against `reports/r7b_pure_clean_metrics.csv`.

## Input Data

- Clean metrics: `reports/r7b_pure_clean_metrics.csv`
- Both-order compare: `reports/r7b_port_order_stress_compare.csv`
- Input-order compare: `reports/r7b_port_order_inputs_stress_compare.csv`
- Output-order compare: `reports/r7b_port_order_outputs_stress_compare.csv`

## Results

| Variant | Nodes | Gain | Max Level | W/T/L | Gain Ex Best | Gain Ex Top2 | Level Regr | CEC Fail | Fallback |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| both | 44365 | 194 | 21 | 5/20/5 | 9 | -22 | 0 | 0 | 0 |
| inputs | 44395 | 164 | 21 | 6/23/1 | 87 | 48 | 0 | 0 | 0 |
| outputs | 44453 | 106 | 20 | 4/22/4 | -32 | -67 | 0 | 0 | 0 |

## Correctness

All three stress variants passed evaluator CEC and independent CEC for all 30 cases, with fallback 0. These are valid equivalence-preserving experiments, but they are not yet a selector-ready final candidate.

## Risk

The raw gains are order-sensitive and include losses. The `inputs` variant has positive gain after excluding the top two cases, but it is still only an offline order perturbation experiment and includes one node-loss case. A final selector cannot simply enable random order shuffling by public case identity.

## Selector Eligibility

Not eligible yet. The next research step would need a deterministic, coarse structural rule or a per-case guarded choose-best wrapper that evaluates multiple orderings and accepts only CEC-passing, node-improving, level-safe outputs without using filenames or exact public fingerprints.

## Conclusion

research-only

## Next Action

Best observed raw total is `both` with `44365` nodes, while `inputs` is the more gate-shaped raw variant with positive gain excluding top two. Continue only with a guarded multi-order choose-best feasibility test, not direct promotion.
