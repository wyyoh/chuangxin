# R30b Formal Release

## Objective

Promote the R30b guarded ODC-style post-pass from release integration to a
formal packaged submission.

## Baseline

Previous formal baseline: `final_selector_v7_20260626` at
`08a42ff4678fc89b5880be3efea7d70e9c7690c9`.

- Nodes: `37260`
- Level sum: `277`
- Max level: `20`
- CEC: `30/30`
- Fallback: `0`
- Submit SHA256:
  `ECF4D8694F8DEDD8DF7599591565693683B2152A321381C1FFE8896CE216C3F3`

## Commands

```powershell
py -3 tools\eval_public_optimize_one.py --abc submit\bin\abc.exe --cases C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public --selector configs\final_selector.yaml --pipelines configs\pipelines.yaml --out results_candidate\r30b_release_integration_full_public --csv reports\r30b_release_integration_metrics.csv --opt-timeout 300 --cec-timeout 300 --stats-timeout 120
py -3 tools\verify_all_cec.py --abc submit\bin\abc.exe --cases C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public --outputs results\final_public --log logs\final_cec.log --timeout 300
py -3 tools\package_submit.py --abc submit\bin\abc.exe --config configs\final_selector.yaml --pipelines configs\pipelines.yaml --results results\final_public --metrics reports\final_metrics.csv --scoreboard reports\final_scoreboard.xlsx --cec-log logs\final_cec.log --failure-cases reports\failure_cases.md --out submit
Compress-Archive -Path submit\* -DestinationPath submit_sharecone.zip -Force
```

## Input Data

- Public cases: `C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public`
- Release ABC: `submit\bin\abc.exe`
- Primary metrics: `reports/final_metrics.csv`
- Package summary: `reports/r30b_formal_release_summary.json`

## Results

| Metric | Value |
| --- | ---: |
| Selected nodes | `37097` |
| Node gain vs v7 | `163` |
| Total selected levels | `275` |
| Level sum delta vs v7 | `-2` |
| Max level | `20` |
| CEC | `30/30` |
| Fallback / bad entry | `0 / 0` |
| R30b accepted / rejected / skipped | `7 / 1 / 22` |
| Gain excluding best / top2 | `103 / 70` |
| Total opt / CEC / stats time | `113.026s / 83.700s / 16.204s` |
| Peak RSS | `47.273 MB` |

Accepted R30b audit labels:

```text
tc_public_12, tc_public_15, tc_public_19, tc_public_20, tc_public_21, tc_public_22, tc_public_30
```

Rejected R30b audit label:

```text
tc_public_13: no_node_gain
```

## Correctness

All formal verification gates passed:

- Root final CEC: `logs/final_cec.log`, `30/30`
- Packaged root CEC: `submit/logs/reproduce_cec.log`, `30/30`
- Packaged inside CEC: `submit/logs/reproduce_cec_inside.log`, `30/30`
- Zip-extracted root CEC: `logs/r30b_formal_zip_extract_cec.log`, `30/30`
- Zip-extracted inside CEC: `logs/r30b_formal_zip_extract_inside_cec.log`, `30/30`
- Zip-extracted hidden-style single-case smoke on `tc_public_12`: equivalent

The new submit archive is:

```text
submit_sharecone.zip
SHA256: D19E2732C825A0004A0C83F0A7C20475C364DD0127EC686DCFF4F6D7611A83A0
```

## Risk

R30b remains guarded by CEC, node decrease, and level non-regression. It does
not use filenames, hashes, public case IDs, exact public fingerprints, or port
names.

Known medium risk: port-order stress is CEC-clean and fallback-free, but not
numerically identical to clean public. It produced `37222` nodes, max level
`20`, CEC `30/30`, fallback `0`, with pipeline/node/level mismatches
`14/15/6`. This is an ABC/variant order sensitivity risk, not a correctness
failure.

## Selector Eligibility

Eligible and promoted. R30b uses coarse structural gates:

- `huge_highlevel_low_overlap`
- `mid_nodes_high_overlap_cluster`
- `medium_cluster_mid_nodes`

The gates are computed from the current v7 output BLIF profile and do not read
research CSV rows or public case names.

## Conclusion

Decision label: `promote-to-candidate`

R30b has been packaged as the new formal release candidate `final_selector_v8_20260626`.
After the release commit is created and tagged, it should supersede
`final_selector_v7_20260626` as the current formal submission.

## Next Action

Commit the release artifacts and tag `final_selector_v8_20260626`. Keep
`final_selector_v7_20260626` as the rollback tag.
