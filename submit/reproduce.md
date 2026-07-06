# Reproduce

## Environment

- ABC path is passed by parameter. The packaged Windows binary is `bin/abc.exe`.
- For the R30b formal package, the packaged ABC binary is the verified
  `/MT Release` Windows build recorded in the release notes. It must not be a
  Debug CRT build.
- The optimizer is single-process/single-thread at the wrapper level; it invokes one ABC process per optimization/CEC/stat step.
- Final submission strategy uses `configs/final_selector.yaml`, a coarse feature selector, not offline portfolio search.

## Final Public Verification

From the repository root:

```powershell
python tools/verify_all_cec.py --abc submit/bin/abc.exe --cases data/tc_public --outputs submit/results/final_public --log submit/logs/reproduce_cec.log
```

From inside `submit/`:

```powershell
python tools/verify_all_cec.py --abc bin/abc.exe --cases ../data/tc_public --outputs results/final_public --log logs/reproduce_cec.log
```

## Hidden/Single Case Interface

Place a BLIF as `input.blif` and run:

```powershell
python tools/optimize_one.py --abc bin/abc.exe --input input.blif --output output.blif --selector configs/final_selector.yaml --pipelines configs/pipelines.yaml
```

For the R30b final, this entrypoint first runs the v7 optimizer. The v7
optimizer keeps the R28 guarded R27 and R29 guarded post-pass dependencies
through `configs/pipelines_r28_gated_r27.yaml` and
`configs/pipelines_r29_postpass_candidate.yaml`. R30b then profiles the v7
output with coarse multi-output TFI-overlap/cluster features and conditionally
loads `configs/pipelines.yaml` for the `r30b_odc_resub_f1` post-pass:

```text
strash; resub -K 8 -N 1 -M 1 -F 1; strash; dc2; rewrite -z; balance
```

The R30b post-pass is accepted only when CEC passes, nodes decrease, and level
does not increase. Non-matching or rejected trials keep the verified v7 output.

Fallback policy:

- candidate crash or timeout -> best verified baseline
- candidate CEC failure -> best verified baseline
- candidate metric regression -> best verified baseline
- identity/original -> last-resort fallback only

Selector constraints:

- Allowed: PI/PO bins, `.names` bins, fanin distribution, cube bins, two-input ratio, high-fanin SOP flag, scale grade, and coarse runtime-size bins derived from name/cube count buckets.
- Forbidden: file names, directory names, hashes, exact line counts, exact public-case PI/PO/names combinations, or exact port-combination fingerprints.
- R30b keeps the v7 coarse selector and adds a guarded post-selector pass only
  for coarse structural buckets: huge high-level low-overlap rows,
  mid-sized high-overlap clusters, and medium clusters. Every selected output is
  still checked by local rollback policy and full public CEC evidence.
- ShareCone and oracle-only search results are not enabled by the final selector.
