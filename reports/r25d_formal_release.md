# R25D Formal Release

## Summary

R25D is promoted from formal-entry candidate to the new packaged release. This release is based on `final_selector_v4_20260623` and is intended to be tagged as `final_selector_v5_20260624` after commit.

## Metrics

| Metric | v4 | R25D final | Delta |
| --- | ---: | ---: | ---: |
| Selected nodes | `41004` | `37708` | `-3296` |
| Max level | `20` | `20` | `0` |
| CEC | `30/30` | `30/30` | `0` |
| Fallback | `0` | `0` | `0` |
| Inner fallback | `0` | `0` | `0` |
| Entry failures | `0` | `0` | `0` |
| Original-input CEC failures | `0` | `0` | `0` |

- Wins/ties/losses vs v4: `3/27/0`
- Gain excluding best/top2: `846/262`
- Peak RSS: `52.211 MB`

## Package

- Archive: `submit_sharecone.zip`
- SHA256: `057963D73132E7752922C707F5348A184BE8D00256522D0C80CFC40061295D0C`
- Previous v4 SHA256: `35BE0138E0B132E39118F4E0466B27AA2F9FA54291091094CB6076D79E54287D`

## Verification

- Final public CEC: `logs/final_cec.log`
- Package root CEC: `submit/logs/reproduce_cec.log`
- Package inside CEC: `submit/logs/reproduce_cec_inside.log`
- Zip extract CEC: `logs/r25d_final_zip_extract_cec.log`
- Zip extract inside CEC: `logs/r25d_final_zip_extract_inside_cec.log`

All five CEC passes are `30/30`. `Cannot open abc.rc` lines are ABC startup noise; non-`abc.rc` open failures are `0`.

## Formal Artifacts

- `configs/final_selector.yaml`
- `configs/pipelines.yaml`
- `tools/optimize_one.py`
- `tools/optimize_one_r8_order_choosebest.py`
- `tools/r25_route_d_divisor_profile.py`
- `reports/final_metrics.csv`
- `reports/final_scoreboard.xlsx`
- `reports/failure_cases.md`
- `current_final_manifest.json`
- `submit/`
- `submit_sharecone.zip`

## Conclusion

R25D release packaging is complete and verified. The release is ready to commit and tag as `final_selector_v5_20260624`.
