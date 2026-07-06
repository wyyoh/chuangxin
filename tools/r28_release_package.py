#!/usr/bin/env python3
"""Guarded R28 Release MT packaging helper.

Default use is non-destructive plan mode. Formal mode can overwrite submit/
and submit_sharecone.zip only when the caller passes the explicit confirmation
token printed by --plan-only.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


EXPECTED = {
    "nodes": 37464,
    "max_level": 20,
    "cec": 30,
    "fallback": 0,
    "wins": 4,
    "ties": 26,
    "losses": 0,
    "gain_vs_v5_release": 104,
    "gain_excluding_best": 21,
    "gain_excluding_top2": 10,
    "abc_sha256": "C21C9F2B28F2669D8F99D7587CBBC496672F5D01E45248D7D028B37FDFFF2E3F",
    "confirm_token": "R28_RELEASE_MT_FORMAL_20260625",
}

DEFAULT_RELEASE_ABC = Path("C:/Users/yy257/abc_r7b_candidate_release_r28_20260625/abc.exe")
DEFAULT_CASES = Path("C:/Users/yy257/cpipc_r28_v5_remeasure/local_data/tc_public")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_text_bytes(path: Path) -> str:
    return path.read_bytes().decode("latin1", errors="ignore")


def count_log(path: Path) -> dict[str, int]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return {
        "passed_true": len(re.findall(r"passed=True", text)),
        "equivalent": len(re.findall(r"Networks are equivalent", text)),
        "bad": len(
            re.findall(
                r"NOT EQUIVALENT|failed|Error|Assertion|Debug Assertion|timeout",
                text,
                flags=re.IGNORECASE,
            )
        ),
    }


def run(cmd: list[str], cwd: Path, log: Path | None = None) -> None:
    print("+ " + " ".join(cmd), flush=True)
    if log is None:
        subprocess.run(cmd, cwd=cwd, check=True)
        return
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w", encoding="utf-8", errors="ignore") as handle:
        subprocess.run(cmd, cwd=cwd, check=True, stdout=handle, stderr=subprocess.STDOUT)


def git_status(cwd: Path) -> str:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def ps_quote(path: Path) -> str:
    return "'" + str(path).replace("'", "''") + "'"


def powershell_compress(src_glob: Path, dst_zip: Path, cwd: Path) -> None:
    command = (
        f"Compress-Archive -Path {ps_quote(src_glob)} "
        f"-DestinationPath {ps_quote(dst_zip)} -Force"
    )
    run(["powershell", "-NoProfile", "-Command", command], cwd)


def powershell_expand(src_zip: Path, dst_dir: Path, cwd: Path) -> None:
    command = (
        f"Expand-Archive -Path {ps_quote(src_zip)} "
        f"-DestinationPath {ps_quote(dst_dir)} -Force"
    )
    run(["powershell", "-NoProfile", "-Command", command], cwd)


def remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def copy_file(src: Path, dst: Path) -> None:
    if not src.exists():
        raise SystemExit(f"missing required file: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_tree(src: Path, dst: Path) -> None:
    if not src.exists():
        raise SystemExit(f"missing required directory: {src}")
    remove_path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)


def metrics_summary(path: Path) -> dict[str, Any]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SystemExit(f"metrics file has no rows: {path}")
    nodes = sum(int(row["selected_nodes"]) for row in rows)
    levels = [int(row["selected_levels"]) for row in rows]
    fallback = sum(1 for row in rows if row.get("fallback_reason") or row.get("status") == "fallback")
    cec_fail = sum(1 for row in rows if str(row.get("cec_pass", "")).lower() != "true")
    runtime_sum = sum(float(row.get("opt_runtime_sec") or 0.0) for row in rows)
    runtime_max = max(float(row.get("opt_runtime_sec") or 0.0) for row in rows)
    peak_rss = max(float(row.get("peak_mem_mb") or 0.0) for row in rows)
    return {
        "rows": len(rows),
        "nodes": nodes,
        "level_sum": sum(levels),
        "max_level": max(levels),
        "fallback": fallback,
        "cec_fail": cec_fail,
        "opt_runtime_sum": runtime_sum,
        "opt_runtime_max": runtime_max,
        "peak_rss_max": peak_rss,
    }


def compare_with_v5(r28_metrics: Path, v5_metrics: Path) -> dict[str, Any]:
    with r28_metrics.open(newline="", encoding="utf-8") as handle:
        r28_rows = {row["case"]: row for row in csv.DictReader(handle)}
    with v5_metrics.open(newline="", encoding="utf-8") as handle:
        v5_rows = list(csv.DictReader(handle))
    deltas: list[int] = []
    wins = ties = losses = 0
    winning_cases: list[dict[str, Any]] = []
    for row in v5_rows:
        case = row["case"]
        r28 = r28_rows[case]
        delta = int(r28["selected_nodes"]) - int(row["selected_nodes"])
        deltas.append(delta)
        if delta < 0:
            wins += 1
            winning_cases.append(
                {
                    "case": case,
                    "node_delta": delta,
                    "level_delta": int(r28["selected_levels"]) - int(row["selected_levels"]),
                }
            )
        elif delta == 0:
            ties += 1
        else:
            losses += 1
    gains = sorted((-delta for delta in deltas), reverse=True)
    return {
        "gain": -sum(deltas),
        "wins": wins,
        "ties": ties,
        "losses": losses,
        "gain_excluding_best": sum(gains[1:]),
        "gain_excluding_top2": sum(gains[2:]),
        "winning_cases": winning_cases,
    }


def check_release_abc(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"ABC binary is missing: {path}")
    content = read_text_bytes(path)
    result = {
        "path": str(path),
        "sha256": sha256(path),
        "has_debug_crt": any(
            token in content
            for token in ["ucrtbased.dll", "VCRUNTIME140D.dll", "MSVCP140D.dll"]
        ),
        "has_dynamic_vc_crt": any(token in content for token in ["VCRUNTIME140.dll", "MSVCP140.dll"]),
        "has_r7win": "r7win" in content,
    }
    if result["sha256"] != EXPECTED["abc_sha256"]:
        raise SystemExit(f"unexpected ABC SHA256: {result['sha256']}")
    if result["has_debug_crt"]:
        raise SystemExit("ABC binary contains Debug CRT strings")
    if result["has_dynamic_vc_crt"]:
        raise SystemExit("ABC binary contains dynamic VC CRT strings")
    if not result["has_r7win"]:
        raise SystemExit("ABC binary does not contain r7win support")
    return result


def check_evidence(args: argparse.Namespace) -> dict[str, Any]:
    metrics = metrics_summary(args.metrics_source)
    if metrics["rows"] != 30:
        raise SystemExit(f"expected 30 metrics rows, got {metrics['rows']}")
    if metrics["nodes"] != EXPECTED["nodes"]:
        raise SystemExit(f"expected {EXPECTED['nodes']} nodes, got {metrics['nodes']}")
    if metrics["max_level"] != EXPECTED["max_level"]:
        raise SystemExit(f"expected max level {EXPECTED['max_level']}, got {metrics['max_level']}")
    if metrics["fallback"] != EXPECTED["fallback"]:
        raise SystemExit(f"expected fallback 0, got {metrics['fallback']}")
    if metrics["cec_fail"] != 0:
        raise SystemExit(f"metrics contain CEC failures: {metrics['cec_fail']}")

    cec = count_log(args.cec_log_source)
    if cec["passed_true"] != EXPECTED["cec"] or cec["bad"] != 0:
        raise SystemExit(f"unexpected CEC log summary: {cec}")

    delta = compare_with_v5(args.metrics_source, args.v5_metrics_source)
    for key in ["gain", "wins", "ties", "losses", "gain_excluding_best", "gain_excluding_top2"]:
        expected_key = "gain_vs_v5_release" if key == "gain" else key
        if delta[key] != EXPECTED[expected_key]:
            raise SystemExit(f"unexpected {key}: {delta[key]} != {EXPECTED[expected_key]}")

    abc = check_release_abc(args.abc)
    return {"metrics": metrics, "cec": cec, "delta": delta, "abc": abc}


def build_paths(args: argparse.Namespace) -> dict[str, Path]:
    if args.mode == "formal":
        return {
            "results": Path("results/final_public"),
            "metrics": Path("reports/final_metrics.csv"),
            "scoreboard": Path("reports/final_scoreboard.xlsx"),
            "cec_log": Path("logs/final_cec.log"),
            "failure_cases": Path("reports/failure_cases.md"),
            "submit": Path("submit"),
            "zip": Path("submit_sharecone.zip"),
            "extract": Path("scratch/r28_formal_zip_extract_check"),
            "root_cec": Path("submit/logs/reproduce_cec.log"),
            "inside_cec": Path("submit/logs/reproduce_cec_inside.log"),
            "zip_root_cec": Path("logs/r28_formal_zip_extract_cec.log"),
            "zip_inside_cec": Path("logs/r28_formal_zip_extract_inside_cec.log"),
            "hidden_dir": Path("logs/r28_formal_zip_hidden_smoke_tc_public_14"),
            "summary": Path("reports/r28_formal_release_summary.json"),
        }
    root = args.work_root
    return {
        "results": root / "results" / "final_public",
        "metrics": root / "reports" / "final_metrics.csv",
        "scoreboard": root / "reports" / "final_scoreboard.xlsx",
        "cec_log": root / "logs" / "final_cec.log",
        "failure_cases": root / "reports" / "failure_cases.md",
        "submit": root / "submit",
        "zip": root / "submit_sharecone.zip",
        "extract": root / "zip_extract",
        "root_cec": root / "submit" / "logs" / "reproduce_cec.log",
        "inside_cec": root / "submit" / "logs" / "reproduce_cec_inside.log",
        "zip_root_cec": root / "logs" / "zip_extract_cec.log",
        "zip_inside_cec": root / "logs" / "zip_extract_inside_cec.log",
        "hidden_dir": root / "logs" / "zip_hidden_smoke_tc_public_14",
        "summary": root / "reports" / "r28_release_package_helper_summary.json",
    }


def stage_release_inputs(args: argparse.Namespace, paths: dict[str, Path]) -> None:
    copy_tree(args.results_source, paths["results"])
    copy_file(args.metrics_source, paths["metrics"])
    copy_file(args.scoreboard_source, paths["scoreboard"])
    copy_file(args.cec_log_source, paths["cec_log"])
    copy_file(args.failure_cases_source, paths["failure_cases"])


def run_package_and_checks(args: argparse.Namespace, paths: dict[str, Path], cwd: Path) -> dict[str, Any]:
    for key in ["results", "submit", "extract"]:
        remove_path(paths[key])
    for key in ["metrics", "scoreboard", "cec_log", "failure_cases", "zip", "summary"]:
        remove_path(paths[key])
    stage_release_inputs(args, paths)

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

    package_abc = paths["submit"] / "bin" / "abc.exe"
    packaged = {
        "abc_sha256": sha256(package_abc),
        "r28_wrapper_present": (paths["submit"] / "tools" / "optimize_one_r28_gated_r27_candidate.py").exists(),
        "r28_pipeline_present": (paths["submit"] / "configs" / "pipelines_r28_gated_r27.yaml").exists(),
    }
    if packaged["abc_sha256"] != EXPECTED["abc_sha256"]:
        raise SystemExit(f"packaged ABC SHA mismatch: {packaged['abc_sha256']}")
    if not packaged["r28_wrapper_present"] or not packaged["r28_pipeline_present"]:
        raise SystemExit(f"missing packaged R28 dependency: {packaged}")

    run(
        [
            sys.executable,
            "tools/verify_all_cec.py",
            "--abc",
            str(package_abc),
            "--cases",
            str(args.cases),
            "--outputs",
            str(paths["submit"] / "results" / "final_public"),
            "--log",
            str(paths["root_cec"]),
            "--timeout",
            "300",
        ],
        cwd,
    )

    inside_log = paths["inside_cec"].resolve()
    rel_cases = os.path.relpath((cwd / args.cases).resolve(), (cwd / paths["submit"]).resolve())
    run(
        [
            sys.executable,
            "tools/verify_all_cec.py",
            "--abc",
            "bin/abc.exe",
            "--cases",
            rel_cases,
            "--outputs",
            "results/final_public",
            "--log",
            str(inside_log),
            "--timeout",
            "300",
        ],
        paths["submit"],
    )

    powershell_compress(paths["submit"] / "*", paths["zip"], cwd)
    remove_path(paths["extract"])
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
            str(paths["zip_root_cec"]),
            "--timeout",
            "300",
        ],
        cwd,
    )

    zip_inside_log = paths["zip_inside_cec"].resolve()
    zip_rel_cases = os.path.relpath((cwd / args.cases).resolve(), (cwd / paths["extract"]).resolve())
    run(
        [
            sys.executable,
            "tools/verify_all_cec.py",
            "--abc",
            "bin/abc.exe",
            "--cases",
            zip_rel_cases,
            "--outputs",
            "results/final_public",
            "--log",
            str(zip_inside_log),
            "--timeout",
            "300",
        ],
        paths["extract"],
    )

    hidden_dir = paths["hidden_dir"]
    remove_path(hidden_dir)
    hidden_dir.mkdir(parents=True, exist_ok=True)
    hidden_dir_abs = (cwd / hidden_dir).resolve()
    cases_abs = (cwd / args.cases).resolve()
    case_input = cases_abs / "tc_public_14" / "input.blif"
    hidden_output = hidden_dir_abs / "output.blif"
    hidden_metrics = hidden_dir_abs / "metrics.json"
    run(
        [
            sys.executable,
            "tools/optimize_one.py",
            "--abc",
            "bin/abc.exe",
            "--input",
            str(case_input),
            "--output",
            str(hidden_output),
            "--selector",
            "configs/final_selector.yaml",
            "--pipelines",
            "configs/pipelines.yaml",
            "--work-dir",
            str(hidden_dir_abs / "work"),
            "--metrics-json",
            str(hidden_metrics),
            "--case-label",
            "tc_public_14",
            "--opt-timeout",
            "300",
            "--cec-timeout",
            "300",
            "--stats-timeout",
            "120",
        ],
        paths["extract"],
    )
    hidden_cec_log = hidden_dir_abs / "cec.log"
    run(
        [
            str((paths["extract"] / "bin" / "abc.exe").resolve()),
            "-c",
            f"cec {case_input} {hidden_output}",
        ],
        paths["extract"],
        hidden_cec_log,
    )

    summary = {
        "mode": args.mode,
        "zip": str(paths["zip"]),
        "zip_sha256": sha256(paths["zip"]),
        "packaged": packaged,
        "logs": {
            "root_cec": {"path": str(paths["root_cec"]), **count_log(paths["root_cec"])},
            "inside_cec": {"path": str(paths["inside_cec"]), **count_log(paths["inside_cec"])},
            "zip_root_cec": {"path": str(paths["zip_root_cec"]), **count_log(paths["zip_root_cec"])},
            "zip_inside_cec": {"path": str(paths["zip_inside_cec"]), **count_log(paths["zip_inside_cec"])},
            "hidden_smoke_cec": {"path": str(hidden_cec_log), **count_log(hidden_cec_log)},
        },
        "hidden_smoke_metrics": json.loads(hidden_metrics.read_text(encoding="utf-8")),
    }
    paths["summary"].parent.mkdir(parents=True, exist_ok=True)
    paths["summary"].write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["dry-run", "formal"], default="dry-run")
    parser.add_argument("--plan-only", action="store_true", default=True)
    parser.add_argument("--execute", action="store_false", dest="plan_only")
    parser.add_argument("--confirm-overwrite-submit", default="")
    parser.add_argument("--allow-dirty", action="store_true")
    parser.add_argument("--abc", type=Path, default=DEFAULT_RELEASE_ABC)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--selector", type=Path, default=Path("configs/final_selector.yaml"))
    parser.add_argument("--pipelines", type=Path, default=Path("configs/pipelines.yaml"))
    parser.add_argument("--results-source", type=Path, default=Path("results_candidate/r28_release_mt_full_public"))
    parser.add_argument("--metrics-source", type=Path, default=Path("reports/r28_release_mt_full_public_metrics.csv"))
    parser.add_argument("--v5-metrics-source", type=Path, default=Path("reports/r28_v5_release_mt_full_public_metrics.csv"))
    parser.add_argument("--scoreboard-source", type=Path, default=Path("reports/r28_release_mt_scoreboard.xlsx"))
    parser.add_argument("--cec-log-source", type=Path, default=Path("logs/r28_release_mt_full_public_cec.log"))
    parser.add_argument("--failure-cases-source", type=Path, default=Path("reports/r28_release_mt_failure_cases.md"))
    parser.add_argument("--work-root", type=Path, default=Path("scratch/r28_release_package_helper_dryrun"))
    args = parser.parse_args()

    cwd = Path.cwd()
    evidence = check_evidence(args)
    paths = build_paths(args)
    plan = {
        "mode": args.mode,
        "destructive": args.mode == "formal",
        "plan_only": args.plan_only,
        "confirm_token_required_for_formal": EXPECTED["confirm_token"],
        "expected": EXPECTED,
        "paths": {key: str(value) for key, value in paths.items()},
        "evidence": evidence,
    }
    print(json.dumps(plan, indent=2))
    if args.plan_only:
        return 0

    if args.mode == "formal":
        if args.confirm_overwrite_submit != EXPECTED["confirm_token"]:
            raise SystemExit(
                "formal mode requires --confirm-overwrite-submit "
                + EXPECTED["confirm_token"]
            )
        if not args.allow_dirty and git_status(cwd):
            raise SystemExit("formal mode requires a clean worktree or --allow-dirty")

    if not args.cases.exists():
        raise SystemExit(f"cases directory is missing: {args.cases}")

    run_package_and_checks(args, paths, cwd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
