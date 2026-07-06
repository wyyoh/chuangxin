#!/usr/bin/env python3
"""Candidate-only R8 single-case port-order choose-best optimizer.

This script is intentionally separate from the formal `optimize_one.py`. It
generates deterministic PI/PO declaration-order variants for one BLIF, runs the
same selector-selected pipeline on each variant, checks each output against the
original input, and keeps only a node-improving, level-safe winner.
"""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from eval_public import load_pipeline_steps, load_yaml_like
from extract_blif_features import extract_one
from extract_r7b_features import run_profile
from r25_route_d_divisor_profile import analyze_case
from r7b_port_order_stress import rewrite_blif
from run_abc_case import collect_stats, run_case, run_cec
from select_pipeline import choose, validate_selector


def safe_int(value: int | None) -> int:
    return int(value) if value is not None else 10**12


def build_features(
    abc: Path,
    input_blif: Path,
    work_dir: Path,
    profile_timeout: float,
    case_label: str,
) -> dict[str, str]:
    features = {key: str(value) for key, value in extract_one(input_blif, case_label).items()}
    profile_args = SimpleNamespace(abc=abc, work_dir=work_dir / "feature_profile", timeout=profile_timeout)
    features.update(run_profile(case_label, input_blif, profile_args))
    route_d_row, _ = analyze_case(case_label, input_blif, {}, features)
    features.update({key: str(value) for key, value in route_d_row.items()})
    return features


def normalize_modes(raw_modes: str) -> list[str]:
    modes = [mode.strip() for mode in raw_modes.split(",") if mode.strip()]
    if "clean" not in modes:
        modes.insert(0, "clean")
    allowed = {"clean", "inputs", "outputs", "both"}
    unknown = [mode for mode in modes if mode not in allowed]
    if unknown:
        raise ValueError(f"unknown R8 variant mode(s): {', '.join(unknown)}")
    return modes


