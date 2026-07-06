#!/usr/bin/env python3
"""Validate Selector 2.0 candidate without modifying formal final configs."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path
from typing import Any

from eval_public import load_pipeline_steps, load_yaml_like
from run_abc_case import collect_stats, metric_tuple, run_cec, run_optimization
from select_pipeline import choose, validate_selector


FORBIDDEN_SELECTOR_KEYS = {"case", "path", "hash", "directory", "line_count", "pi_count", "po_count", "names_count", "cube_count"}
ALLOWED_SELECTOR_FIELDS = {
    "scale_grade",
    "pi_bin",
    "po_bin",
    "outputs_bin",
    "names_bin",
    "cubes_bin",
    "max_fanin_bin",
    "average_fanin_bin",
    "two_input_ratio_bin",
    "high_fanin_sop",
    "near_two_input_aig",
    "level_bin",
    "runtime_size_bin",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = fields or list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {path}")


def i(row: dict[str, str], key: str) -> int:
    return int(float(row.get(key, "0") or 0))


def f(row: dict[str, str], key: str) -> float:
    return float(row.get(key, "0") or 0.0)


def as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def bin_count(value: int, cuts: list[int], labels: list[str]) -> str:
    for cut, label in zip(cuts, labels):
        if value < cut:
            return label
    return labels[-1]


def bin_float(value: float, cuts: list[float], labels: list[str]) -> str:
    for cut, label in zip(cuts, labels):
        if value < cut:
            return label
    return labels[-1]


def enrich_features(features: list[dict[str, str]], final_by_case: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for row in features:
        enriched = dict(row)
        names = i(row, "names_count")
        cubes = i(row, "cube_count")
        max_fanin = i(row, "max_fanin")
        avg_fanin = f(row, "avg_fanin")
        two_ratio = f(row, "two_input_ratio")
        final_level = i(final_by_case.get(row["case"], {}), "selected_levels")
        enriched["outputs_bin"] = row.get("po_bin") or bin_count(i(row, "po_count"), [8, 32, 128], ["po_tiny", "po_small", "po_medium", "po_large"])
        enriched["max_fanin_bin"] = bin_count(max_fanin, [3, 5, 9], ["fanin_le2", "fanin_3_4", "fanin_5_8", "fanin_9p"])
        enriched["average_fanin_bin"] = bin_float(avg_fanin, [1.7, 2.1, 3.1], ["avg_fanin_low", "avg_fanin_aigish", "avg_fanin_mid", "avg_fanin_high"])
        enriched["two_input_ratio_bin"] = bin_float(two_ratio, [0.6, 0.85, 0.97, 0.995], ["two_ratio_low", "two_ratio_mid", "two_ratio_high", "two_ratio_very_high", "two_ratio_near_one"])
        enriched["level_bin"] = bin_count(final_level, [6, 12, 20, 26], ["level_tiny", "level_small", "level_medium", "level_high", "level_very_high"])
        if names >= 5000 or cubes >= 10000:
            runtime_size = "runtime_large"
        elif names >= 1000 or cubes >= 2000:
            runtime_size = "runtime_medium"
        elif names >= 100 or cubes >= 200:
            runtime_size = "runtime_small"
        else:
            runtime_size = "runtime_tiny"
        enriched["runtime_size_bin"] = runtime_size
        out[row["case"]] = {k: str(v) for k, v in enriched.items()}
    return out


def validate_selector2(config: dict[str, Any]) -> None:
    validate_selector(config)
    for rule in config.get("rules", []):
        when = rule.get("when", {})
        for key in when:
            if key in FORBIDDEN_SELECTOR_KEYS or key.endswith("_eq"):
                raise ValueError(f"forbidden selector key in {rule.get('name')}: {key}")
            field = key
            for suffix in ("_in", "_min", "_max"):
                if field.endswith(suffix):
                    field = field[: -len(suffix)]
            if field not in ALLOWED_SELECTOR_FIELDS:
                raise ValueError(f"selector key not in Phase 7 coarse allowlist in {rule.get('name')}: {key}")


def regression_reason(raw_nodes: int, raw_levels: int, final_row: dict[str, str]) -> str:
    final_nodes = i(final_row, "selected_nodes")
    final_levels = i(final_row, "selected_levels")
    if raw_nodes > final_nodes:
        return f"nodes_worse:{raw_nodes - final_nodes}"
    if raw_nodes == final_nodes and raw_levels > final_levels:
        return f"level_worse:{raw_levels - final_levels}"
    return ""


def total_final_time(row: dict[str, str]) -> float:
    return f(row, "opt_runtime_sec") + f(row, "cec_runtime_sec") + f(row, "stats_runtime_sec")


def run_selected_case(
    abc: Path,
    cases_dir: Path,
    out_dir: Path,
    case: str,
    pipeline: str,
    reason: str,
    steps: str,
    final_row: dict[str, str],
    timeouts: dict[str, float],
) -> dict[str, Any]:
    input_blif = cases_dir / case / "input.blif"
    case_dir = out_dir / case
    log_dir = case_dir / "logs"
    raw_path = case_dir / "raw.candidate.blif"
    selected_path = case_dir / "output.blif"
    row: dict[str, Any] = {
        "case": case,
        "selected_pipeline": pipeline,
        "selector_reason": reason,
        "raw_nodes": "",
        "raw_levels": "",
        "raw_cec_status": "not_run",
        "raw_status": "not_run",
        "selected_nodes": final_row["selected_nodes"],
        "selected_levels": final_row["selected_levels"],
        "selected_status": "fallback_current_final",
        "fallback_used": "true",
        "fallback_reason": "not_run",
        "final_pipeline": final_row["requested_pipeline"],
        "final_nodes": final_row["selected_nodes"],
        "final_levels": final_row["selected_levels"],
        "raw_node_delta_vs_final": "",
        "raw_level_delta_vs_final": "",
        "selected_node_delta_vs_final": 0,
        "selected_level_delta_vs_final": 0,
        "opt_time": "0.000000",
        "cec_time": "0.000000",
        "stats_time": "0.000000",
        "total_time": "0.000000",
        "peak_RSS": "0.000",
        "runtime_ratio_vs_final": "",
        "rss_ratio_vs_final": "",
        "opt_returncode": "",
        "cec_returncode": "",
        "output_path": str(selected_path),
        "candidate_path": str(raw_path),
        "log_dir": str(log_dir),
    }

    opt = run_optimization(abc, input_blif, raw_path, steps, timeouts["opt"], log_dir / "raw_opt.log")
    row["opt_time"] = f"{opt.runtime_sec:.6f}"
    row["opt_returncode"] = opt.returncode
    peak = opt.peak_mem_mb
    if opt.timed_out:
        row["raw_status"] = "timeout"
        row["fallback_reason"] = "opt_timeout"
    elif opt.returncode != 0 or not raw_path.exists():
        row["raw_status"] = "crash"
        row["fallback_reason"] = "opt_crash_or_missing_output"
    else:
        cec_pass, cec = run_cec(abc, input_blif, raw_path, timeouts["cec"], log_dir / "raw_cec.log")
        row["cec_time"] = f"{cec.runtime_sec:.6f}"
        row["cec_returncode"] = cec.returncode
        peak = max(peak, cec.peak_mem_mb)
        if cec.timed_out:
            row["raw_cec_status"] = "timeout"
            row["raw_status"] = "timeout"
            row["fallback_reason"] = "cec_timeout"
        elif not cec_pass:
            row["raw_cec_status"] = "failed"
            row["raw_status"] = "cec_failed"
            row["fallback_reason"] = "cec_failed"
        else:
            row["raw_cec_status"] = "passed"
            metrics, stats = collect_stats(abc, raw_path, timeouts["stats"], log_dir / "raw_stats.log")
            row["stats_time"] = f"{stats.runtime_sec:.6f}"
            peak = max(peak, stats.peak_mem_mb)
            raw_nodes, raw_levels = metric_tuple(metrics)
            if raw_nodes is None or raw_levels is None:
                row["raw_status"] = "stats_failed"
                row["fallback_reason"] = "stats_failed"
            else:
                row["raw_nodes"] = raw_nodes
                row["raw_levels"] = raw_levels
                row["raw_node_delta_vs_final"] = raw_nodes - i(final_row, "selected_nodes")
                row["raw_level_delta_vs_final"] = raw_levels - i(final_row, "selected_levels")
                reason_text = regression_reason(raw_nodes, raw_levels, final_row)
                if reason_text:
                    row["raw_status"] = "metric_regression"
                    row["fallback_reason"] = f"metric_regression: {reason_text}"
                else:
                    row["raw_status"] = "ok"
                    row["selected_nodes"] = raw_nodes
                    row["selected_levels"] = raw_levels
                    row["selected_status"] = "selected_raw"
                    row["fallback_used"] = "false"
                    row["fallback_reason"] = ""
                    selected_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(raw_path, selected_path)

    if row["fallback_used"] == "true":
        fallback_steps = steps if pipeline == final_row["requested_pipeline"] else ""
        if fallback_steps:
            fallback_raw = case_dir / "fallback_current_final.blif"
            fb_opt = run_optimization(abc, input_blif, fallback_raw, fallback_steps, timeouts["opt"], log_dir / "fallback_opt.log")
            fb_cec_pass = False
            if fb_opt.returncode == 0 and fallback_raw.exists() and not fb_opt.timed_out:
                fb_cec_pass, fb_cec = run_cec(abc, input_blif, fallback_raw, timeouts["cec"], log_dir / "fallback_cec.log")
                peak = max(peak, fb_cec.peak_mem_mb)
            if fb_cec_pass:
                selected_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(fallback_raw, selected_path)
        # For non-current-final fallback, selected metrics stay equal to frozen current final metrics.

    row["selected_node_delta_vs_final"] = i({k: str(v) for k, v in row.items()}, "selected_nodes") - i(final_row, "selected_nodes")
    row["selected_level_delta_vs_final"] = i({k: str(v) for k, v in row.items()}, "selected_levels") - i(final_row, "selected_levels")
    total_time = f({k: str(v) for k, v in row.items()}, "opt_time") + f({k: str(v) for k, v in row.items()}, "cec_time") + f({k: str(v) for k, v in row.items()}, "stats_time")
    row["total_time"] = f"{total_time:.6f}"
    row["peak_RSS"] = f"{peak:.3f}"
    final_time = total_final_time(final_row)
    final_rss = f(final_row, "peak_mem_mb")
    if final_time > 0:
        row["runtime_ratio_vs_final"] = f"{total_time / final_time:.6f}"
    if final_rss > 0:
        row["rss_ratio_vs_final"] = f"{peak / final_rss:.6f}"
    return row


def summarize(rows: list[dict[str, Any]], final_rows: dict[str, dict[str, str]]) -> dict[str, Any]:
    deltas = [i({k: str(v) for k, v in row.items()}, "selected_node_delta_vs_final") for row in rows]
    gains = sorted([-d for d in deltas], reverse=True)
    selected_nodes = sum(i({k: str(v) for k, v in row.items()}, "selected_nodes") for row in rows)
    raw_nodes = sum(i({k: str(v) for k, v in row.items()}, "raw_nodes") for row in rows if row["raw_nodes"] != "")
    return {
        "cases": len(rows),
        "selected_total_nodes": selected_nodes,
        "raw_total_nodes": raw_nodes,
        "max_selected_level": max(i({k: str(v) for k, v in row.items()}, "selected_levels") for row in rows),
        "max_raw_level": max(i({k: str(v) for k, v in row.items()}, "raw_levels") for row in rows if row["raw_levels"] != ""),
        "raw_cec_passed": sum(1 for row in rows if row["raw_cec_status"] == "passed"),
        "fallback_count": sum(1 for row in rows if as_bool(row["fallback_used"])),
        "crash_count": sum(1 for row in rows if row["raw_status"] == "crash"),
        "timeout_count": sum(1 for row in rows if row["raw_status"] == "timeout"),
        "cec_fail_count": sum(1 for row in rows if row["raw_status"] == "cec_failed"),
        "wins": sum(1 for d in deltas if d < 0),
        "ties": sum(1 for d in deltas if d == 0),
        "losses": sum(1 for d in deltas if d > 0),
        "gain_excluding_best_case": sum(gains[1:]) if gains else 0,
        "gain_excluding_top2_cases": sum(gains[2:]) if len(gains) >= 2 else 0,
        "total_opt_time": round(sum(f({k: str(v) for k, v in row.items()}, "opt_time") for row in rows), 6),
        "total_cec_time": round(sum(f({k: str(v) for k, v in row.items()}, "cec_time") for row in rows), 6),
        "total_time": round(sum(f({k: str(v) for k, v in row.items()}, "total_time") for row in rows), 6),
        "peak_RSS": round(max(f({k: str(v) for k, v in row.items()}, "peak_RSS") for row in rows), 3),
        "runtime_warning_count": sum(1 for row in rows if f({k: str(v) for k, v in row.items()}, "runtime_ratio_vs_final") > 2.5),
        "rss_warning_count": sum(1 for row in rows if f({k: str(v) for k, v in row.items()}, "rss_ratio_vs_final") > 2.0),
        "current_final_nodes": sum(i(row, "selected_nodes") for row in final_rows.values()),
    }


def write_findings(path: Path, choices: list[dict[str, Any]], validation: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    switched = [row for row in choices if row["selected_pipeline"] == "high_aig_three_round"]
    retained = [row for row in choices if row["selected_pipeline"] != "high_aig_three_round"]
    level_regs = [row for row in validation if i({k: str(v) for k, v in row.items()}, "selected_level_delta_vs_final") > 0]
    lines = [
        "# Selector 2.0 Findings",
        "",
        "Phase 7 only. This candidate was validated without modifying `configs/final_selector.yaml`, `configs/pipelines.yaml`, or the submit package.",
        "",
        "## Rule",
        "",
        "`large_runtime_aig_high_effort`: choose `high_aig_three_round` only when `scale_grade in [large]`, `high_fanin_sop=false`, `near_two_input_aig=true`, and `runtime_size_bin in [runtime_large]`.",
        "",
        "All other buckets retain the current final selector behavior: tiny/small high-fanin SOP -> `sop_fx`, medium non-AIG-like -> `rewrite2`, default -> `dc2_fast`.",
        "",
        "## Validation Summary",
        "",
        f"- Selected total nodes: {summary['selected_total_nodes']} vs current final {summary['current_final_nodes']}.",
        f"- Raw total nodes: {summary['raw_total_nodes']}.",
        f"- Max selected level: {summary['max_selected_level']}.",
        f"- Raw CEC: {summary['raw_cec_passed']}/30.",
        f"- Fallback count: {summary['fallback_count']}.",
        f"- Wins/ties/losses vs current final: {summary['wins']}/{summary['ties']}/{summary['losses']}.",
        f"- gain_excluding_best_case: {summary['gain_excluding_best_case']}.",
        f"- gain_excluding_top2_cases: {summary['gain_excluding_top2_cases']}.",
        f"- Runtime/RSS warning counts: {summary['runtime_warning_count']}/{summary['rss_warning_count']}.",
        "",
        "## Switched Cases",
        "",
        "| case | bucket | selected pipeline | reason |",
        "| --- | --- | --- | --- |",
    ]
    for row in switched:
        bucket = f"{row['scale_grade']}|{row['runtime_size_bin']}|near_aig={row['near_two_input_aig']}|high_sop={row['high_fanin_sop']}"
        lines.append(f"| {row['case']} | {bucket} | {row['selected_pipeline']} | {row['selector_reason']} |")
    lines.extend(["", "## Retained Current Final Cases", "", f"{len(retained)} cases retained current final pipeline choices.", ""])
    if level_regs:
        lines.extend(["## Level Regressions", "", "| case | selected pipeline | level delta |", "| --- | --- | ---: |"])
        for row in level_regs:
            lines.append(f"| {row['case']} | {row['selected_pipeline']} | {row['selected_level_delta_vs_final']} |")
        lines.append("")
    else:
        lines.extend(["## Level Regressions", "", "No selected-level regression was observed.", ""])
    phase8_ok = (
        summary["selected_total_nodes"] < summary["current_final_nodes"]
        and summary["raw_cec_passed"] == 30
        and summary["max_selected_level"] <= 25
        and summary["fallback_count"] == 0
        and summary["gain_excluding_best_case"] > 0
        and summary["gain_excluding_top2_cases"] >= 0
        and summary["runtime_warning_count"] == 0
        and summary["rss_warning_count"] == 0
    )
    lines.extend(
        [
            "## Phase 8 Gate",
            "",
            f"- Meets Phase 8 numeric gate: {'yes' if phase8_ok else 'no'}.",
            "- Selector rule uses only coarse structural features and does not reference file names, paths, hashes, exact counts, public case ids, or oracle results.",
            "- The high-effort rule covers a multi-case large AIG-like bucket, not a single public case.",
            "",
            "## Stop Point",
            "",
            "Phase 7 completed. Phase 8 decision and final replacement were not run.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--abc", required=True, type=Path)
    parser.add_argument("--cases", default=Path("data/tc_public"), type=Path)
    parser.add_argument("--features", default=Path("reports/features.csv"), type=Path)
    parser.add_argument("--final", default=Path("reports/final_metrics.csv"), type=Path)
    parser.add_argument("--selector", default=Path("configs/final_selector_candidate_v2.yaml"), type=Path)
    parser.add_argument("--pipelines", default=Path("configs/pipelines_candidate_v2.yaml"), type=Path)
    parser.add_argument("--out-dir", default=Path("results/pipeline_search2/selector2"), type=Path)
    parser.add_argument("--choices", default=Path("reports/selector2_choices.csv"), type=Path)
    parser.add_argument("--validation", default=Path("reports/selector2_validation.csv"), type=Path)
    parser.add_argument("--findings", default=Path("docs/selector2_findings.md"), type=Path)
    parser.add_argument("--opt-timeout", type=float, default=300.0)
    parser.add_argument("--cec-timeout", type=float, default=300.0)
    parser.add_argument("--stats-timeout", type=float, default=120.0)
    args = parser.parse_args()

    selector_config = load_yaml_like(args.selector)
    validate_selector2(selector_config)
    pipeline_config = load_yaml_like(args.pipelines)
    final_rows = {row["case"]: row for row in read_csv(args.final)}
    features = enrich_features(read_csv(args.features), final_rows)

    choices: list[dict[str, Any]] = []
    validation: list[dict[str, Any]] = []
    for case in sorted(final_rows):
        feature_row = features[case]
        pipeline, reason = choose(feature_row, selector_config)
        choices.append({**feature_row, "selected_pipeline": pipeline, "selector_reason": reason, "current_final_pipeline": final_rows[case]["requested_pipeline"]})
        steps = load_pipeline_steps(pipeline_config, pipeline)
        print(f"[selector2][{case}] {pipeline} ({reason})")
        validation.append(
            run_selected_case(
                args.abc,
                args.cases,
                args.out_dir,
                case,
                pipeline,
                reason,
                steps,
                final_rows[case],
                {"opt": args.opt_timeout, "cec": args.cec_timeout, "stats": args.stats_timeout},
            )
        )

    write_csv(args.choices, choices)
    write_csv(args.validation, validation)
    summary = summarize(validation, final_rows)
    summary_path = args.validation.with_name("selector2_summary.csv")
    write_csv(summary_path, [summary])
    write_findings(args.findings, choices, validation, summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
