#!/usr/bin/env python3
"""R29 research-only post-pass matrix on top of the v6 formal outputs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from run_abc_case import collect_stats, run_cec, run_optimization


PIPELINES: dict[str, str] = {
    "r29_fraig_dc2_bal": "fraig; dc2; balance",
    "r29_mfs_dc2_bal": "mfs; dc2; balance",
    "r29_mfs_strash_dc2_bal": "mfs; strash; dc2; balance",
    "r29_mfs_strash_dc2_rwz_bal": "mfs; strash; dc2; rewrite -z; balance",
    "r29_mfs_fraig_bal": "mfs; fraig; balance",
    "r29_mfs_fraig_dc2_bal": "mfs; fraig; dc2; balance",
    "r29_fraig_mfs_dc2_bal": "fraig; mfs; dc2; balance",
    "r29_mfs_fraig_dc2_rwz_bal": "mfs; fraig; dc2; rewrite -z; balance",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def to_int(value: Any) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return 0


def to_float(value: Any) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return 0.0


def case_key(name: str) -> tuple[int, str]:
    digits = "".join(ch for ch in name if ch.isdigit())
    return (int(digits) if digits else 0, name)


def load_joined(metrics_path: Path, features_path: Path) -> list[dict[str, str]]:
    metrics = {row["case"]: row for row in read_csv(metrics_path)}
    features = {row["case"]: row for row in read_csv(features_path)}
    rows: list[dict[str, str]] = []
    for case, metric in metrics.items():
        row = {**features.get(case, {}), **metric}
        row["case"] = case
        row["selector_bucket"] = f"{row.get('selector_reason', '')}@{row.get('chosen_variant', '')}"
        row["r29_target_gate"] = "true" if row.get("r28_gated_r27_status") in {"accepted", "rejected"} else "false"
        rows.append(row)
    return sorted(rows, key=lambda r: case_key(r["case"]))


def add_unique(selected: list[dict[str, str]], row: dict[str, str], reason: str) -> None:
    if any(item["case"] == row["case"] for item in selected):
        return
    copy = dict(row)
    copy["smoke_selection_reason"] = reason
    selected.append(copy)


def select_smoke_rows(rows: list[dict[str, str]], limit: int) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []

    for row in rows:
        if row.get("r28_gated_r27_status") in {"accepted", "rejected"}:
            add_unique(selected, row, "all previously attempted R28 structural gates")

    def pick_best(predicate, key, reason: str, reverse: bool = True) -> None:
        candidates = [row for row in rows if predicate(row) and row["case"] not in {x["case"] for x in selected}]
        if not candidates:
            return
        candidates.sort(key=key, reverse=reverse)
        add_unique(selected, candidates[0], reason)

    pick_best(
        lambda r: r.get("requested_pipeline") == "r9_dc2_fraig_cleanup",
        lambda r: to_int(r.get("selected_nodes")),
        "largest large-smallPO FRAIG/DC2 control",
    )
    pick_best(
        lambda r: r.get("requested_pipeline") == "r11_gia_deepsyn_tiny",
        lambda r: to_float(r.get("opt_runtime_sec")),
        "slowest distilled GIA/deepsyn control",
    )
    pick_best(
        lambda r: r.get("requested_pipeline") == "r10_medium_fraig_cleanup",
        lambda r: to_int(r.get("selected_nodes")),
        "largest medium FRAIG cleanup control",
    )
    pick_best(
        lambda r: str(r.get("high_fanin_sop")).lower() == "true",
        lambda r: to_int(r.get("selected_nodes")),
        "largest high-fanin SOP control",
    )
    pick_best(
        lambda r: r.get("requested_pipeline") == "dc2_fast",
        lambda r: to_int(r.get("selected_nodes")),
        "largest default dc2 control",
    )

    if len(selected) < limit:
        for row in sorted(rows, key=lambda r: to_int(r.get("selected_nodes")), reverse=True):
            add_unique(selected, row, "fill by largest remaining selected_nodes")
            if len(selected) >= limit:
                break

    return selected[:limit]


def select_smoke(args: argparse.Namespace) -> int:
    rows = load_joined(args.metrics, args.features)
    selected = select_smoke_rows(rows, args.limit)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    selection_path = args.out_dir / "R29_smoke_selection.csv"
    case_list_path = args.out_dir / "R29_smoke_cases.txt"
    fields = [
        "case",
        "smoke_selection_reason",
        "selector_reason",
        "requested_pipeline",
        "selected_pipeline",
        "chosen_variant",
        "selected_nodes",
        "selected_levels",
        "original_nodes",
        "original_levels",
        "opt_runtime_sec",
        "peak_mem_mb",
        "scale_grade",
        "pi_bin",
        "po_bin",
        "names_bin",
        "cubes_bin",
        "near_two_input_aig",
        "high_fanin_sop",
        "runtime_size_bin",
        "r28_gated_r27_status",
        "r28_node_delta_vs_v5",
        "r28_level_delta_vs_v5",
    ]
    write_csv(selection_path, selected, fields)
    case_list_path.write_text("\n".join(row["case"] for row in selected) + "\n", encoding="utf-8")
    print(f"selected {len(selected)} smoke cases")
    print(selection_path)
    print(case_list_path)
    return 0


def input_path_for(row: dict[str, str], cases_root: Path | None) -> Path:
    raw = Path(row.get("input_path", ""))
    if raw.exists():
        return raw
    if cases_root:
        candidate = cases_root / row["case"] / "input.blif"
        if candidate.exists():
            return candidate
    return raw


def run_smoke(args: argparse.Namespace) -> int:
    metrics = {row["case"]: row for row in read_csv(args.metrics)}
    case_names = [
        line.strip()
        for line in args.case_list.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    names = args.pipeline_names or list(PIPELINES.keys())
    unknown = [name for name in names if name not in PIPELINES]
    if unknown:
        raise SystemExit(f"unknown pipelines: {', '.join(unknown)}")

    rows: list[dict[str, Any]] = []
    for case in case_names:
        base = metrics[case]
        input_blif = input_path_for(base, args.cases_root)
        baseline_blif = args.outputs_root / case / "output.blif"
        base_nodes = to_int(base.get("selected_nodes"))
        base_levels = to_int(base.get("selected_levels"))
        if not input_blif.exists() or not baseline_blif.exists():
            rows.append(
                {
                    "case": case,
                    "candidate": "",
                    "status": "missing_input_or_baseline",
                    "input_path": str(input_blif),
                    "baseline_path": str(baseline_blif),
                    "baseline_nodes": base_nodes,
                    "baseline_levels": base_levels,
                }
            )
            continue

        for name in names:
            steps = PIPELINES[name]
            case_dir = args.out_dir / "runs" / name / case
            output_blif = case_dir / "output.blif"
            opt = run_optimization(args.abc, baseline_blif, output_blif, steps, args.opt_timeout, case_dir / "opt.log")
            opt_error = "Error:" in (opt.stdout + opt.stderr) or "usage:" in (opt.stdout + opt.stderr)
            opt_ok = opt.returncode == 0 and not opt.timed_out and not opt_error and output_blif.exists()
            cec_pass = False
            cec = None
            stats_result = None
            stats: dict[str, Any] = {}
            nodes = 0
            levels = 0
            if opt_ok:
                cec_pass, cec = run_cec(args.abc, input_blif, output_blif, args.cec_timeout, case_dir / "cec.log")
                stats, stats_result = collect_stats(args.abc, output_blif, args.stats_timeout, case_dir / "stats.log")
                nodes = to_int(stats.get("aig_nodes"))
                levels = to_int(stats.get("levels"))
            else:
                (case_dir / "cec.log").write_text("cec skipped because optimization failed\n", encoding="utf-8")
                (case_dir / "stats.log").write_text("stats skipped because optimization failed\n", encoding="utf-8")

            if opt.timed_out or (cec and cec.timed_out) or (stats_result and stats_result.timed_out):
                status = "timeout"
            elif not opt_ok:
                status = "opt_failed"
            elif not cec_pass:
                status = "cec_failed"
            elif nodes <= 0:
                status = "stats_missing"
            elif nodes < base_nodes and levels <= base_levels:
                status = "accepted"
            elif nodes >= base_nodes:
                status = "no_node_gain"
            elif levels > base_levels:
                status = "level_regression"
            else:
                status = "rejected"

            peak = max(
                opt.peak_mem_mb,
                cec.peak_mem_mb if cec else 0.0,
                stats_result.peak_mem_mb if stats_result else 0.0,
            )
            rows.append(
                {
                    "case": case,
                    "candidate": name,
                    "steps": steps,
                    "selector_reason": base.get("selector_reason", ""),
                    "selected_pipeline": base.get("selected_pipeline", ""),
                    "chosen_variant": base.get("chosen_variant", ""),
                    "baseline_nodes": base_nodes,
                    "baseline_levels": base_levels,
                    "nodes_after": nodes,
                    "levels_after": levels,
                    "node_delta": nodes - base_nodes if nodes else "",
                    "level_delta": levels - base_levels if levels else "",
                    "status": status,
                    "cec_pass": cec_pass,
                    "opt_returncode": opt.returncode,
                    "opt_timed_out": opt.timed_out,
                    "opt_error": opt_error,
                    "cec_returncode": cec.returncode if cec else "",
                    "runtime_opt_sec": float(f"{opt.runtime_sec:.6f}"),
                    "runtime_cec_sec": float(f"{cec.runtime_sec:.6f}") if cec else 0.0,
                    "runtime_stats_sec": float(f"{stats_result.runtime_sec:.6f}") if stats_result else 0.0,
                    "peak_mem_mb": float(f"{peak:.3f}"),
                    "input_path": str(input_blif),
                    "baseline_path": str(baseline_blif),
                    "output_path": str(output_blif),
                    "log_dir": str(case_dir),
                }
            )
            print(f"[{case}][{name}] {status} delta={nodes - base_nodes if nodes else ''} level_delta={levels - base_levels if levels else ''}")

    fieldnames = [
        "case",
        "candidate",
        "steps",
        "selector_reason",
        "selected_pipeline",
        "chosen_variant",
        "baseline_nodes",
        "baseline_levels",
        "nodes_after",
        "levels_after",
        "node_delta",
        "level_delta",
        "status",
        "cec_pass",
        "opt_returncode",
        "opt_timed_out",
        "opt_error",
        "cec_returncode",
        "runtime_opt_sec",
        "runtime_cec_sec",
        "runtime_stats_sec",
        "peak_mem_mb",
        "input_path",
        "baseline_path",
        "output_path",
        "log_dir",
    ]
    write_csv(args.csv, rows, fieldnames)
    write_smoke_summary(args.summary, args.csv, rows)
    return 0


def write_smoke_summary(path: Path, csv_path: Path, rows: list[dict[str, Any]]) -> None:
    valid = [row for row in rows if row.get("candidate")]
    by_candidate: dict[str, list[dict[str, Any]]] = {}
    for row in valid:
        by_candidate.setdefault(str(row["candidate"]), []).append(row)

    lines = [
        "---",
        "research_id: R29-POSTPASS-MATRIX-V6",
        "status: active",
        "baseline_tag: final_selector_v6_20260626",
        "baseline_commit: ffd327f5013e5bef4913750579a99dacf0c4dcfb",
        "branch: research/r29-postpass-matrix-v6",
        "created: 2026-06-26",
        "updated: 2026-06-26",
        "affects_final: false",
        "supersedes: []",
        "superseded_by: []",
        "primary_data:",
        f"  - {csv_path.as_posix()}",
        "---",
        "",
        "# R29 Post-pass Matrix Full 30 Summary" if "full30" in path.name.lower() else "# R29 Post-pass Matrix Smoke Summary",
        "",
        "## Objective",
        "",
        "Test lightweight post-pass variants on top of the v6 formal outputs without modifying the formal selector or submit archive.",
        "",
        "## Baseline",
        "",
        "`final_selector_v6_20260626`: 37464 nodes, max level 20, CEC 30/30, fallback 0.",
        "",
        "## Commands",
        "",
        "Generated by `tools/r29_postpass_matrix.py smoke`.",
        "",
        "## Input Data",
        "",
        "Inputs come from the v6 metrics `input_path` fields and baseline outputs from `submit/results/final_public`.",
        "",
        "## Results",
        "",
        "| candidate | accepted | cec_fail | timeout | opt_fail | level_regression | total_safe_gain | best_gain | gain_ex_best | gain_ex_top2 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, candidate_rows in sorted(by_candidate.items()):
        accepted = [row for row in candidate_rows if row.get("status") == "accepted"]
        gains = [-to_int(row.get("node_delta")) for row in accepted]
        total_gain = sum(gains)
        best_gain = max(gains, default=0)
        top2_gain = sum(sorted(gains, reverse=True)[:2])
        cec_fail = sum(1 for row in candidate_rows if row.get("status") == "cec_failed")
        timeout = sum(1 for row in candidate_rows if row.get("status") == "timeout")
        opt_fail = sum(1 for row in candidate_rows if row.get("status") == "opt_failed")
        level_regression = sum(1 for row in candidate_rows if row.get("status") == "level_regression")
        lines.append(
            f"| `{name}` | {len(accepted)} | {cec_fail} | {timeout} | {opt_fail} | {level_regression} | "
            f"{total_gain} | {best_gain} | {total_gain - best_gain} | {total_gain - top2_gain} |"
        )

    lines.extend(
        [
            "",
            "## Correctness",
            "",
            "Each attempted output is checked with ABC CEC against the original input before a row can be `accepted`.",
            "",
            "## Risk",
            "",
            "This is smoke evidence only. A candidate must still pass full public 30 before any candidate selector work.",
            "",
            "## Selector Eligibility",
            "",
            "No selector was generated. Case names appear only for audit; promotion would require coarse structural predicates.",
            "",
            "## Conclusion",
            "",
            "Decision label: `continue` if any candidate has at least two safe smoke gains and positive total safe gain; otherwise `research-only`.",
            "",
            "## Next Action",
            "",
            "Review the smoke CSV and decide whether any candidate should enter full public 30.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sel = sub.add_parser("select-smoke")
    sel.add_argument("--metrics", type=Path, default=Path("reports/final_metrics.csv"))
    sel.add_argument("--features", type=Path, default=Path("reports/features.csv"))
    sel.add_argument("--out-dir", type=Path, default=Path("results_research/R29_postpass_matrix_v6"))
    sel.add_argument("--limit", type=int, default=10)
    sel.set_defaults(func=select_smoke)

    smoke = sub.add_parser("smoke")
    smoke.add_argument("--abc", type=Path, default=Path("submit/bin/abc.exe"))
    smoke.add_argument("--metrics", type=Path, default=Path("reports/final_metrics.csv"))
    smoke.add_argument("--case-list", type=Path, default=Path("results_research/R29_postpass_matrix_v6/R29_smoke_cases.txt"))
    smoke.add_argument("--outputs-root", type=Path, default=Path("submit/results/final_public"))
    smoke.add_argument("--cases-root", type=Path)
    smoke.add_argument("--out-dir", type=Path, default=Path("results_research/R29_postpass_matrix_v6"))
    smoke.add_argument("--csv", type=Path, default=Path("results_research/R29_postpass_matrix_v6/R29_postpass_smoke.csv"))
    smoke.add_argument("--summary", type=Path, default=Path("results_research/R29_postpass_matrix_v6/R29_postpass_smoke_summary.md"))
    smoke.add_argument("--pipeline-names", nargs="*")
    smoke.add_argument("--opt-timeout", type=float, default=90.0)
    smoke.add_argument("--cec-timeout", type=float, default=300.0)
    smoke.add_argument("--stats-timeout", type=float, default=120.0)
    smoke.set_defaults(func=run_smoke)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
