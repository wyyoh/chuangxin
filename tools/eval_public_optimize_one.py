#!/usr/bin/env python3
"""Evaluate public cases through the packaged single-case optimize_one entry."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from eval_public import discover_cases, load_case_list


CSV_FIELDS = [
    "case",
    "input_path",
    "requested_pipeline",
    "selected_pipeline",
    "selector_reason",
    "status",
    "fallback_reason",
    "output_path",
    "candidate_path",
    "baseline_path",
    "candidate_nodes",
    "candidate_levels",
    "baseline_nodes",
    "baseline_levels",
    "selected_nodes",
    "selected_levels",
    "original_nodes",
    "original_levels",
    "opt_returncode",
    "cec_returncode",
    "cec_pass",
    "opt_runtime_sec",
    "cec_runtime_sec",
    "stats_runtime_sec",
    "peak_mem_mb",
    "log_dir",
    "chosen_variant",
    "attempted_variants",
    "inner_fallback_count",
    "original_cec_fail_count",
    "entry_returncode",
    "r28_gated_r27_gate",
    "r28_gated_r27_status",
    "r28_postpass",
    "r28_postpass_accepted",
    "r28_postpass_reject_reason",
    "r28_postpass_opt_returncode",
    "r28_postpass_cec_pass",
    "r28_postpass_opt_error",
    "r28_node_delta_vs_v5",
    "r28_level_delta_vs_v5",
    "r29_postpass_gate",
    "r29_postpass_status",
    "r29_postpass",
    "r29_postpass_accepted",
    "r29_postpass_reject_reason",
    "r29_postpass_opt_returncode",
    "r29_postpass_cec_pass",
    "r29_postpass_opt_error",
    "r29_node_delta_vs_v6",
    "r29_level_delta_vs_v6",
    "r30b_postpass_gate",
    "r30b_postpass_status",
    "r30b_postpass",
    "r30b_postpass_accepted",
    "r30b_postpass_reject_reason",
    "r30b_postpass_opt_returncode",
    "r30b_postpass_cec_pass",
    "r30b_postpass_opt_error",
    "r30b_node_delta_vs_v7",
    "r30b_level_delta_vs_v7",
    "r30b_profile_runtime_sec",
    "r30b_profile_status",
    "r30b_profile_skip_reason",
    "r30b_cluster_bucket",
    "r30b_cluster_potential_score",
    "r30b_high_overlap_pairs",
    "r30b_largest_cluster_size",
    "r30b_po_count",
    "r30b_node_count",
]


def make_row(case: str, payload: dict[str, Any], returncode: int) -> dict[str, Any]:
    row = {field: payload.get(field, "") for field in CSV_FIELDS}
    row["case"] = case
    row["entry_returncode"] = returncode
    return row


def failure_row(case: str, input_blif: Path, output_blif: Path, returncode: int) -> dict[str, Any]:
    return {
        "case": case,
        "input_path": str(input_blif),
        "status": "entry_failed",
        "fallback_reason": "optimize_one_returncode",
        "output_path": str(output_blif),
        "cec_pass": False,
        "entry_returncode": returncode,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--abc", required=True, type=Path)
    parser.add_argument("--cases", required=True, type=Path)
    parser.add_argument("--case-list", type=Path)
    parser.add_argument("--selector", required=True, type=Path)
    parser.add_argument("--pipelines", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--seed", default=20260622, type=int)
    parser.add_argument("--variant-index", default=1, type=int)
    parser.add_argument("--modes", default="clean,inputs,outputs,both")
    parser.add_argument("--opt-timeout", type=float, default=300.0)
    parser.add_argument("--cec-timeout", type=float, default=300.0)
    parser.add_argument("--stats-timeout", type=float, default=120.0)
    args = parser.parse_args()

    cases = discover_cases(args.cases)
    if args.case_list:
        requested = set(load_case_list(args.case_list))
        cases = [(case, path) for case, path in cases if case in requested]
    if not cases:
        raise SystemExit(f"no cases found under {args.cases}")

    args.out.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for case, input_blif in cases:
        case_out = args.out / case
        output_blif = case_out / "output.blif"
        metrics_json = case_out / "metrics.json"
        entry_log = case_out / "optimize_one_entry.log"
        cmd = [
            sys.executable,
            "tools/optimize_one.py",
            "--abc",
            str(args.abc),
            "--input",
            str(input_blif),
            "--output",
            str(output_blif),
            "--selector",
            str(args.selector),
            "--pipelines",
            str(args.pipelines),
            "--work-dir",
            str(case_out / "work"),
            "--metrics-json",
            str(metrics_json),
            "--seed",
            str(args.seed),
            "--variant-index",
            str(args.variant_index),
            "--modes",
            args.modes,
            "--case-label",
            "input",
            "--opt-timeout",
            str(args.opt_timeout),
            "--cec-timeout",
            str(args.cec_timeout),
            "--stats-timeout",
            str(args.stats_timeout),
        ]
        case_out.mkdir(parents=True, exist_ok=True)
        print(f"[{case}] running optimize_one entry")
        completed = subprocess.run(cmd, capture_output=True, text=True)
        entry_log.write_text(
            "COMMAND:\n"
            + " ".join(cmd)
            + "\n\nSTDOUT:\n"
            + completed.stdout
            + "\n\nSTDERR:\n"
            + completed.stderr,
            encoding="utf-8",
        )
        if completed.returncode != 0 or not metrics_json.exists():
            rows.append(failure_row(case, input_blif, output_blif, completed.returncode))
            print(f"[{case}] entry failed returncode={completed.returncode}")
            continue
        payload = json.loads(metrics_json.read_text(encoding="utf-8"))
        rows.append(make_row(case, payload, completed.returncode))
        print(
            f"[{case}] chosen={payload.get('chosen_variant')} "
            f"nodes={payload.get('selected_nodes')} levels={payload.get('selected_levels')} "
            f"cec={payload.get('cec_pass')}"
        )

    args.csv.parent.mkdir(parents=True, exist_ok=True)
    with args.csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    total = sum(int(row.get("selected_nodes") or 0) for row in rows)
    max_level = max((int(row.get("selected_levels") or 0) for row in rows), default=0)
    cec_pass = sum(1 for row in rows if str(row.get("cec_pass")).lower() == "true")
    fallback = sum(
        1
        for row in rows
        if row.get("status") != "selected_candidate" or row.get("fallback_reason")
    )
    inner_fallback = sum(int(row.get("inner_fallback_count") or 0) for row in rows)
    bad_entry = sum(1 for row in rows if int(row.get("entry_returncode") or 0) != 0)
    r28_accepted = sum(1 for row in rows if row.get("r28_postpass_accepted"))
    r28_delta = sum(int(row.get("r28_node_delta_vs_v5") or 0) for row in rows)
    r29_accepted = sum(1 for row in rows if row.get("r29_postpass_accepted"))
    r29_delta = sum(int(row.get("r29_node_delta_vs_v6") or 0) for row in rows)
    r30b_accepted = sum(1 for row in rows if row.get("r30b_postpass_accepted"))
    r30b_delta = sum(int(row.get("r30b_node_delta_vs_v7") or 0) for row in rows)
    print(
        f"wrote {args.csv}; nodes={total}; max_level={max_level}; "
        f"cec={cec_pass}/{len(rows)}; fallback={fallback}; "
        f"inner_fallback={inner_fallback}; bad_entry={bad_entry}; "
        f"r28_accepted={r28_accepted}; r28_gain_vs_v5={-r28_delta}; "
        f"r29_accepted={r29_accepted}; r29_gain_vs_v6={-r29_delta}; "
        f"r30b_accepted={r30b_accepted}; r30b_gain_vs_v7={-r30b_delta}"
    )
    return 0 if cec_pass == len(rows) and fallback == 0 and bad_entry == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
