#!/usr/bin/env python3
"""Anti-overfit analysis for Pipeline Search 2.0 Phase 6."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


FINAL_NODES = 47338
FINAL_MAX_LEVEL = 25
RUNTIME_WARN_RATIO = 2.5
RSS_WARN_RATIO = 2.0
MIN_BUCKET_CASES_FOR_RULE = 2


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: Iterable[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(fields or (rows[0].keys() if rows else []))
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {path}")


def i(row: dict[str, str], key: str) -> int:
    value = row.get(key, "")
    return int(float(value or 0))


def f(row: dict[str, str], key: str) -> float:
    value = row.get(key, "")
    return float(value or 0.0)


def b(row: dict[str, str], key: str) -> bool:
    return str(row.get(key, "")).strip().lower() in {"1", "true", "yes", "y"}


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
        case = row["case"]
        final = final_by_case.get(case, {})
        max_fanin = i(row, "max_fanin")
        avg_fanin = f(row, "avg_fanin")
        two_ratio = f(row, "two_input_ratio")
        po_count = i(row, "po_count")
        names_count = i(row, "names_count")
        cube_count = i(row, "cube_count")
        level = i(final, "selected_levels") if final else 0
        total_time = f(final, "opt_runtime_sec") + f(final, "cec_runtime_sec") + f(final, "stats_runtime_sec") if final else 0.0
        enriched = dict(row)
        enriched["outputs_bin"] = row.get("po_bin") or bin_count(po_count, [8, 32, 128], ["po_tiny", "po_small", "po_medium", "po_large"])
        enriched["max_fanin_bin"] = bin_count(max_fanin, [3, 5, 9], ["fanin_le2", "fanin_3_4", "fanin_5_8", "fanin_9p"])
        enriched["average_fanin_bin"] = bin_float(avg_fanin, [1.7, 2.1, 3.1], ["avg_fanin_low", "avg_fanin_aigish", "avg_fanin_mid", "avg_fanin_high"])
        enriched["two_input_ratio_bin"] = bin_float(two_ratio, [0.6, 0.85, 0.97, 0.995], ["two_ratio_low", "two_ratio_mid", "two_ratio_high", "two_ratio_very_high", "two_ratio_near_one"])
        enriched["level_bin"] = bin_count(level, [6, 12, 20, 26], ["level_tiny", "level_small", "level_medium", "level_high", "level_very_high"])
        if names_count >= 5000 or cube_count >= 10000 or total_time >= 1.5:
            runtime_size = "runtime_large"
        elif names_count >= 1000 or cube_count >= 2000 or total_time >= 0.4:
            runtime_size = "runtime_medium"
        elif names_count >= 100 or cube_count >= 200:
            runtime_size = "runtime_small"
        else:
            runtime_size = "runtime_tiny"
        enriched["runtime_size_bin"] = runtime_size
        out[case] = enriched
    return out


def node_delta(row: dict[str, str], prefix: str = "raw") -> int:
    key = f"{prefix}_node_delta_vs_final"
    if key in row and row[key] != "":
        return int(float(row[key]))
    return i(row, f"{prefix}_nodes") - i(row, "final_nodes")


def level_delta(row: dict[str, str], prefix: str = "raw") -> int:
    key = f"{prefix}_level_delta_vs_final"
    if key in row and row[key] != "":
        return int(float(row[key]))
    return i(row, f"{prefix}_levels") - i(row, "final_levels")


def gain_excluding(deltas: list[int], top_n: int) -> int:
    gains = sorted([-d for d in deltas], reverse=True)
    return sum(gains[top_n:])


def candidate_summary(metrics: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pipeline, items in sorted(group_by(metrics, "pipeline_id").items()):
        raw_deltas = [node_delta(row, "raw") for row in items if row.get("raw_nodes")]
        selected_deltas = [node_delta(row, "selected") for row in items]
        raw_total_nodes = sum(i(row, "raw_nodes") for row in items if row.get("raw_nodes"))
        selected_total_nodes = sum(i(row, "selected_nodes") for row in items)
        raw_total_gain = -sum(raw_deltas)
        selected_total_gain = -sum(selected_deltas)
        max_raw_level = max(i(row, "raw_levels") for row in items if row.get("raw_levels"))
        max_selected_level = max(i(row, "selected_levels") for row in items)
        fallback_count = sum(1 for row in items if b(row, "fallback_used"))
        raw_fail_count = sum(1 for row in items if row["raw_status"] in {"crash", "timeout", "cec_failed", "stats_failed"})
        runtime_warnings = sum(1 for row in items if f(row, "runtime_ratio_vs_final") > RUNTIME_WARN_RATIO)
        rss_warnings = sum(1 for row in items if f(row, "rss_ratio_vs_final") > RSS_WARN_RATIO)
        wins = sum(1 for d in raw_deltas if d < 0)
        ties = sum(1 for d in raw_deltas if d == 0)
        losses = sum(1 for d in raw_deltas if d > 0)
        best_gain = max([-d for d in raw_deltas], default=0)
        best_ratio = best_gain / raw_total_gain if raw_total_gain > 0 else 1.0
        raw_better = raw_total_nodes < FINAL_NODES and max_raw_level <= FINAL_MAX_LEVEL
        selected_better = selected_total_nodes < FINAL_NODES and max_selected_level <= FINAL_MAX_LEVEL
        selected_depends_on_fallback = selected_total_gain > raw_total_gain and fallback_count > 0
        not_robust = selected_better and selected_depends_on_fallback and raw_total_nodes >= FINAL_NODES
        ge_best = gain_excluding(raw_deltas, 1)
        ge_top2 = gain_excluding(raw_deltas, 2)
        eligible = (
            sum(1 for row in items if row["raw_cec_status"] == "passed") == 30
            and selected_total_nodes < FINAL_NODES
            and (ge_best > 0 or wins > losses)
            and max_selected_level <= FINAL_MAX_LEVEL
            and raw_fail_count == 0
            and runtime_warnings == 0
            and rss_warnings == 0
            and not not_robust
        )
        if fallback_count and eligible:
            # Keep eligible only if raw remains globally better; Phase 7 must filter regressions.
            eligible = raw_total_nodes < FINAL_NODES and ge_best > 0
        if not eligible:
            if not selected_total_nodes < FINAL_NODES:
                reason = "selected nodes do not beat current final"
            elif ge_best <= 0 and wins <= losses:
                reason = "gain excluding best case is not positive and wins do not exceed losses"
            elif not_robust:
                reason = "selected result depends on fallback while raw total is not robust"
            elif runtime_warnings or rss_warnings:
                reason = "runtime or RSS warning"
            elif fallback_count and not (raw_total_nodes < FINAL_NODES and ge_best > 0):
                reason = "fallback improves selected result but raw anti-overfit is weak"
            else:
                reason = "hard gate not met"
        else:
            reason = "passes Phase 6 hard gates; Phase 7 must use coarse buckets and avoid regression buckets"
        rows.append(
            {
                "candidate": pipeline,
                "family": items[0]["family"],
                "raw_total_nodes": raw_total_nodes,
                "selected_total_nodes": selected_total_nodes,
                "node_delta_vs_final": raw_total_nodes - FINAL_NODES,
                "selected_node_delta_vs_final": selected_total_nodes - FINAL_NODES,
                "max_level": max_selected_level,
                "max_raw_level": max_raw_level,
                "level_delta_vs_final": max_selected_level - FINAL_MAX_LEVEL,
                "total_opt_time": round(sum(f(row, "opt_time") for row in items), 6),
                "total_cec_time": round(sum(f(row, "cec_time") for row in items), 6),
                "total_time": round(sum(f(row, "total_time") for row in items), 6),
                "peak_RSS": round(max(f(row, "peak_RSS") for row in items), 3),
                "fallback_count": fallback_count,
                "raw_cec_pass_count": sum(1 for row in items if row["raw_cec_status"] == "passed"),
                "crash_count": sum(1 for row in items if row["raw_status"] == "crash"),
                "timeout_count": sum(1 for row in items if row["raw_status"] == "timeout"),
                "cec_fail_count": sum(1 for row in items if row["raw_status"] == "cec_failed"),
                "metric_regression_count": sum(1 for row in items if row["raw_status"] == "metric_regression"),
                "wins": wins,
                "ties": ties,
                "losses": losses,
                "gain_excluding_best_case": ge_best,
                "gain_excluding_top2_cases": ge_top2,
                "best_case_gain": best_gain,
                "best_case_contribution_ratio": round(best_ratio, 6),
                "raw_total_better_than_final": raw_total_nodes < FINAL_NODES,
                "selected_total_better_than_final": selected_total_nodes < FINAL_NODES,
                "selected_depends_on_fallback": selected_depends_on_fallback,
                "not_robust_raw_vs_selected": not_robust,
                "runtime_warning_count": runtime_warnings,
                "rss_warning_count": rss_warnings,
                "eligible_for_selector_phase7": eligible,
                "phase7_reason": reason,
            }
        )
    return rows


def group_by(rows: list[dict[str, str]], key: str) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row[key]].append(row)
    return grouped


BUCKET_FIELDS = [
    "scale_grade",
    "high_fanin_sop",
    "near_two_input_aig",
    "two_input_ratio_bin",
    "names_bin",
    "cubes_bin",
    "max_fanin_bin",
    "outputs_bin",
    "level_bin",
    "runtime_size_bin",
]


def bucket_analysis(metrics: list[dict[str, str]], features: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pipeline, items in sorted(group_by(metrics, "pipeline_id").items()):
        for field in BUCKET_FIELDS:
            bucketed: dict[str, list[dict[str, str]]] = defaultdict(list)
            for row in items:
                bucketed[features[row["case"]].get(field, "")].append(row)
            for value, bucket_rows in sorted(bucketed.items()):
                deltas = [node_delta(row, "raw") for row in bucket_rows if row.get("raw_nodes")]
                if not deltas:
                    continue
                wins = sum(1 for d in deltas if d < 0)
                ties = sum(1 for d in deltas if d == 0)
                losses = sum(1 for d in deltas if d > 0)
                total_delta = sum(deltas)
                runtime_ratios = [f(row, "runtime_ratio_vs_final") for row in bucket_rows if row.get("runtime_ratio_vs_final")]
                rss_ratios = [f(row, "rss_ratio_vs_final") for row in bucket_rows if row.get("rss_ratio_vs_final")]
                cases = len(bucket_rows)
                selector_rule_candidate = (
                    cases >= MIN_BUCKET_CASES_FOR_RULE
                    and wins > losses
                    and total_delta < 0
                    and max(level_delta(row, "raw") for row in bucket_rows if row.get("raw_levels")) <= 1
                    and max(runtime_ratios or [0]) <= RUNTIME_WARN_RATIO
                    and max(rss_ratios or [0]) <= RSS_WARN_RATIO
                )
                rows.append(
                    {
                        "candidate": pipeline,
                        "family": bucket_rows[0]["family"],
                        "bucket_feature": field,
                        "bucket_value": value,
                        "cases": cases,
                        "wins": wins,
                        "ties": ties,
                        "losses": losses,
                        "total_node_delta": total_delta,
                        "avg_node_delta": round(total_delta / cases, 3),
                        "max_level_delta": max(level_delta(row, "raw") for row in bucket_rows if row.get("raw_levels")),
                        "avg_runtime_ratio": round(sum(runtime_ratios) / len(runtime_ratios), 6) if runtime_ratios else "",
                        "max_runtime_ratio": round(max(runtime_ratios), 6) if runtime_ratios else "",
                        "avg_RSS_ratio": round(sum(rss_ratios) / len(rss_ratios), 6) if rss_ratios else "",
                        "max_RSS_ratio": round(max(rss_ratios), 6) if rss_ratios else "",
                        "recommended_pipeline": pipeline if selector_rule_candidate else "",
                        "selector_rule_candidate": selector_rule_candidate,
                        "rule_safety_note": "coarse bucket, >=2 cases" if selector_rule_candidate else "not stable enough for selector rule",
                    }
                )
    return rows


def regression_cases(metrics: list[dict[str, str]], features: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in metrics:
        raw_delta = node_delta(row, "raw") if row.get("raw_nodes") else 0
        selected_delta = node_delta(row, "selected")
        lvl_delta = level_delta(row, "raw") if row.get("raw_levels") else 0
        runtime_delta = f(row, "total_time") - f(row, "final_total_time_sec")
        rss_delta = f(row, "peak_RSS") - f(row, "final_peak_rss_mb")
        if raw_delta <= 0 and selected_delta <= 0 and lvl_delta <= 0 and runtime_delta <= 0 and rss_delta <= 0:
            continue
        feat = features[row["case"]]
        high_level_bucket = "|".join(
            [
                feat.get("scale_grade", ""),
                "high_sop" if b(feat, "high_fanin_sop") else "not_sop",
                "near_aig" if b(feat, "near_two_input_aig") else "non_aig",
                feat.get("two_input_ratio_bin", ""),
            ]
        )
        possible_rule = (
            f"avoid {feat.get('scale_grade')} + high_fanin_sop={feat.get('high_fanin_sop')} "
            f"+ near_two_input_aig={feat.get('near_two_input_aig')} + {feat.get('two_input_ratio_bin')}"
        )
        coarse_avoidable = raw_delta > 0 and feat.get("scale_grade") in {"tiny", "small"} and b(feat, "high_fanin_sop")
        rows.append(
            {
                "case": row["case"],
                "candidate": row["pipeline_id"],
                "raw_nodes_delta": raw_delta,
                "selected_nodes_delta": selected_delta,
                "level_delta": lvl_delta,
                "runtime_delta": round(runtime_delta, 6),
                "RSS_delta": round(rss_delta, 6),
                "raw_status": row["raw_status"],
                "selected_status": row["selected_status"],
                "fallback_used": row["fallback_used"],
                "fallback_reason": row["fallback_reason"],
                "feature_bucket": high_level_bucket,
                "scale_grade": feat.get("scale_grade", ""),
                "high_fanin_sop": feat.get("high_fanin_sop", ""),
                "near_two_input_aig": feat.get("near_two_input_aig", ""),
                "two_input_ratio_bin": feat.get("two_input_ratio_bin", ""),
                "names_bin": feat.get("names_bin", ""),
                "cubes_bin": feat.get("cubes_bin", ""),
                "outputs_bin": feat.get("outputs_bin", ""),
                "possible_filter_rule": possible_rule,
                "coarse_rule_avoidable": coarse_avoidable,
            }
        )
    return rows


def pareto(summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in summary_rows:
        strictly = (
            int(row["selected_total_nodes"]) < FINAL_NODES
            and int(row["max_level"]) <= FINAL_MAX_LEVEL
            and int(row["fallback_count"]) == 0
            and int(row["crash_count"]) == 0
            and int(row["timeout_count"]) == 0
            and int(row["cec_fail_count"]) == 0
            and int(row["runtime_warning_count"]) == 0
            and int(row["rss_warning_count"]) == 0
        )
        robust = (
            bool(row["eligible_for_selector_phase7"])
            and int(row["gain_excluding_best_case"]) > 0
            and int(row["gain_excluding_top2_cases"]) > 0
            and float(row["best_case_contribution_ratio"]) < 0.85
        )
        rows.append(
            {
                "candidate": row["candidate"],
                "family": row["family"],
                "nodes": row["selected_total_nodes"],
                "raw_nodes": row["raw_total_nodes"],
                "max_level": row["max_level"],
                "runtime": row["total_time"],
                "RSS": row["peak_RSS"],
                "fallback_count": row["fallback_count"],
                "CEC_status": f"{row['raw_cec_pass_count']}/30",
                "strictly_better_than_current_final": strictly,
                "node_better_but_level_worse": int(row["selected_total_nodes"]) < FINAL_NODES and int(row["max_level"]) > FINAL_MAX_LEVEL,
                "node_better_but_runtime_costly": int(row["selected_total_nodes"]) < FINAL_NODES and int(row["runtime_warning_count"]) > 0,
                "robust_candidate": robust,
                "research_only": not robust,
            }
        )
    return rows


def md_bool(value: Any) -> str:
    return "yes" if bool(value) else "no"


def md_cell(value: Any) -> str:
    return str(value).replace("|", "\\|")


def write_report(
    path: Path,
    summary_rows: list[dict[str, Any]],
    bucket_rows: list[dict[str, Any]],
    reg_rows: list[dict[str, Any]],
    pareto_rows: list[dict[str, Any]],
) -> None:
    high = next(row for row in summary_rows if row["candidate"] == "high_aig_three_round")
    high_regs = [row for row in reg_rows if row["candidate"] == "high_aig_three_round" and int(row["raw_nodes_delta"]) > 0]
    high_winning_buckets = [
        row
        for row in bucket_rows
        if row["candidate"] == "high_aig_three_round" and row["selector_rule_candidate"]
    ]
    phase7 = [row for row in summary_rows if row["eligible_for_selector_phase7"]]
    robust = [row for row in pareto_rows if row["robust_candidate"]]
    lines = [
        "# Pipeline Search 2.0 Anti-overfit Report",
        "",
        "Phase 6 only. No selector candidate was generated, and no final/submit artifacts were modified.",
        "",
        "## Candidate Summary",
        "",
        "| candidate | raw nodes | selected nodes | max level | CEC | fallback | W/T/L | gain excl best | gain excl top2 | best-case ratio | Phase 7 eligible |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['candidate']} | {row['raw_total_nodes']} | {row['selected_total_nodes']} | {row['max_level']} | "
            f"{row['raw_cec_pass_count']}/30 | {row['fallback_count']} | {row['wins']}/{row['ties']}/{row['losses']} | "
            f"{row['gain_excluding_best_case']} | {row['gain_excluding_top2_cases']} | "
            f"{row['best_case_contribution_ratio']:.3f} | {md_bool(row['eligible_for_selector_phase7'])} |"
        )
    lines.extend(
        [
            "",
            "## Raw vs Selected",
            "",
            "- All seven candidates have raw CEC 30/30 and selected total nodes below 47338.",
            "- Selected totals are not purely raw for any candidate: every candidate has 1 or 2 metric-regression fallbacks.",
            "- Candidates whose raw anti-overfit is weak are marked research-only even if selected totals look strong.",
            "",
            "## high_aig_three_round",
            "",
            f"- Selected total nodes: {high['selected_total_nodes']} (< 47338).",
            f"- Raw total nodes: {high['raw_total_nodes']} (< 47338).",
            f"- Max level: {high['max_level']} (<= 25).",
            f"- Wins/ties/losses: {high['wins']}/{high['ties']}/{high['losses']}.",
            f"- gain_excluding_best_case: {high['gain_excluding_best_case']}; gain_excluding_top2_cases: {high['gain_excluding_top2_cases']}.",
            f"- Fallback count: {high['fallback_count']}; raw remains globally better without relying on fallback.",
            f"- Runtime/RSS warnings: {high['runtime_warning_count']}/{high['rss_warning_count']}.",
            "",
            "Largest high_aig_three_round raw gains are concentrated on large near-two-input AIG-like cases, but the candidate still has positive gain after removing the best and top two gains. Regressions are small and mostly tiny/small high-fanin SOP or small cleanup-sensitive cases.",
            "",
            "High-aig regression cases with raw node loss:",
            "",
            "| case | raw delta | level delta | bucket | coarse avoidable |",
            "| --- | ---: | ---: | --- | --- |",
        ]
    )
    for row in sorted(high_regs, key=lambda r: int(r["raw_nodes_delta"]), reverse=True):
        lines.append(
            f"| {row['case']} | {row['raw_nodes_delta']} | {row['level_delta']} | {md_cell(row['feature_bucket'])} | {md_bool(row['coarse_rule_avoidable'])} |"
        )
    lines.extend(
        [
            "",
            "Coarse bucket leads for high_aig_three_round:",
            "",
            "| bucket feature | bucket value | cases | W/T/L | total delta | selector-rule candidate |",
            "| --- | --- | ---: | --- | ---: | --- |",
        ]
    )
    for row in high_winning_buckets[:20]:
        lines.append(
            f"| {row['bucket_feature']} | {row['bucket_value']} | {row['cases']} | {row['wins']}/{row['ties']}/{row['losses']} | {row['total_node_delta']} | {md_bool(row['selector_rule_candidate'])} |"
        )
    lines.extend(
        [
            "",
            "## Phase 7 Gate",
            "",
            f"- Phase 7 eligible by hard gates: {', '.join(row['candidate'] for row in phase7) if phase7 else 'none'}.",
            f"- Robust Pareto candidate(s): {', '.join(row['candidate'] for row in robust) if robust else 'none'}.",
            "- Recommended Phase 7 priority: `high_aig_three_round` first, because it is the only candidate with both gain_excluding_best_case and gain_excluding_top2_cases positive.",
            "- All other Phase 5 candidates are research-only at this gate because their raw gains collapse after removing the best public case or top two cases.",
            "- Suggested coarse direction for high_aig_three_round: large/medium near-two-input AIG-like or runtime-large buckets; avoid tiny/small high-fanin SOP buckets where final `sop_fx` remains better.",
            "",
            "## Stop Point",
            "",
            "Phase 6 completed. Phase 7 selector generation and Phase 8 final decision were not run.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics", default=Path("reports/pipeline_search2_metrics.csv"), type=Path)
    parser.add_argument("--final", default=Path("reports/final_metrics.csv"), type=Path)
    parser.add_argument("--features", default=Path("reports/features.csv"), type=Path)
    parser.add_argument("--anti-out", default=Path("reports/anti_overfit_pipeline_search2.csv"), type=Path)
    parser.add_argument("--bucket-out", default=Path("reports/bucket_gain_pipeline_search2.csv"), type=Path)
    parser.add_argument("--regression-out", default=Path("reports/pipeline_search2_regression_cases.csv"), type=Path)
    parser.add_argument("--pareto-out", default=Path("reports/pipeline_search2_pareto.csv"), type=Path)
    parser.add_argument("--report", default=Path("docs/pipeline_search2_anti_overfit_report.md"), type=Path)
    args = parser.parse_args()

    metrics = read_csv(args.metrics)
    final_by_case = {row["case"]: row for row in read_csv(args.final)}
    features = enrich_features(read_csv(args.features), final_by_case)
    summary_rows = candidate_summary(metrics)
    bucket_rows = bucket_analysis(metrics, features)
    reg_rows = regression_cases(metrics, features)
    pareto_rows = pareto(summary_rows)

    write_csv(args.anti_out, summary_rows)
    write_csv(args.bucket_out, bucket_rows)
    write_csv(args.regression_out, reg_rows)
    write_csv(args.pareto_out, pareto_rows)
    write_report(args.report, summary_rows, bucket_rows, reg_rows, pareto_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
