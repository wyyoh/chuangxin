#!/usr/bin/env python3
"""R29 guarded post-pass candidate optimizer.

The candidate first runs the formal v6 optimizer. It then attempts a lightweight
post-pass only for coarse buckets that R29 research showed were candidate-ready.
The post-pass is accepted only when it passes CEC against the original input,
reduces AIG nodes, and does not increase AIG level.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from eval_public import load_yaml_like
from optimize_one_r28_gated_r27_candidate import optimize_one as optimize_v6
from run_abc_case import collect_stats, run_cec, run_optimization


DEFAULT_R29_POSTPASS = "r29_mfs_strash_dc2_rwz_bal"


def int_metric(value: Any) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return 0


def abc_reported_error(*texts: str) -> bool:
    combined = "\n".join(texts)
    return "Error:" in combined or "usage:" in combined or "Cannot find" in combined


def gate_matches(v6_payload: dict[str, Any]) -> tuple[bool, str]:
    reason = str(v6_payload.get("selector_reason") or "")
    allowed = {
        "r7b_high_overlap_guarded_fraig",
        "medium_runtime_fraig_cleanup",
        "large_smallpo_fraig_cleanup",
        "r11_deepsyn_medium_tiny_po",
    }
    if reason in allowed:
        return True, reason
    return False, "gate_not_matched"


def load_postpass_steps(config_path: Path, postpass_name: str) -> str:
    config = load_yaml_like(config_path)
    entry = (config.get("pipelines", {}) or {}).get(postpass_name)
    if not entry:
        raise KeyError(f"R29 post-pass not found: {postpass_name}")
    return str((entry or {}).get("steps", "")).strip()


def run_postpass(
    *,
    abc: Path,
    original_input: Path,
    v6_output: Path,
    postpass_name: str,
    postpass_steps: str,
    baseline_nodes: int,
    baseline_levels: int,
    work_dir: Path,
    timeouts: dict[str, float],
    gate_reason: str,
) -> dict[str, Any]:
    cand_dir = work_dir / "r29_postpass" / postpass_name
    cand_dir.mkdir(parents=True, exist_ok=True)
    output = cand_dir / "output.blif"
    if output.exists():
        output.unlink()

    opt = run_optimization(
        abc,
        v6_output,
        output,
        postpass_steps,
        timeouts["opt"],
        cand_dir / "opt.log",
        env={"R29_GATE": gate_reason, "R29_POSTPASS": postpass_name},
    )
    opt_error = abc_reported_error(opt.stdout, opt.stderr)
    opt_ok = opt.returncode == 0 and not opt.timed_out and not opt_error and output.exists()

    cec_pass = False
    cec = None
    stats_result = None
    stats: dict[str, Any] = {}
    nodes = 0
    levels = 0
    reject_reason = ""
    if opt_ok:
        cec_pass, cec = run_cec(abc, original_input, output, timeouts["cec"], cand_dir / "cec.log")
        stats, stats_result = collect_stats(abc, output, timeouts["stats"], cand_dir / "stats.log")
        nodes = int_metric(stats.get("aig_nodes"))
        levels = int_metric(stats.get("levels"))
    else:
        (cand_dir / "cec.log").write_text("cec skipped because optimization failed\n", encoding="utf-8")
        (cand_dir / "stats.log").write_text("stats skipped because optimization failed\n", encoding="utf-8")

    if opt.timed_out or (cec and cec.timed_out) or (stats_result and stats_result.timed_out):
        reject_reason = "timeout"
    elif not opt_ok:
        reject_reason = "opt_failed"
    elif not cec_pass:
        reject_reason = "cec_failed"
    elif nodes <= 0:
        reject_reason = "stats_missing"
    elif nodes >= baseline_nodes:
        reject_reason = "no_node_gain"
    elif levels > baseline_levels:
        reject_reason = "level_regression"

    accepted = reject_reason == ""
    peak = max(
        opt.peak_mem_mb,
        cec.peak_mem_mb if cec else 0.0,
        stats_result.peak_mem_mb if stats_result else 0.0,
    )
    return {
        "candidate": postpass_name,
        "steps": postpass_steps,
        "accepted": accepted,
        "reject_reason": reject_reason,
        "output_path": str(output),
        "nodes": nodes,
        "levels": levels,
        "node_delta_vs_v6": nodes - baseline_nodes if nodes else "",
        "level_delta_vs_v6": levels - baseline_levels if levels else "",
        "opt_returncode": opt.returncode,
        "opt_error": opt_error,
        "cec_returncode": cec.returncode if cec else "",
        "cec_pass": cec_pass,
        "opt_runtime_sec": float(f"{opt.runtime_sec:.6f}"),
        "cec_runtime_sec": float(f"{cec.runtime_sec:.6f}") if cec else 0.0,
        "stats_runtime_sec": float(f"{stats_result.runtime_sec:.6f}") if stats_result else 0.0,
        "peak_mem_mb": float(f"{peak:.3f}"),
    }


def optimize_one(args: argparse.Namespace) -> dict[str, Any]:
    v6_output = args.work_dir / "v6" / "output.blif"
    v6_args = argparse.Namespace(**vars(args))
    v6_args.output = v6_output
    v6_args.work_dir = args.work_dir / "v6" / "work"
    v6_args.metrics_json = args.work_dir / "v6" / "metrics.json"
    v6_payload = optimize_v6(v6_args)
    v6_args.metrics_json.parent.mkdir(parents=True, exist_ok=True)
    v6_args.metrics_json.write_text(json.dumps(v6_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    if not v6_payload.get("cec_pass"):
        shutil.copyfile(v6_output if v6_output.exists() else args.input, args.output)
        return {
            **v6_payload,
            "output_path": str(args.output),
            "r29_postpass_gate": "v6_cec_failed",
            "r29_postpass_status": "v6_cec_failed",
            "r29_postpass": args.r29_postpass,
            "r29_postpass_accepted": "",
            "r29_postpass_reject_reason": "v6_cec_failed",
            "r29_node_delta_vs_v6": 0,
            "r29_level_delta_vs_v6": 0,
        }

    matched, gate_reason = gate_matches(v6_payload)
    baseline_nodes = int_metric(v6_payload.get("selected_nodes"))
    baseline_levels = int_metric(v6_payload.get("selected_levels"))
    if not matched:
        shutil.copyfile(v6_output, args.output)
        return {
            **v6_payload,
            "output_path": str(args.output),
            "r29_postpass_gate": gate_reason,
            "r29_postpass_status": "skipped",
            "r29_postpass": args.r29_postpass,
            "r29_postpass_accepted": "",
            "r29_postpass_reject_reason": "gate_not_matched",
            "r29_postpass_opt_returncode": "",
            "r29_postpass_cec_pass": "",
            "r29_postpass_opt_error": "",
            "r29_node_delta_vs_v6": 0,
            "r29_level_delta_vs_v6": 0,
        }

    postpass_steps = load_postpass_steps(args.r29_pipelines, args.r29_postpass)
    attempt = run_postpass(
        abc=args.abc,
        original_input=args.input,
        v6_output=v6_output,
        postpass_name=args.r29_postpass,
        postpass_steps=postpass_steps,
        baseline_nodes=baseline_nodes,
        baseline_levels=baseline_levels,
        work_dir=args.work_dir,
        timeouts={"opt": args.post_opt_timeout, "cec": args.cec_timeout, "stats": args.stats_timeout},
        gate_reason=gate_reason,
    )

    selected_source = Path(attempt["output_path"]) if attempt["accepted"] else v6_output
    shutil.copyfile(selected_source, args.output)
    final_cec_pass, final_cec = run_cec(
        args.abc,
        args.input,
        args.output,
        args.cec_timeout,
        args.work_dir / "logs" / "r29_final_cec.log",
    )
    if not final_cec_pass:
        shutil.copyfile(v6_output, args.output)
    final_stats, final_stats_result = collect_stats(
        args.abc,
        args.output,
        args.stats_timeout,
        args.work_dir / "logs" / "r29_final_stats.log",
    )
    selected_nodes = int_metric(final_stats.get("aig_nodes"))
    selected_levels = int_metric(final_stats.get("levels"))

    post_opt_runtime = float(attempt.get("opt_runtime_sec") or 0.0)
    post_cec_runtime = float(attempt.get("cec_runtime_sec") or 0.0) + final_cec.runtime_sec
    post_stats_runtime = float(attempt.get("stats_runtime_sec") or 0.0) + final_stats_result.runtime_sec
    post_peak = max(float(attempt.get("peak_mem_mb") or 0.0), final_cec.peak_mem_mb, final_stats_result.peak_mem_mb)
    v6_peak = float(v6_payload.get("peak_mem_mb") or 0.0)

    payload = dict(v6_payload)
    payload.update(
        {
            "output_path": str(args.output),
            "selected_nodes": selected_nodes,
            "selected_levels": selected_levels,
            "cec_pass": bool(final_cec_pass),
            "cec_returncode": final_cec.returncode,
            "status": "selected_candidate" if final_cec_pass else "fallback_baseline",
            "fallback_reason": "" if final_cec_pass else "r29_final_cec_failed",
            "selected_pipeline": (
                f"{v6_payload.get('selected_pipeline')}+{args.r29_postpass}"
                if attempt["accepted"]
                else str(v6_payload.get("selected_pipeline"))
            ),
            "opt_runtime_sec": float(f"{float(v6_payload.get('opt_runtime_sec') or 0.0) + post_opt_runtime:.6f}"),
            "cec_runtime_sec": float(f"{float(v6_payload.get('cec_runtime_sec') or 0.0) + post_cec_runtime:.6f}"),
            "stats_runtime_sec": float(f"{float(v6_payload.get('stats_runtime_sec') or 0.0) + post_stats_runtime:.6f}"),
            "peak_mem_mb": float(f"{max(v6_peak, post_peak):.3f}"),
            "log_dir": str(args.work_dir / "logs"),
            "r29_postpass_gate": gate_reason,
            "r29_postpass_status": "accepted" if attempt["accepted"] else "rejected",
            "r29_postpass": args.r29_postpass,
            "r29_postpass_accepted": args.r29_postpass if attempt["accepted"] else "",
            "r29_postpass_reject_reason": attempt["reject_reason"],
            "r29_postpass_opt_returncode": attempt["opt_returncode"],
            "r29_postpass_cec_pass": attempt["cec_pass"],
            "r29_postpass_opt_error": attempt["opt_error"],
            "r29_node_delta_vs_v6": selected_nodes - baseline_nodes,
            "r29_level_delta_vs_v6": selected_levels - baseline_levels,
            "r29_attempt": attempt,
        }
    )
    return payload
