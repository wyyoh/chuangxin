#!/usr/bin/env python3
"""Evaluate public cases through the R8 single-case choose-best interface."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from eval_public import discover_cases, load_case_list
from optimize_one_r8_order_choosebest import optimize_one


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
]


def public_row(case: str, payload: dict[str, Any]) -> dict[str, Any]:
    row = {field: payload.get(field, "") for field in CSV_FIELDS}
    row["case"] = case
    return row


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
        requested = load_case_list(args.case_list)
        cases = [(case, path) for case, path in cases if case in requested]
    if not cases:
        raise SystemExit(f"no cases found under {args.cases}")

    args.out.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for case, input_blif in cases:
        case_out = args.out / case
        case_args = SimpleNamespace(
            abc=args.abc,
            input=input_blif,
            output=case_out / "output.blif",
            selector=args.selector,
            pipelines=args.pipelines,
            work_dir=case_out / "work",
            metrics_json=case_out / "metrics.json",
            seed=args.seed,
            variant_index=args.variant_index,
            modes=args.modes,
            case_label="input",
            opt_timeout=args.opt_timeout,
            cec_timeout=args.cec_timeout,
            stats_timeout=args.stats_timeout,
        )
        print(f"[{case}] running R8 single-case choose-best")
        payload = optimize_one(case_args)
        case_args.metrics_json.parent.mkdir(parents=True, exist_ok=True)
        case_args.metrics_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        rows.append(public_row(case, payload))
        print(
            f"[{case}] chosen={payload['chosen_variant']} "
            f"nodes={payload['selected_nodes']} levels={payload['selected_levels']} "
            f"cec={payload['cec_pass']}"
        )

    args.csv.parent.mkdir(parents=True, exist_ok=True)
    with args.csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    total = sum(int(row["selected_nodes"]) for row in rows)
    max_level = max(int(row["selected_levels"]) for row in rows)
    cec_pass = sum(1 for row in rows if str(row["cec_pass"]).lower() == "true")
    fallback = sum(1 for row in rows if row["status"] != "selected_candidate" or row["fallback_reason"])
    inner_fallback = sum(int(row["inner_fallback_count"]) for row in rows)
    print(
        f"wrote {args.csv}; nodes={total}; max_level={max_level}; "
        f"cec={cec_pass}/{len(rows)}; fallback={fallback}; inner_fallback={inner_fallback}"
    )
    return 0 if cec_pass == len(rows) and fallback == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
