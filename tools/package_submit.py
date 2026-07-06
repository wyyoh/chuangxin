#!/usr/bin/env python3
"""Create the submit directory from verified final artifacts."""

from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path


SCRIPT_NAMES = [
    "optimize_one.py",
    "optimize_one_r30b_release.py",
    "optimize_one_r29_postpass_candidate.py",
    "optimize_one_r28_gated_r27_candidate.py",
    "optimize_one_r8_order_choosebest.py",
    "run_abc_case.py",
    "parse_abc_stats.py",
    "eval_public.py",
    "extract_blif_features.py",
    "extract_r7b_features.py",
    "r25_route_d_divisor_profile.py",
    "r7b_port_order_stress.py",
    "select_pipeline.py",
    "verify_all_cec.py",
]


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--abc", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--pipelines", default=Path("configs/pipelines.yaml"), type=Path)
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--metrics", default=Path("reports/final_metrics.csv"), type=Path)
    parser.add_argument("--scoreboard", default=Path("reports/final_scoreboard.xlsx"), type=Path)
    parser.add_argument("--cec-log", default=Path("logs/final_cec.log"), type=Path)
    parser.add_argument("--failure-cases", default=Path("reports/failure_cases.md"), type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    abc_source = args.abc
    cached_abc: Path | None = None
    try:
        abc_resolved = args.abc.resolve()
        out_resolved = args.out.resolve()
        if abc_resolved.is_relative_to(out_resolved):
            suffix = ".exe" if args.abc.suffix.lower() == ".exe" else ""
            handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            handle.close()
            cached_abc = Path(handle.name)
            shutil.copy2(args.abc, cached_abc)
            abc_source = cached_abc
    except AttributeError:
        pass

    if args.out.exists():
        shutil.rmtree(args.out)
    args.out.mkdir(parents=True)

    abc_name = "abc.exe" if args.abc.suffix.lower() == ".exe" else "abc"
    copy_file(abc_source, args.out / "bin" / abc_name)
    copy_file(args.config, args.out / "configs" / "final_selector.yaml")
    copy_file(args.pipelines, args.out / "configs" / "pipelines.yaml")
    r28_pipelines = Path("configs/pipelines_r28_gated_r27.yaml")
    if r28_pipelines.exists():
        copy_file(r28_pipelines, args.out / "configs" / "pipelines_r28_gated_r27.yaml")
    r29_pipelines = Path("configs/pipelines_r29_postpass_candidate.yaml")
    if r29_pipelines.exists():
        copy_file(r29_pipelines, args.out / "configs" / "pipelines_r29_postpass_candidate.yaml")
    for script in SCRIPT_NAMES:
        copy_file(Path("tools") / script, args.out / "tools" / script)

    copy_tree(args.results, args.out / "results" / "final_public")

    required = [
        (args.metrics, args.out / "final_metrics.csv"),
        (args.scoreboard, args.out / "final_scoreboard.xlsx"),
        (args.cec_log, args.out / "final_cec.log"),
        (args.failure_cases, args.out / "failure_cases.md"),
    ]
    for src, dst in required:
        copy_file(src, dst)
    copy_file(Path("docs/sharecone_algorithm.md"), args.out / "docs" / "sharecone_algorithm.md")
    if Path("docs/algorithm.md").exists():
        copy_file(Path("docs/algorithm.md"), args.out / "docs" / "algorithm_design.md")
    copy_file(Path("docs/review_fixes.md"), args.out / "docs" / "review_fixes.md")

    reproduce = f"""# Reproduce

## Environment

- ABC path is passed by parameter. The packaged Windows binary is `bin/{abc_name}`.
- For the R30b formal package, the packaged ABC binary is the verified
  `/MT Release` Windows build recorded in the release notes. It must not be a
  Debug CRT build.
- The optimizer is single-process/single-thread at the wrapper level; it invokes one ABC process per optimization/CEC/stat step.
- Final submission strategy uses `configs/final_selector.yaml`, a coarse feature selector, not offline portfolio search.

## Final Public Verification

From the repository root:

```powershell
python tools/verify_all_cec.py --abc submit/bin/{abc_name} --cases data/tc_public --outputs submit/results/final_public --log submit/logs/reproduce_cec.log
```

From inside `submit/`:

```powershell
python tools/verify_all_cec.py --abc bin/{abc_name} --cases ../data/tc_public --outputs results/final_public --log logs/reproduce_cec.log
```

## Hidden/Single Case Interface

Place a BLIF as `input.blif` and run:

```powershell
python tools/optimize_one.py --abc bin/{abc_name} --input input.blif --output output.blif --selector configs/final_selector.yaml --pipelines configs/pipelines.yaml
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
"""
    (args.out / "reproduce.md").write_text(reproduce, encoding="utf-8")
    if cached_abc is not None:
        cached_abc.unlink(missing_ok=True)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
