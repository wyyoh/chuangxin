# R28 Release MT ABC Reproduction

## Objective

Resolve the R28 release-packaging blocker caused by the Debug CRT ABC binary,
without modifying `submit/` or `submit_sharecone.zip`.

## Baseline

- Candidate branch: `candidate/r28-gated-r27`
- Candidate evidence commit: `94d2036a680223216a099785307ce8b4de6523a1`
- Baseline tag: `final_selector_v5_20260624`
- Baseline commit: `2722491e9079052e63073344c69eb5c2e10d50a4`
- Previous R28 candidate with Debug ABC: `37604` nodes, level sum `279`,
  max level `20`, CEC `30/30`, fallback `0`.

## Commands

Release ABC configure/build:

```powershell
cmd.exe /c "call D:\Microsoft Visual Studio\2022\Community\Common7\Tools\VsDevCmd.bat -arch=x64 -host_arch=x64 && set CPIPC_ROOT=C:\Users\yy257\cpipc_r28_candidate&& set CPIPC_PYTHON=C:\Users\yy257\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe&& D:\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe -S C:\Users\yy257\abc_r7b_candidate -B C:\Users\yy257\abc_r7b_candidate_release_r28_20260625 -G Ninja -DCMAKE_MAKE_PROGRAM=D:\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe -DABC_SKIP_TESTS=ON -DREADLINE_FOUND=FALSE -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_FLAGS_RELEASE=/MT /O2 /Ob2 /DNDEBUG -DCMAKE_CXX_FLAGS_RELEASE=/MT /O2 /Ob2 /DNDEBUG -DCMAKE_EXE_LINKER_FLAGS_RELEASE=/INCREMENTAL:NO"
cmd.exe /c "call D:\Microsoft Visual Studio\2022\Community\Common7\Tools\VsDevCmd.bat -arch=x64 -host_arch=x64 && D:\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe -C C:\Users\yy257\abc_r7b_candidate_release_r28_20260625 abc"
```

R28 full public with Release ABC:

```powershell
py -3 tools\eval_public_optimize_one.py --abc C:\Users\yy257\abc_r7b_candidate_release_r28_20260625\abc.exe --cases C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public --selector configs\final_selector.yaml --pipelines configs\pipelines.yaml --out results_candidate\r28_release_mt_full_public --csv reports\r28_release_mt_full_public_metrics.csv --opt-timeout 300 --cec-timeout 300 --stats-timeout 120
py -3 tools\verify_all_cec.py --abc C:\Users\yy257\abc_r7b_candidate_release_r28_20260625\abc.exe --cases C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public --outputs results_candidate\r28_release_mt_full_public --log logs\r28_release_mt_full_public_cec.log --timeout 300
```

V5 comparison with the same Release ABC:

```powershell
py -3 tools\eval_public_optimize_one.py --abc C:\Users\yy257\abc_r7b_candidate_release_r28_20260625\abc.exe --cases C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public --selector configs\final_selector.yaml --pipelines configs\pipelines.yaml --out results_research\R28_v5_release_mt_full_public --csv reports\r28_v5_release_mt_full_public_metrics.csv --opt-timeout 300 --cec-timeout 300 --stats-timeout 120
py -3 tools\verify_all_cec.py --abc C:\Users\yy257\abc_r7b_candidate_release_r28_20260625\abc.exe --cases C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public --outputs results_research\R28_v5_release_mt_full_public --log logs\r28_v5_release_mt_full_public_cec.log --timeout 300
```

## Input Data

- ABC source: `C:\Users\yy257\abc_r7b_candidate`
- ABC source commit: `9546db421c4f1b3d8736b6af2f9af875ddec8ec2`
- Build dir: `C:\Users\yy257\abc_r7b_candidate_release_r28_20260625`
- Public cases: `C:\Users\yy257\cpipc_r28_v5_remeasure\local_data\tc_public`

## Results

Release ABC binary:

- Path: `C:\Users\yy257\abc_r7b_candidate_release_r28_20260625\abc.exe`
- SHA256: `C21C9F2B28F2669D8F99D7587CBBC496672F5D01E45248D7D028B37FDFFF2E3F`
- Size: `11186176` bytes
- CMake build type: `Release`
- MSVC runtime: `/MT`
- Debug CRT strings found: `0`
- Dynamic VC CRT strings found: `0`
- `r7win -h`: return code `0`, usage present
- small BLIF `r7win -profile` plus CEC: return code `0`, equivalent

Layered public results:

| Run | Nodes | Level Sum | Max Level | CEC | Fallback | Opt Runtime | Peak RSS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| v5 Debug remeasure | 37708 | 281 | 20 | 30/30 | 0 | 350.330218s | 52.098 MB |
| v5 Release ABC | 37568 | 280 | 20 | 30/30 | 0 | 74.356008s | 47.227 MB |
| R28 Debug ABC | 37604 | 279 | 20 | 30/30 | 0 | 344.568115s | 52.035 MB |
| R28 Release ABC | 37464 | 278 | 20 | 30/30 | 0 | 76.225724s | 47.309 MB |

Layered gains:

| Comparison | Total Gain | Wins / Ties / Losses | Gain Excluding Best | Gain Excluding Top2 | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| v5 Release ABC vs v5 Debug remeasure | 140 | 1 / 29 / 0 | 0 | 0 | Binary/build effect, entirely `tc_public_23`. |
| R28 Release ABC vs v5 Release ABC | 104 | 4 / 26 / 0 | 21 | 10 | R28 post-pass effect: `tc_public_14/15/26/30`. |
| R28 Release ABC vs v5 Debug remeasure | 244 | 5 / 25 / 0 | 104 | 21 | Combined Release ABC plus R28 post-pass. |

## Correctness

- R28 Release ABC evaluator CEC: `30/30`
- R28 Release ABC independent CEC: `30/30`
- v5 Release ABC independent CEC: `30/30`
- Release ABC smoke-only CEC: `6/6`
- `NOT EQUIVALENT` / failed / Error / Assertion / Debug lines in checked CEC
  logs: `0`

## Risk

The prior Debug CRT packaging blocker is resolved for execution evidence by the
new `/MT Release` ABC. It is not yet a formal release artifact because it has
not been copied into `submit/`, packaged, or verified from inside a generated
submit archive.

The 140-node gain from replacing the ABC binary is concentrated in one case.
Treat that as a binary/rebuild improvement, not as selector generalization.
The R28 post-pass improvement remains separate and passes excluding-best and
excluding-top-two gates on the Release ABC baseline.

## Selector Eligibility

The R28 selector gate remains unchanged:

- no filename, hash, public case ID, or exact fingerprint condition;
- post-pass applies only through coarse v5 selector reason/variant buckets;
- post-pass acceptance still requires CEC, node decrease, and no level increase.

## Conclusion

Decision label: `promote-to-candidate`.

R28 with the `/MT Release` ABC is a stronger candidate than the previous Debug
ABC evidence: `37464` nodes, level sum `278`, max level `20`, CEC `30/30`, and
fallback `0`. It is ready for release-integration packaging review, but still
must not overwrite `submit/` or `submit_sharecone.zip` until explicit packaging
approval is given.

## Next Action

If approved, enter release packaging by copying the verified `/MT Release` ABC
into the release branch/package, regenerating `submit/` once, computing SHA256,
and rerunning packaged CEC from the generated archive.
