#!/usr/bin/env python3
"""Run one BLIF optimization candidate with ABC, CEC, metrics, and fallback."""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:
    import psutil
except ImportError:  # pragma: no cover - env_check reports this explicitly.
    psutil = None  # type: ignore[assignment]

from parse_abc_stats import parse_ps_output


EQUIV_MARKERS = (
    "Networks are equivalent",
    "Networks are equivalent after",
    "Networks are equivalent up to",
)
NON_EQUIV_MARKERS = (
    "Networks are NOT EQUIVALENT",
    "Networks are not equivalent",
    "not equivalent",
    "NOT EQUIVALENT",
)


@dataclass
class ProcessResult:
    returncode: int
    stdout: str
    stderr: str
    runtime_sec: float
    peak_mem_mb: float
    timed_out: bool = False


@dataclass
class CaseResult:
    case: str
    input_path: str
    requested_pipeline: str
    selected_pipeline: str
    status: str
    fallback_reason: str
    output_path: str
    candidate_path: str
    baseline_path: str
    candidate_nodes: int | None
    candidate_levels: int | None
    baseline_nodes: int | None
    baseline_levels: int | None
    selected_nodes: int | None
    selected_levels: int | None
    original_nodes: int | None
    original_levels: int | None
    opt_returncode: int
    cec_returncode: int
    cec_pass: bool
    opt_runtime_sec: float
    cec_runtime_sec: float
    stats_runtime_sec: float
    peak_mem_mb: float
    log_dir: str


def abc_path(path: Path) -> str:
    return str(path).replace("\\", "/")


def abc_quote(path: Path) -> str:
    return '"' + abc_path(path) + '"'


def normalize_pipeline_steps(steps: str | list[str] | None) -> str:
    if not steps:
        return ""
    if isinstance(steps, list):
        return "; ".join(s.strip().rstrip(";") for s in steps if str(s).strip())
    return str(steps).strip().rstrip(";")


def run_process(args: list[str], timeout: float | None = None, env: dict[str, str] | None = None) -> ProcessResult:
    start = time.perf_counter()
    peak = 0
    proc_env = os.environ.copy()
    if env:
        proc_env.update(env)
    proc = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=proc_env,
    )
    ps_proc = None
    if psutil is not None:
        try:
            ps_proc = psutil.Process(proc.pid)
        except Exception:
            ps_proc = None

    timed_out = False
    stdout = ""
    stderr = ""
    while True:
        if ps_proc is not None:
            try:
                rss = ps_proc.memory_info().rss
                for child in ps_proc.children(recursive=True):
                    try:
                        rss += child.memory_info().rss
                    except Exception:
                        pass
                peak = max(peak, rss)
            except Exception:
                pass
        if proc.poll() is not None:
            stdout, stderr = proc.communicate()
            break
        if timeout is not None and time.perf_counter() - start > timeout:
            timed_out = True
            proc.kill()
            stdout, stderr = proc.communicate()
            break
        time.sleep(0.02)

    runtime = time.perf_counter() - start
    return ProcessResult(
        returncode=proc.returncode if proc.returncode is not None else -1,
        stdout=stdout,
        stderr=stderr,
        runtime_sec=runtime,
        peak_mem_mb=peak / (1024 * 1024) if peak else 0.0,
        timed_out=timed_out,
    )


