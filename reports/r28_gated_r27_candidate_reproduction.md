# R28 Gated R27 Candidate Reproduction

## Objective

Integrate the R28 score-aware gated R27 post-pass as a candidate entrypoint
based on `final_selector_v5_20260624`, then reproduce full public 30 without
generating or overwriting any submit package.

## Baseline

- baseline tag: `final_selector_v5_20260624`
- baseline commit: `2722491e9079052e63073344c69eb5c2e10d50a4`
- baseline nodes: `37708`
- baseline level sum: `281`
- baseline max level: `20`
- baseline CEC: `30/30`
- baseline fallback: `0`

## Candidate

Branch/worktree:

- branch: `candidate/r28-gated-r27`
- worktree: `C:\Users\yy257\cpipc_r28_candidate`

Candidate entrypoint changes:

- `tools/optimize_one.py` now calls the R28 gated R27 wrapper.
- `tools/optimize_one_r28_gated_r27_candidate.py` runs v5 first, then applies
  the R27 post-pass only for the coarse `r7b_plus_r25_inputs` gate.
- `configs/pipelines_r28_gated_r27.yaml` defines the post-pass:
  `mfs; fraig; dc2; balance`.
- `configs/final_selector.yaml` and `configs/pipelines.yaml` remain the v5
  formal selector and pipeline config.

Gate logic:

- apply post-pass when v5 selector reason is
  `r7b_high_overlap_guarded_fraig`; or
- apply post-pass when v5 selector reason starts with `r25_dsd_` and the chosen
  variant is `inputs`.

The gate does not use filenames, hashes, public case IDs, exact public
fingerprints, or port names.

## Commands

Smoke:

```powershell
py -3 tools\eval_public_optimize_one.py `
  --abc submit\bin\abc.exe `
  --cases C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public `
  --case-list reports\r28_candidate_smoke_cases.txt `
  --selector configs\final_selector.yaml `
  --pipelines configs\pipelines.yaml `
  --out results_candidate\r28_gated_r27_smoke `
  --csv reports\r28_gated_r27_smoke_metrics.csv `
  --opt-timeout 300 --cec-timeout 300 --stats-timeout 120
```

Full public:

```powershell
py -3 tools\eval_public_optimize_one.py `
  --abc submit\bin\abc.exe `
  --cases C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public `
  --selector configs\final_selector.yaml `
  --pipelines configs\pipelines.yaml `
  --out results_candidate\r28_gated_r27_full_public `
  --csv reports\r28_gated_r27_full_public_metrics.csv `
  --opt-timeout 300 --cec-timeout 300 --stats-timeout 120
```

Independent CEC:

```powershell
py -3 tools\verify_all_cec.py `
  --abc submit\bin\abc.exe `
  --cases C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public `
  --outputs results_candidate\r28_gated_r27_full_public `
  --log logs\r28_gated_r27_full_public_cec.log `
  --timeout 300
```

## Input Data

- Public cases: `C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public`
- ABC binary: `submit\bin\abc.exe`
- Selector: `configs\final_selector.yaml`
- Main pipelines: `configs\pipelines.yaml`
- R28 post-pass pipelines: `configs\pipelines_r28_gated_r27.yaml`

## Release Packaging Blocker

After candidate reproduction, the local `submit\bin\abc.exe` used in this
candidate worktree was audited because a Microsoft Visual C++ Debug Assertion
dialog appeared from the same binary family. The audited binary has SHA256
`85F59E6291A1C4B10B757BF163D14D2152EAA974B21BC6F4E13F44EC49969805` and contains
Debug CRT dependency strings: `ucrtbased.dll`, `VCRUNTIME140D.dll`, and
`MSVCP140D.dll`.

The follow-up binary audit is recorded in
`reports\r28_abc_binary_audit.csv`. In the checked worktrees, every ABC binary
that both runs and prints `r7win -h` has the same Debug CRT hash above. The
existing non-Debug 195 MB ABC binaries with SHA256
`89E2ED2D2630E668717FBA334C547B3D482D4EEF9A601A2792E64ADDE00FA89A` do not expose
Debug CRT strings, but they return `-1073741515` on this machine before printing
`r7win -h`, which indicates a local loader/dependency failure.

This does not invalidate the recorded node/level/CEC evidence, but it does mean
the current candidate worktree is not release-package ready. Before any formal
packaging, build or locate a non-Debug ABC that is runnable in a clean
environment and supports `r7win`, then rerun full public metrics, independent
CEC, and packaged CEC from the release package. Do not reuse this Debug CRT
binary in a formal submit archive.

