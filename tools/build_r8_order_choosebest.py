#!/usr/bin/env python3
"""Build a research-only R8 choose-best output set from order stress variants."""

from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path


def load_metrics(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return {row["case"]: row for row in csv.DictReader(f)}


def as_int(row: dict[str, str], field: str) -> int:
    return int(float(row[field]))


def as_bool(row: dict[str, str], field: str) -> bool:
    return str(row.get(field, "")).strip().lower() in {"1", "true", "yes"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean-metrics", default=Path("reports/r7b_pure_clean_metrics.csv"), type=Path)
    parser.add_argument("--clean-dir", default=Path("results_candidate/r7b_pure_clean/public30"), type=Path)
    parser.add_argument("--variant", nargs=3, action="append", metavar=("NAME", "METRICS", "OUTDIR"), required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--csv", required=True, type=Path)
    args = parser.parse_args()

    variants: dict[str, tuple[dict[str, dict[str, str]], Path]] = {
        "clean": (load_metrics(args.clean_metrics), args.clean_dir)
    }
    for name, metrics, outdir in args.variant:
        variants[name] = (load_metrics(Path(metrics)), Path(outdir))

    args.out.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for case in sorted(variants["clean"][0]):
        clean_row = variants["clean"][0][case]
        clean_nodes = as_int(clean_row, "selected_nodes")
        clean_levels = as_int(clean_row, "selected_levels")
        best_name = "clean"
        best_row = clean_row
        for name, (metrics, _outdir) in variants.items():
            row = metrics.get(case)
            if not row or not as_bool(row, "cec_pass") or row.get("status") == "fallback":
                continue
            nodes = as_int(row, "selected_nodes")
            levels = as_int(row, "selected_levels")
            if nodes < as_int(best_row, "selected_nodes") and levels <= clean_levels:
                best_name = name
                best_row = row

        source_dir = variants[best_name][1] / case
        output_src = source_dir / "output.blif"
        candidate_src = source_dir / "output.candidate.blif"
        target_dir = args.out / case
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(output_src, target_dir / "output.blif")
        if candidate_src.exists():
            shutil.copyfile(candidate_src, target_dir / "output.candidate.blif")
        rows.append(
            {
                "case": case,
                "chosen_variant": best_name,
                "clean_nodes": clean_nodes,
                "chosen_nodes": as_int(best_row, "selected_nodes"),
                "node_gain_vs_clean": clean_nodes - as_int(best_row, "selected_nodes"),
                "clean_levels": clean_levels,
                "chosen_levels": as_int(best_row, "selected_levels"),
                "level_delta_vs_clean": as_int(best_row, "selected_levels") - clean_levels,
                "chosen_pipeline": best_row.get("selected_pipeline", ""),
                "chosen_status": best_row.get("status", ""),
                "chosen_cec_pass": as_bool(best_row, "cec_pass"),
                "source_output": str(output_src),
            }
        )

    args.csv.parent.mkdir(parents=True, exist_ok=True)
    with args.csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)

    total = sum(int(row["chosen_nodes"]) for row in rows)
    gain = sum(int(row["node_gain_vs_clean"]) for row in rows)
    max_level = max((int(row["chosen_levels"]) for row in rows), default=0)
    wins = sum(int(row["node_gain_vs_clean"]) > 0 for row in rows)
    gains = sorted((int(row["node_gain_vs_clean"]) for row in rows), reverse=True)
    gain_ex_best = gain - gains[0] if gains else 0
    gain_ex_top2 = gain - gains[0] - gains[1] if len(gains) > 1 else gain_ex_best
    print(
        f"wrote {args.csv}; outputs={args.out}; nodes={total}; gain={gain}; "
        f"max_level={max_level}; wins={wins}; gain_ex_best={gain_ex_best}; gain_ex_top2={gain_ex_top2}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
