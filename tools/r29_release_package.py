#!/usr/bin/env python3
"""Guarded R29 release packaging helper.

Default use is non-destructive dry-run mode. Formal mode can overwrite submit/
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
import tempfile
from pathlib import Path
from typing import Any


EXPECTED = {
    "nodes": 37260,
    "level_sum": 277,
    "max_level": 20,
    "cec": 30,
    "fallback": 0,
    "bad_entry": 0,
    "inner_fallback": 0,
    "wins": 9,
    "ties": 21,
    "losses": 0,
    "gain_vs_v6": 204,
    "gain_excluding_best": 147,
    "gain_excluding_top2": 111,
    "abc_sha256": "C21C9F2B28F2669D8F99D7587CBBC496672F5D01E45248D7D028B37FDFFF2E3F",
    "previous_zip_sha256": "EF7638BC06771F86485588A16786EAD760550CA86EFAD858B93EE1D808AA4E7F",
    "confirm_token": "R29_RELEASE_FORMAL_20260626",
}

DEFAULT_CASES = Path("C:/Users/yy257/cpipc_r28_v5_remeasure/local_data/tc_public")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def count_log(path: Path) -> dict[str, int]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return {
        "equivalent": len(re.findall(r"Networks are equivalent", text)),
        "bad": len(re.findall(r"NOT EQUIVALENT|failed|Error|Assertion|Debug Assertion|timeout", text, flags=re.IGNORECASE)),
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
    result = subprocess.run(["git", "status", "--porcelain"], cwd=cwd, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def ps_quote(path: Path) -> str:
    return "'" + str(path).replace("'", "''") + "'"


def powershell_compress(src_glob: Path, dst_zip: Path, cwd: Path) -> None:
    command = f"Compress-Archive -Path {ps_quote(src_glob)} -DestinationPath {ps_quote(dst_zip)} -Force"
    run(["powershell", "-NoProfile", "-Command", command], cwd)


def powershell_expand(src_zip: Path, dst_dir: Path, cwd: Path) -> None:
    command = f"Expand-Archive -Path {ps_quote(src_zip)} -DestinationPath {ps_quote(dst_dir)} -Force"
    run(["powershell", "-NoProfile", "-Command", command], cwd)


def remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def metrics_summary(path: Path) -> dict[str, Any]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SystemExit(f"metrics file has no rows: {path}")
    nodes = sum(int(row["selected_nodes"]) for row in rows)
    levels = [int(row["selected_levels"]) for row in rows]
    return {
        "rows": len(rows),
        "nodes": nodes,
        "level_sum": sum(levels),
        "max_level": max(levels),
        "fallback": sum(1 for row in rows if row.get("fallback_reason") or str(row.get("status", "")).startswith("fallback")),
        "cec_fail": sum(1 for row in rows if str(row.get("cec_pass", "")).lower() != "true"),
        "bad_entry": sum(1 for row in rows if int(row.get("entry_returncode") or 0) != 0),
        "inner_fallback": sum(int(row.get("inner_fallback_count") or 0) for row in rows),
        "opt_runtime_sum": sum(float(row.get("opt_runtime_sec") or 0.0) for row in rows),
        "cec_runtime_sum": sum(float(row.get("cec_runtime_sec") or 0.0) for row in rows),
        "stats_runtime_sum": sum(float(row.get("stats_runtime_sec") or 0.0) for row in rows),
        "peak_rss_max": max(float(row.get("peak_mem_mb") or 0.0) for row in rows),
    }


def compare_with_v6(r29_metrics: Path, v6_metrics: Path) -> dict[str, Any]:
    with r29_metrics.open(newline="", encoding="utf-8") as handle:
        r29_rows = {row["case"]: row for row in csv.DictReader(handle)}
    with v6_metrics.open(newline="", encoding="utf-8") as handle:
        v6_rows = list(csv.DictReader(handle))
    deltas: list[int] = []
    wins = ties = losses = 0
    for row in v6_rows:
        case = row["case"]
        delta = int(r29_rows[case]["selected_nodes"]) - int(row["selected_nodes"])
        deltas.append(delta)
        if delta < 0:
            wins += 1
        elif delta == 0:
            ties += 1
        else:
            losses += 1
    gains = sorted((-delta for delta in deltas if delta < 0), reverse=True)
    return {
        "gain": -sum(deltas),
        "wins": wins,
        "ties": ties,
        "losses": losses,
        "gain_excluding_best": sum(gains[1:]),
        "gain_excluding_top2": sum(gains[2:]),
    }


def check_evidence(args: argparse.Namespace) -> dict[str, Any]:
    metrics = metrics_summary(args.metrics_source)
    expected_map = {
        "rows": 30,
        "nodes": EXPECTED["nodes"],
        "level_sum": EXPECTED["level_sum"],
        "max_level": EXPECTED["max_level"],
        "fallback": EXPECTED["fallback"],
        "cec_fail": 0,
        "bad_entry": EXPECTED["bad_entry"],
        "inner_fallback": EXPECTED["inner_fallback"],
    }
    for key, expected in expected_map.items():
        if metrics[key] != expected:
            raise SystemExit(f"unexpected metrics {key}: {metrics[key]} != {expected}")

    cec = count_log(args.cec_log_source)
    if cec["equivalent"] != EXPECTED["cec"] or cec["bad"] != 0:
        raise SystemExit(f"unexpected CEC log summary: {cec}")

    delta = compare_with_v6(args.metrics_source, args.v6_metrics_source)
    for key in ["gain", "wins", "ties", "losses", "gain_excluding_best", "gain_excluding_top2"]:
        expected_key = "gain_vs_v6" if key == "gain" else key
        if delta[key] != EXPECTED[expected_key]:
            raise SystemExit(f"unexpected {key}: {delta[key]} != {EXPECTED[expected_key]}")

    abc_sha = sha256(args.abc)
    if abc_sha != EXPECTED["abc_sha256"]:
        raise SystemExit(f"unexpected ABC SHA256: {abc_sha}")
    if args.previous_zip.exists():
        prev_sha = sha256(args.previous_zip)
        if prev_sha != EXPECTED["previous_zip_sha256"]:
            raise SystemExit(f"unexpected previous formal zip SHA256: {prev_sha}")
    else:
        prev_sha = ""

    return {"metrics": metrics, "cec": cec, "delta": delta, "abc_sha256": abc_sha, "previous_zip_sha256": prev_sha}


def build_paths(args: argparse.Namespace) -> dict[str, Path]:
    if args.mode == "formal":
        return {
            "submit": Path("submit"),
            "zip": Path("submit_sharecone.zip"),
            "extract": Path("scratch/r29_formal_zip_extract_check"),
            "root_cec": Path("submit/logs/reproduce_cec.log"),
            "inside_cec": Path("submit/logs/reproduce_cec_inside.log"),
            "zip_root_cec": Path("logs/r29_formal_zip_extract_cec.log"),
            "zip_inside_cec": Path("logs/r29_formal_zip_extract_inside_cec.log"),
            "hidden_dir": Path("logs/r29_formal_zip_hidden_smoke_tc_public_14"),
            "summary": Path("reports/r29_formal_release_summary.json"),
        }
    root = args.work_root
    return {
        "submit": root / "submit",
        "zip": root / "submit_sharecone.zip",
        "extract": root / "zip_extract",
        "root_cec": root / "submit" / "logs" / "reproduce_cec.log",
        "inside_cec": root / "submit" / "logs" / "reproduce_cec_inside.log",
        "zip_root_cec": root / "logs" / "zip_extract_cec.log",
        "zip_inside_cec": root / "logs" / "zip_extract_inside_cec.log",
        "hidden_dir": root / "logs" / "zip_hidden_smoke_tc_public_14",
        "summary": root / "reports" / "r29_release_package_helper_summary.json",
    }


def run_package_and_checks(args: argparse.Namespace, paths: dict[str, Path], cwd: Path, evidence: dict[str, Any]) -> dict[str, Any]:
    abc_source = args.abc
    cached_abc: Path | None = None
    if args.abc.exists():
        try:
            abc_abs = args.abc.resolve()
            submit_abs = (cwd / paths["submit"]).resolve()
            if abc_abs.is_relative_to(submit_abs):
                handle = tempfile.NamedTemporaryFile(delete=False, suffix=".exe")
                handle.close()
                cached_abc = Path(handle.name)
                shutil.copy2(args.abc, cached_abc)
                abc_source = cached_abc
        except AttributeError:
            pass

    for key in ["submit", "extract", "zip"]:
        remove_path(paths[key])
    paths["submit"].parent.mkdir(parents=True, exist_ok=True)

    run(
        [
            sys.executable,
            "tools/package_submit.py",
            "--abc",
            str(abc_source),
            "--config",
            str(args.selector),
            "--pipelines",
            str(args.pipelines),
            "--results",
            str(args.results_source),
            "--metrics",
            str(args.metrics_source),
            "--scoreboard",
            str(args.scoreboard_source),
            "--cec-log",
            str(args.cec_log_source),
            "--failure-cases",
            str(args.failure_cases_source),
            "--out",
            str(paths["submit"]),
        ],
        cwd,
    )
    if cached_abc is not None:
        cached_abc.unlink(missing_ok=True)

    package_abc = paths["submit"] / "bin" / "abc.exe"
    packaged = {
        "abc_sha256": sha256(package_abc),
        "r28_wrapper_present": (paths["submit"] / "tools" / "optimize_one_r28_gated_r27_candidate.py").exists(),
        "r29_wrapper_present": (paths["submit"] / "tools" / "optimize_one_r29_postpass_candidate.py").exists(),
        "r28_pipeline_present": (paths["submit"] / "configs" / "pipelines_r28_gated_r27.yaml").exists(),
        "r29_pipeline_present": (paths["submit"] / "configs" / "pipelines_r29_postpass_candidate.yaml").exists(),
    }
    if packaged["abc_sha256"] != EXPECTED["abc_sha256"]:
        raise SystemExit(f"packaged ABC SHA mismatch: {packaged['abc_sha256']}")
    missing = [key for key, value in packaged.items() if key.endswith("_present") and not value]
    if missing:
        raise SystemExit(f"missing packaged dependencies: {missing}")

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
        [str((paths["extract"] / "bin" / "abc.exe").resolve()), "-c", f"cec {case_input} {hidden_output}"],
        paths["extract"],
        hidden_cec_log,
    )

    summary = {
        "mode": args.mode,
        "evidence": evidence,
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
    parser.add_argument("--abc", type=Path, default=Path("submit/bin/abc.exe"))
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--selector", type=Path, default=Path("configs/final_selector_candidate.yaml"))
    parser.add_argument("--pipelines", type=Path, default=Path("configs/pipelines_candidate.yaml"))
    parser.add_argument("--results-source", type=Path, default=Path("results_candidate/r29_postpass_entry_full_public_candidate_config"))
    parser.add_argument("--metrics-source", type=Path, default=Path("reports/r29_candidate_entry_full_public_candidate_config.csv"))
    parser.add_argument("--v6-metrics-source", type=Path, default=Path("reports/final_metrics.csv"))
    parser.add_argument("--scoreboard-source", type=Path, default=Path("reports/r29_candidate_scoreboard.xlsx"))
    parser.add_argument("--cec-log-source", type=Path, default=Path("logs/r29_candidate_entry_full_public_candidate_config_cec.log"))
    parser.add_argument("--failure-cases-source", type=Path, default=Path("reports/r29_candidate_failure_cases.md"))
    parser.add_argument("--previous-zip", type=Path, default=Path("submit_sharecone.zip"))
    parser.add_argument("--work-root", type=Path, default=Path("scratch/r29_release_package_helper_dryrun"))
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
            raise SystemExit("formal mode requires --confirm-overwrite-submit " + EXPECTED["confirm_token"])
        if not args.allow_dirty and git_status(cwd):
            raise SystemExit("formal mode requires a clean worktree or --allow-dirty")

    if not args.cases.exists():
        raise SystemExit(f"cases directory is missing: {args.cases}")

    run_package_and_checks(args, paths, cwd, evidence)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