Follow-up status: this blocker has been resolved for candidate evidence by
building a separate `/MT Release` ABC at
`C:\Users\yy257\abc_r7b_candidate_release_r28_20260625\abc.exe`. The binary has
SHA256 `C21C9F2B28F2669D8F99D7587CBBC496672F5D01E45248D7D028B37FDFFF2E3F`,
contains no checked Debug CRT or dynamic VC CRT dependency strings, prints
`r7win -h`, and passes small BLIF CEC. See
`reports\r28_release_mt_abc_reproduction.md`.

## Results

| Metric | v5 tag | R28 candidate | Delta |
| --- | ---: | ---: | ---: |
| Selected nodes | 37708 | 37604 | -104 |
| Level sum | 281 | 279 | -2 |
| Max level | 20 | 20 | 0 |
| CEC pass | 30/30 | 30/30 | 0 |
| Fallback | 0 | 0 | 0 |
| Inner fallback | 0 | 0 | 0 |
| Bad entry return code | 0 | 0 | 0 |
| Wins / ties / losses | n/a | 4 / 26 / 0 | n/a |
| Gain excluding best case | n/a | 21 | n/a |
| Gain excluding top two cases | n/a | 10 | n/a |
| R28 accepted / rejected / skipped | n/a | 4 / 1 / 25 | n/a |
| Opt runtime | 330.892152s | 344.568115s | +13.675963s |
| Opt runtime vs R28 v5 remeasure | 350.330218s | 344.568115s | -5.762103s |
| Runtime warnings >300s | 0 | 0 | 0 |
| RSS warnings >1024 MB | 0 | 0 | 0 |
| Peak RSS max | 52.211 MB | 52.035 MB | -0.176 MB |

Release ABC rerun:

| Run | Nodes | Level Sum | Max Level | CEC | Fallback | Opt Runtime |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| v5 Debug remeasure | 37708 | 281 | 20 | 30/30 | 0 | 350.330218s |
| v5 `/MT Release` ABC | 37568 | 280 | 20 | 30/30 | 0 | 74.356008s |
| R28 `/MT Release` ABC | 37464 | 278 | 20 | 30/30 | 0 | 76.225724s |

The release-ABC binary itself contributes `140` nodes versus the v5 Debug
remeasure, all from `tc_public_23`. The R28 post-pass contributes another `104`
nodes versus the v5 Release-ABC baseline, with wins on four cases and
gain-excluding-best/top2 of `21/10`. Combined, the current release-grade
candidate evidence is `37464` nodes and level sum `278`.

Winning cases:

| Case | Node Delta | Level Delta | Runtime Delta vs v5 tag | Post-pass |
| --- | ---: | ---: | ---: | --- |
| `tc_public_14` | -83 | -1 | +6.181736s | `r28_r27_mfs_fraig_dc2_bal` |
| `tc_public_30` | -11 | -1 | +1.277007s | `r28_r27_mfs_fraig_dc2_bal` |
| `tc_public_15` | -9 | 0 | +1.635336s | `r28_r27_mfs_fraig_dc2_bal` |
| `tc_public_26` | -1 | 0 | +0.975832s | `r28_r27_mfs_fraig_dc2_bal` |

## Correctness

- Evaluator CEC: `30/30`
- Independent CEC: `30/30`
- Independent CEC NOT EQUIVALENT / failed / Error lines: `0`
- Fallback / inner fallback / bad entry: `0/0/0`
- Full-public stderr length: `0`

## Risk

This candidate is materially lighter than broad R27:

- broad R27 gained `236` nodes but added about `155.5s` public opt time versus
  the v5 tag run;
- gated R28 gains `104` nodes and adds `13.675963s` versus the v5 tag run;
- in the same R28 remeasure environment, gated R28 measured `5.762103s` faster
  than v5, but runtime should still be treated as noisy and rechecked before
  release packaging.

The main residual risk is concentration: the best case contributes `83/104`
nodes. The candidate still passes excluding-best and excluding-top-two gates
with `21/10` remaining gain.

## Selector Eligibility

Eligible for candidate review:

- no case names or hashes in the gate;
- no exact public fingerprints;
- no exact PI/PO/name combinations;
- post-pass accepted only after CEC, node decrease, and level non-regression;
- max level remains `20`;
- no broad losses.

## Conclusion

Decision label: `promote-to-candidate`.

The R28 gated R27 candidate passes full-public candidate reproduction and
independent CEC. It is ready for release-integration review, but it is not a
formal final because `submit/` and `submit_sharecone.zip` were not regenerated.

## Next Action

If this runtime tradeoff is accepted, enter release packaging from this
candidate branch using the verified `/MT Release` ABC, regenerate `submit/`
once, compute the archive SHA256, and rerun packaged CEC. Do not overwrite
`submit/` or `submit_sharecone.zip` until explicit release packaging approval
is given.
