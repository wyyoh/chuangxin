#!/usr/bin/env python3
"""Guarded R11S release packaging helper.

Default mode is non-destructive. Formal mode requires an explicit confirmation
flag before it can overwrite submit/ or submit_sharecone.zip.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


EXPECTED = {
    "nodes": 41004,
    "max_level": 20,
    "cec": 30,
    "fallback": 0,
    "old_submit_sha256": "4B6236AF057009318EA50E39FFC43FFA3A74708B49A07C2F08FD386AB6D1AF8A",
}


def run(cmd: list[str], cwd: Path) -> None:
    print("+ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def git_status(cwd: Path) -> str:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def powershell_compress(src_glob: Path, dst_zip: Path, cwd: Path) -> None:
    command = (
        f"Compress-Archive -Path '{src_glob}' "
        f"-DestinationPath '{dst_zip}' -Force"
    )
    run(["powershell", "-NoProfile", "-Command", command], cwd)


def powershell_expand(src_zip: Path, dst_dir: Path, cwd: Path) -> None:
    command = (
        f"Expand-Archive -Path '{src_zip}' "
        f"-DestinationPath '{dst_dir}' -Force"
    )
    run(["powershell", "-NoProfile", "-Command", command], cwd)


def powershell_hash(path: Path, cwd: Path) -> str:
    command = (
        f"(Get-FileHash '{path}' -Algorithm SHA256).Hash"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def build_paths(args: argparse.Namespace) -> dict[str, Path]:
    if args.mode == "formal":
        return {
            "results": Path("results/final_public"),
            "metrics": Path("reports/final_metrics.csv"),
            "cec_log": Path("logs/final_cec.log"),
            "failure_cases": Path("reports/failure_cases.md"),
            "scoreboard": Path("reports/final_scoreboard.xlsx"),
            "submit": Path("submit"),
            "zip": Path("submit_sharecone.zip"),
            "extract": Path("scratch/r11s_formal_zip_extract_check"),
            "zip_cec_log": Path("logs/r11s_formal_zip_extract_cec.log"),
            "zip_inside_cec_log": Path("logs/r11s_formal_zip_extract_inside_cec.log"),
        }
    root = Path(args.work_root)
    return {
        "results": root / "results" / "final_public",
        "metrics": root / "reports" / "final_metrics.csv",
        "cec_log": root / "logs" / "final_cec.log",
        "failure_cases": root / "reports" / "failure_cases.md",
        "scoreboard": root / "reports" / "final_scoreboard.xlsx",
        "submit": root / "submit",
        "zip": root / "submit_sharecone_dryrun.zip",
        "extract": root / "zip_extract",
        "zip_cec_log": root / "logs" / "zip_extract_cec.log",
        "zip_inside_cec_log": root / "logs" / "zip_extract_inside_cec.log",
    }


def remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["dry-run", "formal"], default="dry-run")
    parser.add_argument("--cases", default=Path("local_data/tc_public"), type=Path)
    parser.add_argument("--abc", default=Path("submit/bin/abc.exe"), type=Path)
    parser.add_argument("--selector", default=Path("configs/final_selector.yaml"), type=Path)
    parser.add_argument("--pipelines", default=Path("configs/pipelines.yaml"), type=Path)
    parser.add_argument(
        "--source-scoreboard",
        default=Path("reports/r11s_packaging_dryrun_scoreboard.xlsx"),
        type=Path,
    )
    parser.add_argument(
        "--work-root",
        default=Path("scratch/r11s_release_package_dryrun"),
        type=Path,
    )
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--allow-dirty", action="store_true")
    parser.add_argument("--confirm-overwrite-submit", action="store_true")
    args = parser.parse_args()

    cwd = Path.cwd()
    paths = build_paths(args)
    plan = {
        "mode": args.mode,
        "destructive": args.mode == "formal",
        "requires_confirmation": args.mode == "formal",
        "paths": {key: str(value) for key, value in paths.items()},
        "expected": EXPECTED,
    }
    print(json.dumps(plan, indent=2))
    if args.plan_only:
        return 0

    if args.mode == "formal":
        if not args.confirm_overwrite_submit:
            raise SystemExit(
                "formal mode requires --confirm-overwrite-submit"
            )
        if not args.allow_dirty and git_status(cwd):
            raise SystemExit(
                "formal mode requires a clean worktree, or pass --allow-dirty"
            )

    if not args.cases.exists():
        raise SystemExit(f"cases directory is missing: {args.cases}")
    if not args.abc.exists():
        raise SystemExit(f"ABC binary is missing: {args.abc}")
    if not args.source_scoreboard.exists():
        raise SystemExit(f"scoreboard is missing: {args.source_scoreboard}")

    for key in ["results", "submit", "extract"]:
        remove_path(paths[key])
    for key in ["metrics", "cec_log", "failure_cases", "scoreboard", "zip"]:
        if paths[key].exists():
            remove_path(paths[key])

    paths["metrics"].parent.mkdir(parents=True, exist_ok=True)
    paths["cec_log"].parent.mkdir(parents=True, exist_ok=True)
    paths["failure_cases"].parent.mkdir(parents=True, exist_ok=True)
    paths["scoreboard"].parent.mkdir(parents=True, exist_ok=True)

    run(
        [
            sys.executable,
            "tools/eval_public_optimize_one.py",
            "--abc",
            str(args.abc),
            "--cases",
            str(args.cases),
            "--selector",
            str(args.selector),
            "--pipelines",
            str(args.pipelines),
            "--out",
            str(paths["results"]),
            "--csv",
            str(paths["metrics"]),
            "--opt-timeout",
            "300",
            "--cec-timeout",
            "300",
            "--stats-timeout",
            "120",
        ],
        cwd,
    )
    run(
        [
            sys.executable,
            "tools/verify_all_cec.py",
            "--abc",
            str(args.abc),
            "--cases",
            str(args.cases),
            "--outputs",
            str(paths["results"]),
            "--log",
            str(paths["cec_log"]),
            "--timeout",
            "300",
        ],
        cwd,
    )
    run(
        [
            sys.executable,
            "tools/generate_failure_cases.py",
            "--metrics",
            str(paths["metrics"]),
            "--out",
            str(paths["failure_cases"]),
        ],
        cwd,
    )
    shutil.copy2(args.source_scoreboard, paths["scoreboard"])
    run(
        [
            sys.executable,
            "tools/package_submit.py",
            "--abc",
            str(args.abc),
            "--config",
            str(args.selector),
            "--pipelines",
            str(args.pipelines),
            "--results",
            str(paths["results"]),
            "--metrics",
            str(paths["metrics"]),
            "--scoreboard",
            str(paths["scoreboard"]),
            "--cec-log",
            str(paths["cec_log"]),
            "--failure-cases",
            str(paths["failure_cases"]),
            "--out",
            str(paths["submit"]),
        ],
        cwd,
    )
    powershell_compress(paths["submit"] / "*", paths["zip"], cwd)
    if paths["extract"].exists():
        shutil.rmtree(paths["extract"])
    powershell_expand(paths["zip"], paths["extract"], cwd)
    run(
        [
            sys.executable,
            str(paths["extract"] / "tools" / "verify_all_cec.py"),
            "--abc",
            str(paths["extract"] / "bin" / "abc.exe"),
            "--cases",
            str(args.cases),
            "--outputs",
            str(paths["extract"] / "results" / "final_public"),
            "--log",
            str(paths["zip_cec_log"]),
            "--timeout",
            "300",
        ],
        cwd,
    )
    inside_log = paths["zip_inside_cec_log"].resolve()
    inside_rel_cases = os.path.relpath(
        (cwd / args.cases).resolve(),
        (cwd / paths["extract"]).resolve(),
    )
    run(
        [
            sys.executable,
            "tools/verify_all_cec.py",
            "--abc",
            "bin/abc.exe",
            "--cases",
            inside_rel_cases,
            "--outputs",
            "results/final_public",
            "--log",
            str(inside_log),
            "--timeout",
            "300",
        ],
        paths["extract"],
    )
    print(
        json.dumps(
            {
                "zip_sha256": powershell_hash(paths["zip"], cwd),
                "zip_path": str(paths["zip"]),
                "mode": args.mode,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
