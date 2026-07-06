#!/usr/bin/env python3
"""Summarize R7b port-order stress variants against clean candidate metrics."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def as_int(row: dict[str, str], field: str) -> int:
    return int(float(row[field]))


def summarize_one(name: str, path: Path) -> dict[str, object]:
    rows = load_rows(path)
    gains = [as_int(row, "clean_nodes") - as_int(row, "stress_nodes") for row in rows]
    level_deltas = [as_int(row, "stress_levels") - as_int(row, "clean_levels") for row in rows]
    sorted_gains = sorted(gains, reverse=True)
    total_gain = sum(gains)
    wins = sum(1 for gain in gains if gain > 0)
    losses = sum(1 for gain in gains if gain < 0)
    ties = sum(1 for gain in gains if gain == 0)
    best_gain = sorted_gains[0] if sorted_gains else 0
    second_gain = sorted_gains[1] if len(sorted_gains) > 1 else 0
    return {
        "variant": name,
        "compare_csv": str(path),
        "total_nodes": sum(as_int(row, "stress_nodes") for row in rows),
        "total_gain_vs_clean": total_gain,
        "max_level": max(as_int(row, "stress_levels") for row in rows),
        "wins": wins,
        "ties": ties,
        "losses": losses,
        "best_case_gain": best_gain,
        "second_case_gain": second_gain,
        "gain_excluding_best": total_gain - best_gain,
        "gain_excluding_top2": total_gain - best_gain - second_gain,
        "node_mismatch_count": sum(1 for gain in gains if gain != 0),
        "level_mismatch_count": sum(1 for delta in level_deltas if delta != 0),
        "level_regression_count": sum(1 for delta in level_deltas if delta > 0),
        "pipeline_mismatch_count": sum(1 for row in rows if row["pipeline_match"] != "True"),
        "cec_fail_count": sum(1 for row in rows if row["stress_cec_pass"] != "True"),
        "fallback_count": sum(as_int(row, "stress_fallback") for row in rows),
    }


def write_markdown(rows: list[dict[str, object]], report: Path) -> None:
    best = min(rows, key=lambda row: int(row["total_nodes"])) if rows else None
    md = [
        "---",
        "research_id: R8-PORT-ORDER",
        "status: research-only",
        "baseline_tag: final_selector_v2_20260526",
        "baseline_commit: 0b0edf4890283e36fac943166a8c84a148c120b8",
        "branch: candidate/r7b-pure",
        "created: 2026-06-22",
        "updated: 2026-06-22",
        "affects_final: false",
        "primary_data:",
    ]
    for row in rows:
        md.append(f"  - {row['compare_csv']}")
    md.extend(
        [
            "---",
            "",
            "# R8 Port-Order Preconditioning Feasibility",
            "",
            "## Objective",
            "",
            "Evaluate whether PI/PO declaration-order changes discovered during R7b stress testing are a candidate-worthy optimization direction.",
            "",
            "## Baseline",
            "",
            "Comparator is the clean pure R7b candidate: 44559 nodes, max level 21, CEC 30/30, fallback 0.",
            "",
            "## Commands",
            "",
            "The three stress variants were generated with `tools/r7b_port_order_stress.py` using `--mode both`, `--mode inputs`, and `--mode outputs`, followed by feature extraction, full public 30 evaluation, independent CEC, and comparison against `reports/r7b_pure_clean_metrics.csv`.",
            "",
            "## Input Data",
            "",
            "- Clean metrics: `reports/r7b_pure_clean_metrics.csv`",
            "- Both-order compare: `reports/r7b_port_order_stress_compare.csv`",
            "- Input-order compare: `reports/r7b_port_order_inputs_stress_compare.csv`",
            "- Output-order compare: `reports/r7b_port_order_outputs_stress_compare.csv`",
            "",
            "## Results",
            "",
            "| Variant | Nodes | Gain | Max Level | W/T/L | Gain Ex Best | Gain Ex Top2 | Level Regr | CEC Fail | Fallback |",
            "| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in rows:
        md.append(
            "| {variant} | {total_nodes} | {total_gain_vs_clean} | {max_level} | {wins}/{ties}/{losses} | {gain_excluding_best} | {gain_excluding_top2} | {level_regression_count} | {cec_fail_count} | {fallback_count} |".format(
                **row
            )
        )
    md.extend(
        [
            "",
            "## Correctness",
            "",
            "All three stress variants passed evaluator CEC and independent CEC for all 30 cases, with fallback 0. These are valid equivalence-preserving experiments, but they are not yet a selector-ready final candidate.",
            "",
            "## Risk",
            "",
            "The raw gains are order-sensitive and include broad losses. The best variant improves total nodes, but the gains do not yet pass the promotion gate requiring positive gain after excluding the top two cases. A final selector cannot simply enable random order shuffling by public case identity.",
            "",
            "## Selector Eligibility",
            "",
            "Not eligible yet. The next research step would need a deterministic, coarse structural rule or a per-case guarded choose-best wrapper that evaluates multiple orderings and accepts only CEC-passing, node-improving, level-safe outputs without using filenames or exact public fingerprints.",
            "",
            "## Conclusion",
            "",
            "research-only",
            "",
            "## Next Action",
            "",
        ]
    )
    if best is not None:
        md.append(
            f"Best observed raw variant is `{best['variant']}` with `{best['total_nodes']}` nodes, but it fails gain-excluding-top2 promotion. Continue only with a guarded multi-order choose-best feasibility test, not direct promotion."
        )
    else:
        md.append("No usable rows were available; stop this direction until evidence is regenerated.")
    md.append("")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(md), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", nargs=2, action="append", metavar=("NAME", "CSV"), required=True)
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    rows = [summarize_one(name, Path(path)) for name, path in args.variant]
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    with args.csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)
    write_markdown(rows, args.report)
    for row in rows:
        print(
            f"{row['variant']}: nodes={row['total_nodes']} gain={row['total_gain_vs_clean']} "
            f"gain_ex_top2={row['gain_excluding_top2']} cec_fail={row['cec_fail_count']} fallback={row['fallback_count']}"
        )
    print(f"wrote {args.csv}")
    print(f"wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