def write_log(path: Path, result: ProcessResult, command: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", errors="replace") as f:
        f.write(f"$ {command}\n")
        f.write(f"returncode={result.returncode}\n")
        f.write(f"runtime_sec={result.runtime_sec:.6f}\n")
        f.write(f"peak_mem_mb={result.peak_mem_mb:.3f}\n")
        f.write(f"timed_out={result.timed_out}\n\n")
        f.write("STDOUT\n")
        f.write(result.stdout)
        if result.stdout and not result.stdout.endswith("\n"):
            f.write("\n")
        f.write("\nSTDERR\n")
        f.write(result.stderr)
        if result.stderr and not result.stderr.endswith("\n"):
            f.write("\n")


def run_abc_command(
    abc: Path,
    command: str,
    timeout: float | None,
    log_path: Path,
    env: dict[str, str] | None = None,
) -> ProcessResult:
    result = run_process([str(abc), "-c", command], timeout=timeout, env=env)
    write_log(log_path, result, f"{abc} -c {command}")
    return result


def run_optimization(
    abc: Path,
    input_blif: Path,
    output_blif: Path,
    steps: str,
    timeout: float,
    log_path: Path,
    env: dict[str, str] | None = None,
) -> ProcessResult:
    output_blif.parent.mkdir(parents=True, exist_ok=True)
    if not steps:
        shutil.copyfile(input_blif, output_blif)
        result = ProcessResult(0, "identity copy\n", "", 0.0, 0.0, False)
        write_log(log_path, result, f"copy {input_blif} {output_blif}")
        return result
    command = f"read_blif {abc_quote(input_blif)}; {steps}; write_blif {abc_quote(output_blif)}"
    return run_abc_command(abc, command, timeout, log_path, env=env)


def run_cec(
    abc: Path,
    input_blif: Path,
    output_blif: Path,
    timeout: float,
    log_path: Path,
    env: dict[str, str] | None = None,
) -> tuple[bool, ProcessResult]:
    command = f"cec {abc_quote(input_blif)} {abc_quote(output_blif)}"
    result = run_abc_command(abc, command, timeout, log_path, env=env)
    text = result.stdout + "\n" + result.stderr
    failed = any(marker in text for marker in NON_EQUIV_MARKERS)
    passed = result.returncode == 0 and not failed and any(marker in text for marker in EQUIV_MARKERS)
    return passed, result


def collect_stats(
    abc: Path,
    blif: Path,
    timeout: float,
    log_path: Path,
    env: dict[str, str] | None = None,
) -> tuple[dict[str, Any], ProcessResult]:
    command = f"read_blif {abc_quote(blif)}; strash; ps"
    result = run_abc_command(abc, command, timeout, log_path, env=env)
    return parse_ps_output(result.stdout + "\n" + result.stderr), result


def metric_tuple(metrics: dict[str, Any] | None) -> tuple[int | None, int | None]:
    if not metrics:
        return None, None
    nodes = metrics.get("aig_nodes")
    levels = metrics.get("levels")
    return (int(nodes) if nodes is not None else None, int(levels) if levels is not None else None)


def is_obviously_worse(
    candidate_metrics: dict[str, Any],
    baseline_metrics: dict[str, Any],
) -> bool:
    cand_nodes, cand_levels = metric_tuple(candidate_metrics)
    base_nodes, base_levels = metric_tuple(baseline_metrics)
    if cand_nodes is None or base_nodes is None:
        return True
    if cand_nodes > base_nodes:
        return True
    if cand_nodes == base_nodes and cand_levels is not None and base_levels is not None and cand_levels > base_levels:
        return True
    return False


def ensure_verified_baseline(
    abc: Path,
    input_blif: Path,
    baseline_output: Path,
    baseline_steps: str,
    log_dir: Path,
    timeouts: dict[str, float],
    env: dict[str, str] | None = None,
) -> tuple[bool, dict[str, Any], float]:
    if not baseline_output.exists():
        run_optimization(
            abc,
            input_blif,
            baseline_output,
            baseline_steps,
            timeouts["opt"],
            log_dir / "baseline_opt.log",
            env=env,
        )
    cec_pass, _ = run_cec(abc, input_blif, baseline_output, timeouts["cec"], log_dir / "baseline_cec.log", env=env)
    if not cec_pass:
        return False, {}, 0.0
    metrics, stats_result = collect_stats(abc, baseline_output, timeouts["stats"], log_dir / "baseline_stats.log", env=env)
    return bool(metrics), metrics, stats_result.runtime_sec


def run_case(
    abc: Path,
    input_blif: Path,
    output_blif: Path,
    pipeline_name: str,
    pipeline_steps: str,
    baseline_output: Path,
    baseline_steps: str,
    log_dir: Path,
    case_name: str,
    timeouts: dict[str, float] | None = None,
) -> CaseResult:
    timeouts = timeouts or {"opt": 300.0, "cec": 300.0, "stats": 120.0}
    log_dir.mkdir(parents=True, exist_ok=True)
    candidate_path = output_blif.with_name(output_blif.stem + ".candidate.blif")

    abc_env = {"SHARECONE_CASE": case_name}

    original_metrics, _ = collect_stats(abc, input_blif, timeouts["stats"], log_dir / "original_stats.log", env=abc_env)
    orig_nodes, orig_levels = metric_tuple(original_metrics)

    if pipeline_name == "identity":
        baseline_ok = False
        baseline_metrics: dict[str, Any] = {}
    else:
        baseline_ok, baseline_metrics, _ = ensure_verified_baseline(
            abc, input_blif, baseline_output, baseline_steps, log_dir, timeouts, env=abc_env
        )

    opt_result = run_optimization(
        abc,
        input_blif,
        candidate_path,
        pipeline_steps,
        timeouts["opt"],
        log_dir / "candidate_opt.log",
        env=abc_env,
    )
    cec_pass = False
    cec_result = ProcessResult(-1, "", "", 0.0, 0.0, False)
    candidate_metrics: dict[str, Any] = {}
    stats_result = ProcessResult(-1, "", "", 0.0, 0.0, False)
    status = "selected_candidate"
    fallback_reason = ""
    selected_pipeline = pipeline_name
    selected_source = candidate_path

    if opt_result.returncode != 0 or opt_result.timed_out or not candidate_path.exists():
        status = "fallback_baseline" if baseline_ok else "fallback_identity"
        fallback_reason = "candidate_crash_or_timeout"
    else:
        cec_pass, cec_result = run_cec(
            abc, input_blif, candidate_path, timeouts["cec"], log_dir / "candidate_cec.log", env=abc_env
        )
        if not cec_pass:
            status = "fallback_baseline" if baseline_ok else "fallback_identity"
            fallback_reason = "candidate_cec_failed"
        else:
            candidate_metrics, stats_result = collect_stats(
                abc, candidate_path, timeouts["stats"], log_dir / "candidate_stats.log", env=abc_env
            )
            if pipeline_name not in ("baseline", "identity") and baseline_ok and is_obviously_worse(
                candidate_metrics, baseline_metrics
            ):
                status = "fallback_baseline"
                fallback_reason = "candidate_metrics_worse_than_baseline"

    if status == "fallback_baseline" and baseline_ok:
        selected_pipeline = "baseline"
        selected_source = baseline_output
    elif status == "fallback_baseline" and not baseline_ok:
        status = "fallback_identity"
        fallback_reason = (fallback_reason + "; " if fallback_reason else "") + "baseline_unavailable"

    if status == "fallback_identity":
        selected_pipeline = "identity"
        selected_source = input_blif

    output_blif.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(selected_source, output_blif)
    selected_metrics, selected_stats = collect_stats(
        abc, output_blif, timeouts["stats"], log_dir / "selected_stats.log", env=abc_env
    )

    cand_nodes, cand_levels = metric_tuple(candidate_metrics)
    base_nodes, base_levels = metric_tuple(baseline_metrics)
    sel_nodes, sel_levels = metric_tuple(selected_metrics)
    peak_mem = max(opt_result.peak_mem_mb, cec_result.peak_mem_mb, stats_result.peak_mem_mb, selected_stats.peak_mem_mb)

    return CaseResult(
        case=case_name,
        input_path=str(input_blif),
        requested_pipeline=pipeline_name,
        selected_pipeline=selected_pipeline,
        status=status,
        fallback_reason=fallback_reason,
        output_path=str(output_blif),
        candidate_path=str(candidate_path),
        baseline_path=str(baseline_output),
        candidate_nodes=cand_nodes,
        candidate_levels=cand_levels,
        baseline_nodes=base_nodes,
        baseline_levels=base_levels,
        selected_nodes=sel_nodes,
        selected_levels=sel_levels,
        original_nodes=orig_nodes,
        original_levels=orig_levels,
        opt_returncode=opt_result.returncode,
        cec_returncode=cec_result.returncode,
        cec_pass=cec_pass,
        opt_runtime_sec=opt_result.runtime_sec,
        cec_runtime_sec=cec_result.runtime_sec,
        stats_runtime_sec=stats_result.runtime_sec + selected_stats.runtime_sec,
        peak_mem_mb=peak_mem,
        log_dir=str(log_dir),
    )


def write_csv(path: Path, rows: list[CaseResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(asdict(rows[0]).keys()) if rows else list(CaseResult.__dataclass_fields__.keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--abc", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--pipeline-name", required=True)
    parser.add_argument("--pipeline-steps", default="")
    parser.add_argument("--baseline-output", required=True, type=Path)
    parser.add_argument("--baseline-steps", required=True)
    parser.add_argument("--log-dir", required=True, type=Path)
    parser.add_argument("--case", default="case")
    parser.add_argument("--json", type=Path)
    parser.add_argument("--opt-timeout", type=float, default=300.0)
    parser.add_argument("--cec-timeout", type=float, default=300.0)
    parser.add_argument("--stats-timeout", type=float, default=120.0)
    args = parser.parse_args()

    result = run_case(
        args.abc,
        args.input,
        args.output,
        args.pipeline_name,
        normalize_pipeline_steps(args.pipeline_steps),
        args.baseline_output,
        normalize_pipeline_steps(args.baseline_steps),
        args.log_dir,
        args.case,
        {"opt": args.opt_timeout, "cec": args.cec_timeout, "stats": args.stats_timeout},
    )
    payload = asdict(result)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
