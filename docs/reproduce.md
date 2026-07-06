# Reproduce R30b Final Release

This branch packages the R30b guarded ODC-style post-pass entrypoint as the
formal `submit_sharecone.zip`.

## Public Evaluation

The formal release was verified with the public cases at:

```text
C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public
```

```powershell
py -3 tools\verify_all_cec.py `
  --abc submit\bin\abc.exe `
  --cases C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public `
  --outputs results\final_public `
  --log logs\final_cec.log `
  --timeout 300
```

Expected public metrics:

- selected AIG nodes: `37097`
- total selected levels: `275`
- max selected level: `20`
- CEC: `30/30`
- fallback: `0`
- crash/timeout/CEC fail: `0/0/0`

## Release Packaging

The formal package was generated after R30b release integration approval by
running `tools/package_submit.py`, compressing `submit/*`, and verifying the
packaged and zip-extracted outputs.

```powershell
py -3 tools\package_submit.py `
  --abc submit\bin\abc.exe `
  --config configs\final_selector.yaml `
  --pipelines configs\pipelines.yaml `
  --results results\final_public `
  --metrics reports\final_metrics.csv `
  --scoreboard reports\final_scoreboard.xlsx `
  --cec-log logs\final_cec.log `
  --failure-cases reports\failure_cases.md `
  --out submit

Compress-Archive -Path submit\* -DestinationPath submit_sharecone.zip -Force
Get-FileHash submit_sharecone.zip -Algorithm SHA256
```

Package verification:

```powershell
py -3 tools\verify_all_cec.py --abc submit\bin\abc.exe --cases C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public --outputs submit\results\final_public --log submit\logs\reproduce_cec.log --timeout 300

cd submit
py -3 tools\verify_all_cec.py --abc bin\abc.exe --cases C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public --outputs results\final_public --log logs\reproduce_cec_inside.log --timeout 300
cd ..
```

The zip was extracted and verified from both repository-root and inside-package
entrypoints:

```text
logs\r30b_formal_zip_extract_cec.log
logs\r30b_formal_zip_extract_inside_cec.log
```

Final packaged archive:

```text
submit_sharecone.zip
SHA256: D19E2732C825A0004A0C83F0A7C20475C364DD0127EC686DCFF4F6D7611A83A0
```

Packaged ABC:

```text
submit\bin\abc.exe
SHA256: C21C9F2B28F2669D8F99D7587CBBC496672F5D01E45248D7D028B37FDFFF2E3F
Build: /MT Release, no Debug CRT dependency
```

## Hidden/Single Case Interface

Place a BLIF as `input.blif` and run from inside `submit/`:

```powershell
py -3 tools\optimize_one.py --abc bin\abc.exe --input input.blif --output output.blif --selector configs\final_selector.yaml --pipelines configs\pipelines.yaml
```

The R30b entrypoint first runs the v7 optimizer. The v7 optimizer retains the
R28 guarded R27 post-pass and the R29 guarded post-pass. R30b then profiles the
v7 output using coarse multi-output TFI-overlap/cluster features and may try:

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

- Allowed: PI/PO bins, `.names` bins, fanin distribution, cube bins, two-input
  ratio, high-fanin SOP flag, scale grade, coarse runtime-size bins, R7B
  high-overlap structural features, existing coarse selector reasons, and R30b
  coarse cluster/overlap buckets computed from the current output BLIF.
- Forbidden: file names, directory names, hashes, exact line counts, exact
  public-case IDs, exact public fingerprints, port-name predicates, or
  output-order fingerprints.
