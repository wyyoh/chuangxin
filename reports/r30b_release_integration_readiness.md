---
research_id: R30B-ODC-RELEASE-INTEGRATION
status: candidate-ready
baseline_tag: final_selector_v7_20260626
baseline_commit: 08a42ff4678fc89b5880be3efea7d70e9c7690c9
branch: release/r30b-odc-guard-integration
created: 2026-06-26
updated: 2026-06-26
affects_final: false
supersedes: []
superseded_by: []
primary_data:
  - reports/r30b_release_integration_metrics.csv
  - logs/r30b_release_integration_cec.log
  - reports/r30b_release_port_name_metrics.csv
  - logs/r30b_release_port_name_cec.log
  - reports/r30b_release_port_order_metrics.csv
  - logs/r30b_release_port_order_cec.log
---

# R30b Release Integration Readiness

## Objective

Land the R30b balanced guarded ODC-style post-pass as a formal release
entrypoint/config candidate on top of `final_selector_v7_20260626`, then rerun
full public evaluation, independent CEC, and release-entrypoint stress. This
phase does not generate or overwrite `submit/` or `submit_sharecone.zip`.

## Baseline

`final_selector_v7_20260626` at
`08a42ff4678fc89b5880be3efea7d70e9c7690c9`:

- Selected nodes: `37260`
- Max level: `20`
- Level sum: `277`
- CEC: `30/30`
- Fallback/bad entry: `0/0`
- Submit zip SHA256 in manifest and actual file:
  `ECF4D8694F8DEDD8DF7599591565693683B2152A321381C1FFE8896CE216C3F3`

## Commands

```powershell
py -3 tools\eval_public_optimize_one.py --abc submit\bin\abc.exe --cases C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public --selector configs\final_selector.yaml --pipelines configs\pipelines.yaml --out results_candidate\r30b_release_integration_full_public --csv reports\r30b_release_integration_metrics.csv --opt-timeout 300 --cec-timeout 300 --stats-timeout 120
py -3 tools\verify_all_cec.py --abc submit\bin\abc.exe --cases C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public --outputs results_candidate\r30b_release_integration_full_public --log logs\r30b_release_integration_cec.log --timeout 300
py -3 tools\r7b_port_name_stress.py generate --cases C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public --out results_candidate\r30b_release_stress\port_name_cases --map-csv results_candidate\r30b_release_stress\port_name_map.csv --seed 20260626 --clean
py -3 tools\eval_public_optimize_one.py --abc submit\bin\abc.exe --cases results_candidate\r30b_release_stress\port_name_cases --selector configs\final_selector.yaml --pipelines configs\pipelines.yaml --out results_candidate\r30b_release_stress\port_name_public30 --csv reports\r30b_release_port_name_metrics.csv --opt-timeout 300 --cec-timeout 300 --stats-timeout 120
py -3 tools\verify_all_cec.py --abc submit\bin\abc.exe --cases results_candidate\r30b_release_stress\port_name_cases --outputs results_candidate\r30b_release_stress\port_name_public30 --log logs\r30b_release_port_name_cec.log --timeout 300
py -3 tools\r7b_port_order_stress.py generate --cases C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public --out results_candidate\r30b_release_stress\port_order_cases --map-csv results_candidate\r30b_release_stress\port_order_map.csv --seed 20260626 --mode both --clean
py -3 tools\eval_public_optimize_one.py --abc submit\bin\abc.exe --cases results_candidate\r30b_release_stress\port_order_cases --selector configs\final_selector.yaml --pipelines configs\pipelines.yaml --out results_candidate\r30b_release_stress\port_order_public30 --csv reports\r30b_release_port_order_metrics.csv --opt-timeout 300 --cec-timeout 300 --stats-timeout 120
py -3 tools\verify_all_cec.py --abc submit\bin\abc.exe --cases results_candidate\r30b_release_stress\port_order_cases --outputs results_candidate\r30b_release_stress\port_order_public30 --log logs\r30b_release_port_order_cec.log --timeout 300
```

## Input Data

- Public cases: `C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public`
- Release ABC: `submit\bin\abc.exe`
- Baseline selector/config: `configs/final_selector.yaml`,
  `configs/pipelines.yaml`

## Results

