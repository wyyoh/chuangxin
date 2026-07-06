# R28 Formal Release

## Status

Decision label: `promoted`.

R28 gated R27 post-pass has been packaged as the formal release candidate for
`final_selector_v6_20260626`. The formal helper overwrote `submit/` and
`submit_sharecone.zip` only after explicit user approval.

## Baseline

- Previous formal tag: `final_selector_v5_20260624`
- Previous formal commit: `2722491e9079052e63073344c69eb5c2e10d50a4`
- Previous formal nodes: `37708`
- Previous formal max level: `20`
- Previous formal zip SHA256:
  `057963D73132E7752922C707F5348A184BE8D00256522D0C80CFC40061295D0C`

## Release Metrics

| Item | Value |
| --- | --- |
| Public cases | `30` |
| Selected AIG nodes | `37464` |
| Total selected levels | `278` |
| Max selected level | `20` |
| CEC | `30/30` |
| Fallback | `0` |
| Crash/timeout/CEC fail | `0/0/0` |
| Total opt runtime | `76.225724s` |
| Total CEC runtime | `55.517710s` |
| Total stats runtime | `12.622708s` |
| Peak RSS | `47.309 MB` |

## Delta Versus V5

Under the same Release ABC comparison, R28 improves from `37568` to `37464`
selected nodes.

| Item | Value |
| --- | --- |
| Same-binary node gain | `104` |
| Gain versus v5 formal package metric | `244` |
| Wins / ties / losses | `4 / 26 / 0` |
| Gain excluding best case | `21` |
| Gain excluding top two cases | `10` |
| Winning cases for audit | `tc_public_14`, `tc_public_15`, `tc_public_26`, `tc_public_30` |

The R28 gate remains coarse-structural and does not use filenames, hashes,
public case IDs, exact public-set fingerprints, or port-name fingerprints.

## Package

- Formal zip: `submit_sharecone.zip`
- Formal zip SHA256:
  `EF7638BC06771F86485588A16786EAD760550CA86EFAD858B93EE1D808AA4E7F`
- Packaged ABC SHA256:
  `C21C9F2B28F2669D8F99D7587CBBC496672F5D01E45248D7D028B37FDFFF2E3F`
- Packaged ABC build: `/MT Release`
- Debug CRT strings: none
- Dynamic VC CRT strings: none

## Verification

| Check | Result | Evidence |
| --- | --- | --- |
| Package root CEC | `30/30` | `submit/logs/reproduce_cec.log` |
| Package inside CEC | `30/30` | `submit/logs/reproduce_cec_inside.log` |
| Zip-extract root CEC | `30/30` | `logs/r28_formal_zip_extract_cec.log` |
| Zip-extract inside CEC | `30/30` | `logs/r28_formal_zip_extract_inside_cec.log` |
| Hidden-entry smoke | CEC equivalent | `logs/r28_formal_zip_hidden_smoke_tc_public_14/cec.log` |

The hidden-entry smoke loaded the packaged R28 wrapper and
`configs/pipelines_r28_gated_r27.yaml`, accepted the R28 post-pass on
`tc_public_14`, selected `2073` nodes at level `15`, and passed CEC.

## Conclusion

R28 passes the release gates and becomes the current formal package candidate.
Use `final_selector_v6_20260626` and the new `submit_sharecone.zip` after the
release commit is tagged.
