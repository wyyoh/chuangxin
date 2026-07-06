#!/usr/bin/env python3
"""Offline ABC pipeline portfolio runner.

This is intentionally for tuning only. Final submission must use a fixed
pipeline or a lightweight selector choosing a small number of configured
pipelines.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
from pathlib import Path
from typing import Any

from eval_public import discover_cases, load_pipeline_steps, load_yaml_like
from run_abc_case import CaseResult, run_case, write_csv


def pipeline_names(config: dict[str, Any], requested: list[str] | None) -> list[str]:
    names = list((config.get("pipelines") or {}).keys())
    names = [name for name in names if name != "identity"]
    if requested:
        missing = [name for name in requested if name not in names]
        if missing:
            raise KeyError(f"pipelines not found: {', '.join(missing)}")
        return requested
    return names


def write_summary(path: Path, rows: list[CaseResult]) -> None:
    grouped: dict[str, list[CaseResult]] = {}
    for row in rows:
        grouped.setdefault(row.requested_pipeline, []).append(row)

    lines = [
        "# Portfolio Summary",
        "",
        "This report is generated from real `tools/run_portfolio.py` runs. Portfolio search is offline tuning only; final submission must not run all pipelines per case.",
        "",
        "| pipeline | cases | selected_nodes_sum | max_level | fallbacks | cec_failures | runtime_sec_sum | peak_mem_mb_max |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name in sorted(grouped):
        items = grouped[name]
        node_sum = sum(int(r.selected_nodes or 0) for r in items)
        max_level = max((int(r.selected_levels or 0) for r in items), default=0)
        fallbacks = sum(1 for r in items if r.status.startswith("fallback"))
        cec_failures = sum(1 for r in items if not r.cec_pass and not r.status.startswith("fallback"))
        runtime = sum(float(r.opt_runtime_sec + r.cec_runtime_sec) for r in items)
        peak_mem = max((float(r.peak_mem_mb) for r in items), default=0.0)
        lines.append(
            f"| {name} | {len(items)} | {node_sum} | {max_level} | {fallbacks} | "
            f"{cec_failures} | {runtime:.3f} | {peak_mem:.1f} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--abc", required=True, type=Path)
    parser.add_argument("--cases", required=True, type=Path)
    parser.add_argument("--pipelines", required=True, type=Path)
    parser.add_argument("--pipeline", action="append", dest="only")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--summary", type=Path, default=Path("reports/portfolio_summary.md"))
    parser.add_argument("--baseline-dir", type=Path, default=Path("results/baseline"))
    parser.add_argument("--opt-timeout", type=float, default=300.0)
    parser.add_argument("--cec-timeout", type=float, default=300.0)
    parser.add_argument("--stats-timeout", type=float, default=120.0)
    args = parser.parse_args()

    config = load_yaml_like(args.pipelines)
    names = pipeline_names(config, args.only)
    baseline_steps = load_pipeline_steps(config, "baseline")
    cases = discover_cases(args.cases)
    rows: list[CaseResult] = []

    for name in names:
        steps = load_pipeline_steps(config, name)
        for case_name, input_blif in cases:
            case_out_dir = args.out / name / case_name
            print(f"[{name}][{case_name}]")
            result = run_case(
                args.abc,
                input_blif,
                case_out_dir / "output.blif",
                name,
                steps,
                args.baseline_dir / case_name / "output.blif",
                baseline_steps,
                case_out_dir / "logs",
                case_name,
                {"opt": args.opt_timeout, "cec": args.cec_timeout, "stats": args.stats_timeout},
            )
            rows.append(result)
            print(
                f"[{name}][{case_name}] status={result.status} selected={result.selected_pipeline} "
                f"nodes={result.selected_nodes} levels={result.selected_levels}"
            )

    write_csv(args.csv, rows)
    write_summary(args.summary, rows)
    print(f"wrote {args.csv}")
    print(f"wrote {args.summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