| Run | Nodes | Gain vs v7 | Max level | Level sum | CEC | Fallback | Bad entry | Inner fallback | R30b accepted/rejected/skipped |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| Clean release entrypoint | `37097` | `163` | `20` | `275` | `30/30` | `0` | `0` | `0` | `7/1/22` |
| Port-name stress | `37097` | `163` | `20` | `275` | `30/30` | `0` | `0` | `0` | `7/1/22` |
| Port-order stress | `37222` | `38` | `20` | `279` | `30/30` | `0` | `0` | `2` | `6/2/22` |

Clean R30b gains:

- Gain excluding best case: `103`
- Gain excluding top two cases: `70`
- Accepted cases: `tc_public_12`, `tc_public_15`, `tc_public_19`,
  `tc_public_20`, `tc_public_21`, `tc_public_22`, `tc_public_30`
- Trial rejected case: `tc_public_13` with `no_node_gain`

Runtime and memory on the clean release-entrypoint run:

- Total opt time: `113.026s`
- Total CEC time: `83.700s`
- Total stats time: `16.204s`
- Peak RSS: `47.273 MB`

Compared with the v7 manifest (`105.041s` opt, `64.621s` CEC, `13.825s`
stats, `47.184 MB` peak RSS), R30b adds about `7.985s` opt time and `29.443s`
total internal opt+CEC+stats time while reducing `163` nodes.

## Correctness

The clean release entrypoint passes evaluator CEC and independent CEC:

- Evaluator CEC: `30/30` in `reports/r30b_release_integration_metrics.csv`
- Independent CEC: all checks passed in `logs/r30b_release_integration_cec.log`
- No formal fallback, no bad entry, no timeout/crash observed in the clean run

The port-name stress also passes independent CEC and exactly matches the clean
nodes, levels, and selected pipelines. This is evidence that the R30b release
entrypoint is not using PI/PO names as selector fingerprints.

The port-order stress passes independent CEC and formal fallback remains `0`,
but it is not numerically identical to clean public: `14` pipeline mismatches,
`15` node mismatches, and `6` level mismatches. This appears to come from
order-sensitive ABC/variant behavior rather than a correctness failure. It is a
medium robustness risk and should be disclosed before packaging.

## Risk

Low risk:

- R30b is guarded by CEC, node decrease, and level non-regression.
- Non-matching cases keep the v7 output.
- The post-pass uses coarse structural profile buckets: cluster bucket, node
  count, level, high-overlap pair count, and largest cluster size.
- No filename, hash, `tc_public_xx`, port-name, or exact public fingerprint rule
  is used by the release entrypoint.

Medium risk:

- Port-order stress shows numerical sensitivity. Correctness is stable, but
  gains can shrink under declaration-order perturbation.
- Runtime increases modestly because matched cases run an extra post-pass and
  verification.
- `submit_sharecone.zip.sha256` is stale in this worktree: it contains the old
  v6 hash `EF7638BC06771F86485588A16786EAD760550CA86EFAD858B93EE1D808AA4E7F`,
  while the actual zip and manifest hash are v7
  `ECF4D8694F8DEDD8DF7599591565693683B2152A321381C1FFE8896CE216C3F3`.
  This sidecar should be corrected only during an approved packaging phase.

High risk:

- Packaging has not been run in this phase.
- No new formal tag has been created.
- `submit/` and `submit_sharecone.zip` have not been regenerated.

## Selector Eligibility

Eligible for release packaging review. The R30b gate is structural:

- `huge_highlevel_low_overlap`
- `mid_nodes_high_overlap_cluster`
- `medium_cluster_mid_nodes`

The public case labels in the CSVs are audit labels only. The release wrapper
computes the profile from the current v7 output BLIF and does not read research
CSV rows or public-case names.

## Conclusion

Decision label: `promote-to-candidate`

R30b release integration is candidate-ready for the next user-approved
packaging phase. It improves clean public nodes from `37260` to `37097` while
holding max level at `20`, CEC at `30/30`, and formal fallback at `0`.

## Next Action

Wait for explicit user approval before release packaging. Packaging should:

1. Update release manifest and `submit_sharecone.zip.sha256`.
2. Regenerate `submit/` and `submit_sharecone.zip` exactly once.
3. Verify packaged root and inside CEC.
4. Tag the new formal release only after package verification passes.