def optimize_one(args: argparse.Namespace) -> dict[str, Any]:
    selector_config = load_yaml_like(args.selector)
    validate_selector(selector_config)
    pipeline_config = load_yaml_like(args.pipelines)
    features = build_features(args.abc, args.input, args.work_dir, args.stats_timeout, args.case_label)
    pipeline_name, selector_reason = choose(features, selector_config)
    pipeline_steps = load_pipeline_steps(pipeline_config, pipeline_name)
    baseline_steps = load_pipeline_steps(pipeline_config, "baseline")
    modes = normalize_modes(args.modes)
    timeouts = {"opt": args.opt_timeout, "cec": args.cec_timeout, "stats": args.stats_timeout}

    args.work_dir.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    attempts: list[dict[str, Any]] = []
    clean_levels: int | None = None
    for mode in modes:
        if mode == "clean":
            variant_input = args.input
        else:
            variant_input = args.work_dir / "variant_inputs" / mode / "input.blif"
            rewrite_blif(args.input, variant_input, args.case_label, args.variant_index, args.seed, mode)

        variant_dir = args.work_dir / "variants" / mode
        result = run_case(
            args.abc,
            variant_input,
            variant_dir / "output.blif",
            pipeline_name,
            pipeline_steps,
            variant_dir / "baseline.blif",
            baseline_steps,
            variant_dir / "logs",
            args.case_label,
            timeouts,
        )
        selected_output = Path(result.output_path)
        if mode == "clean":
            original_cec_pass = bool(result.cec_pass)
            original_cec_runtime = 0.0
            if result.selected_levels is not None:
                clean_levels = int(result.selected_levels)
        else:
            original_cec_pass, original_cec = run_cec(
                args.abc,
                args.input,
                selected_output,
                args.cec_timeout,
                variant_dir / "logs" / "original_input_cec.log",
            )
            original_cec_runtime = original_cec.runtime_sec
        attempts.append(
            {
                "mode": mode,
                "result": result,
                "original_cec_pass": bool(original_cec_pass),
                "original_cec_runtime": float(original_cec_runtime),
            }
        )

    if not attempts:
        raise RuntimeError("no R8 attempts were run")
    if clean_levels is None:
        clean_levels = safe_int(attempts[0]["result"].selected_levels)

    best = attempts[0]
    for attempt in attempts[1:]:
        result = attempt["result"]
        if not attempt["original_cec_pass"]:
            continue
        if result.selected_nodes is None or result.selected_levels is None:
            continue
        if int(result.selected_levels) > int(clean_levels):
            continue
        best_result = best["result"]
        if safe_int(result.selected_nodes) < safe_int(best_result.selected_nodes):
            best = attempt

    shutil.copyfile(best["result"].output_path, args.output)
    final_cec_pass, final_cec = run_cec(
        args.abc,
        args.input,
        args.output,
        args.cec_timeout,
        args.work_dir / "logs" / "final_original_cec.log",
    )
    fallback_reason = ""
    if not final_cec_pass:
        shutil.copyfile(args.input, args.output)
        fallback_reason = "final_original_cec_failed"

    final_metrics, final_stats = collect_stats(
        args.abc,
        args.output,
        args.stats_timeout,
        args.work_dir / "logs" / "final_stats.log",
    )
    chosen = best["result"]
    opt_runtime = sum(float(attempt["result"].opt_runtime_sec) for attempt in attempts)
    cec_runtime = (
        sum(float(attempt["result"].cec_runtime_sec) for attempt in attempts)
        + sum(float(attempt["original_cec_runtime"]) for attempt in attempts)
        + final_cec.runtime_sec
    )
    stats_runtime = sum(float(attempt["result"].stats_runtime_sec) for attempt in attempts) + final_stats.runtime_sec
    peak_mem = max(float(attempt["result"].peak_mem_mb) for attempt in attempts)
    fallback_count = sum(1 for attempt in attempts if str(attempt["result"].status).startswith("fallback"))
    original_cec_fail_count = sum(1 for attempt in attempts if not attempt["original_cec_pass"])

    payload: dict[str, Any] = {
        "case": args.case_label,
        "input_path": str(args.input),
        "requested_pipeline": pipeline_name,
        "selected_pipeline": f"{chosen.selected_pipeline}@{best['mode']}",
        "selector_reason": selector_reason,
        "status": "selected_candidate" if final_cec_pass else "fallback_identity",
        "fallback_reason": fallback_reason,
        "output_path": str(args.output),
        "candidate_path": str(chosen.candidate_path),
        "baseline_path": str(chosen.baseline_path),
        "candidate_nodes": chosen.candidate_nodes,
        "candidate_levels": chosen.candidate_levels,
        "baseline_nodes": chosen.baseline_nodes,
        "baseline_levels": chosen.baseline_levels,
        "selected_nodes": int(final_metrics.get("aig_nodes", 0) or 0),
        "selected_levels": int(final_metrics.get("levels", 0) or 0),
        "original_nodes": attempts[0]["result"].original_nodes,
        "original_levels": attempts[0]["result"].original_levels,
        "opt_returncode": 0,
        "cec_returncode": final_cec.returncode,
        "cec_pass": bool(final_cec_pass),
        "opt_runtime_sec": float(f"{opt_runtime:.6f}"),
        "cec_runtime_sec": float(f"{cec_runtime:.6f}"),
        "stats_runtime_sec": float(f"{stats_runtime:.6f}"),
        "peak_mem_mb": float(f"{peak_mem:.3f}"),
        "log_dir": str(args.work_dir / "logs"),
        "chosen_variant": best["mode"],
        "attempted_variants": ",".join(modes),
        "inner_fallback_count": fallback_count,
        "original_cec_fail_count": original_cec_fail_count,
        "features": features,
        "attempts": [
            {
                "mode": attempt["mode"],
                "selected_nodes": attempt["result"].selected_nodes,
                "selected_levels": attempt["result"].selected_levels,
                "status": attempt["result"].status,
                "cec_pass": attempt["result"].cec_pass,
                "original_cec_pass": attempt["original_cec_pass"],
            }
            for attempt in attempts
        ],
    }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--abc", required=True, type=Path)
    parser.add_argument("--input", default=Path("input.blif"), type=Path)
    parser.add_argument("--output", default=Path("output.blif"), type=Path)
    parser.add_argument("--selector", default=Path("configs/final_selector_r7b_candidate.yaml"), type=Path)
    parser.add_argument("--pipelines", default=Path("configs/pipelines_r7b_pure_candidate.yaml"), type=Path)
    parser.add_argument("--work-dir", default=Path("work/r8_order_choosebest"), type=Path)
    parser.add_argument("--metrics-json", type=Path)
    parser.add_argument("--seed", default=20260622, type=int)
    parser.add_argument("--variant-index", default=1, type=int)
    parser.add_argument("--modes", default="clean,inputs,outputs,both")
    parser.add_argument("--case-label", default="input")
    parser.add_argument("--opt-timeout", type=float, default=300.0)
    parser.add_argument("--cec-timeout", type=float, default=300.0)
    parser.add_argument("--stats-timeout", type=float, default=120.0)
    args = parser.parse_args()

    payload = optimize_one(args)
    if args.metrics_json:
        args.metrics_json.parent.mkdir(parents=True, exist_ok=True)
        args.metrics_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if payload.get("cec_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
