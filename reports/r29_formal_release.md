# R29 Formal Release

R29 is promoted as `final_selector_v7_20260626`: `37260` nodes, total levels `277`, max level `20`, CEC `30/30`, fallback `0`.

Final submit archive SHA256: `ECF4D8694F8DEDD8DF7599591565693683B2152A321381C1FFE8896CE216C3F3`

## Delta vs v6

| Metric | v6 | v7 R29 | Delta |
| --- | ---: | ---: | ---: |
| Total nodes | `37464` | `37260` | `-204` |
| Level sum | `278` | `277` | `-1` |
| Max level | `20` | `20` | `0` |
| Wins/ties/losses | n/a | `9/21/0` | n/a |
| Gain excluding best/top2 | n/a | `147 / 111` | n/a |
| Opt time | `76.225724s` | `105.041315s` | `+28.815591s` |
| CEC time | `55.51771s` | `64.621365s` | `+9.103655s` |
| Stats time | `12.622708s` | `13.825113s` | `+1.202405s` |

## Correctness

- Root final CEC: `30/30` (`logs/final_cec.log`).
- Packaged submit root CEC: `30/30` (`submit/logs/reproduce_cec.log`).
- Packaged submit inside CEC: `30/30` (`submit/logs/reproduce_cec_inside.log`).
- Zip extract root/inside CEC: `30/30` / `30/30`.
- Hidden/single-case packaged entry smoke CEC: equivalent.
- Fallback, bad entry, and inner fallback: `0 / 0 / 0`.

## Packaging

- Previous formal zip SHA256: `EF7638BC06771F86485588A16786EAD760550CA86EFAD858B93EE1D808AA4E7F`
- New formal zip SHA256: `ECF4D8694F8DEDD8DF7599591565693683B2152A321381C1FFE8896CE216C3F3`
- Packaged ABC SHA256: `C21C9F2B28F2669D8F99D7587CBBC496672F5D01E45248D7D028B37FDFFF2E3F`
- Packaged runtime dependencies include R28 and R29 guarded post-pass wrappers/configs.

## Release Notes

R29 keeps the v6 selector and adds a second guarded post-pass through the formal `tools/optimize_one.py` entrypoint. The R29 post-pass is attempted only on coarse structural selector buckets and is accepted only when CEC passes, nodes decrease, and level does not increase.

The main tradeoff is runtime: public opt+CEC+stats time increases by about `39.121651s` versus v6 while reducing total nodes by `204` with no public losses.

## Conclusion

Decision label: `promoted`.

R29 is the new formal release package and should be tagged as `final_selector_v7_20260626` after commit.
