#!/usr/bin/env python3
"""Run Pipeline Search 2.0 smoke candidates on the fixed smoke subset."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from run_abc_case import collect_stats, metric_tuple, run_cec, run_optimization


SMOKE_USAGE_NOTE = "SMOKE_ONLY_FILTER_NOT_FINAL_CONCLUSION"
DISABLED_COMMANDS = {"compress2rs"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def num(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def int_or_blank(value: Any) -> int | str:
    if value in (None, ""):
        return ""
    return int(float(value))


def timeout_profile(config: dict[str, Any], name: str, scale: str) -> tuple[float, float, float, str]:
    profiles = config.get("timeout_profiles", {})
    profile = profiles.get(name) or profiles.get("default") or {}
    opt_by_scale = profile.get("opt_timeout_sec_by_scale", {})
    opt = float(opt_by_scale.get(scale, opt_by_scale.get("medium", 120)))
    cec = float(profile.get("cec_timeout_sec", 300))
    stats = float(profile.get("stats_timeout_sec", 120))
    return opt, cec, stats, json.dumps(profile, sort_keys=True)


def load_inventory(path: Path) -> dict[str, dict[str, str]]:
    return {row["command"]: row for row in read_csv(path)}


def inventory_enabled(inventory: dict[str, dict[str, str]], command: str) -> bool:
    row = inventory.get(command)
    return bool(row) and row.get("generation_status") == "enabled"


def has_disabled_command(candidate: dict[str, str], inventory: dict[str, dict[str, str]]) -> str:
    steps = candidate.get("normalized_steps", "")
    requires = set(filter(None, candidate.get("requires_tokens", "").split("|")))
    if "compress2rs" in steps or "compress2rs" in requires:
        return "compress2rs disabled by smoke policy"
    if ("mfs2" in steps or "mfs2" in requires) and not inventory_enabled(inventory, "mfs2"):
        return "mfs2 disabled because inventory does not mark it enabled"
    for command in DISABLED_COMMANDS:
        if command in requires:
            return f"{command} disabled by smoke policy"
    return ""


def cache_key(
    normalized_steps: str,
    input_sha: str,
    abc_sha: str,
    runner_sha: str,
    stats_parser_sha: str,
    timeout_profile_name: str,
    timeout_profile_payload: str,
) -> str:
    payload = {
        "normalized_pipeline_steps": normalized_steps,
        "input_blif_sha256": input_sha,
        "abc_binary_sha256": abc_sha,
        "runner_script_hash_or_version": runner_sha,
        "stats_parser_hash_or_version": stats_parser_sha,
        "timeout_profile": timeout_profile_name,
        "timeout_profile_payload": timeout_profile_payload,
    }
    return sha256_text(json.dumps(payload, sort_keys=True))


def final_total_time(row: dict[str, str]) -> float:
    return num(row.get("opt_runtime_sec")) + num(row.get("cec_runtime_sec")) + num(row.get("stats_runtime_sec"))


def regression_reasons(
    raw_nodes: int,
    raw_levels: int,
    raw_total_time: float,
    raw_peak_rss: float,
    final_row: dict[str, str],
    policy: dict[str, Any],
) -> list[str]:
    reasons: list[str] = []
    final_nodes = int_or_blank(final_row.get("selected_nodes"))
    final_levels = int_or_blank(final_row.get("selected_levels"))
    final_time = final_total_time(final_row)
    final_rss = num(final_row.get("peak_mem_mb"))

    if isinstance(final_nodes, int):
        node_delta = raw_nodes - final_nodes
        ratio_limit = float(policy.get("raw_nodes_ratio_max_vs_final", 1.03))
        abs_limit = int(policy.get("raw_nodes_abs_worse_min", 25))
        if raw_nodes > final_nodes * ratio_limit and node_delta >= abs_limit:
            reasons.append(f"nodes_worse:{node_delta}")
    if isinstance(final_levels, int):
        level_delta = raw_levels - final_levels
        if level_delta > int(policy.get("raw_level_delta_max_vs_final", 2)):
            reasons.append(f"levels_worse:{level_delta}")
    if final_time > 0 and raw_total_time / final_time > float(policy.get("raw_runtime_ratio_max_vs_final", 2.5)):
        reasons.append(f"runtime_ratio:{raw_total_time / final_time:.3f}")
    if final_rss > 0 and raw_peak_rss / final_rss > float(policy.get("raw_rss_ratio_max_vs_final", 2.0)):
        reasons.append(f"rss_ratio:{raw_peak_rss / final_rss:.3f}")
    return reasons


def base_row(candidate: dict[str, str], subset: dict[str, str], final_row: dict[str, str], cache: str) -> dict[str, Any]:
    return {
        "phase": "smoke",
        "usage_note": SMOKE_USAGE_NOTE,
        "family": candidate.get("family", ""),
        "pipeline_id": candidate.get("pipeline_id", ""),
        "pipeline_hash": candidate.get("pipeline_hash", ""),
        "candidate_kind": candidate.get("candidate_kind", ""),
        "selector_eligible": candidate.get("selector_eligible", ""),
        "offline_only": candidate.get("offline_only", ""),
        "raw_steps": candidate.get("raw_steps", ""),
        "normalized_steps": candidate.get("normalized_steps", ""),
        "timeout_profile": candidate.get("timeout_profile", ""),
        "allowed_case_scales": candidate.get("allowed_case_scales", ""),
        "case": subset.get("case", ""),
        "selection_order": subset.get("selection_order", ""),
        "selection_reason": subset.get("selection_reason", ""),
        "selector_bucket": subset.get("selector_bucket", ""),
        "scale_grade": subset.get("scale_grade", ""),
        "final_nodes": final_row.get("selected_nodes", ""),
        "final_levels": final_row.get("selected_levels", ""),
        "final_total_time_sec": f"{final_total_time(final_row):.6f}",
        "final_peak_rss_mb": final_row.get("peak_mem_mb", ""),
        "raw_nodes": "",
        "raw_levels": "",
        "raw_cec_status": "not_run",
        "raw_status": "not_run",
        "selected_nodes": final_row.get("selected_nodes", ""),
        "selected_levels": final_row.get("selected_levels", ""),
        "selected_status": "fallback_current_final",
        "fallback_used": "true",
        "fallback_reason": "not_run",
        "metric_regression": "false",
        "metric_regression_reasons": "",
        "raw_node_delta_vs_final": "",
        "raw_level_delta_vs_final": "",
        "opt_runtime_sec": "0.000000",
        "cec_runtime_sec": "0.000000",
        "stats_runtime_sec": "0.000000",
        "total_runtime_sec": "0.000000",
        "peak_rss_mb": "0.000",
        "runtime_ratio_vs_final": "",
        "rss_ratio_vs_final": "",
        "opt_returncode": "",
        "cec_returncode": "",
        "output_path": "",
        "candidate_path": "",
        "log_dir": "",
        "cache_key": cache,
    }


def run_one(
    abc: Path,
    cases_dir: Path,
    out_dir: Path,
    candidate: dict[str, str],
    subset: dict[str, str],
    final_row: dict[str, str],
    config: dict[str, Any],
    inventory: dict[str, dict[str, str]],
    abc_sha: str,
    runner_sha: str,
    stats_parser_sha: str,
) -> dict[str, Any]:
    case = subset["case"]
    input_blif = cases_dir / case / "input.blif"
    scale = subset.get("scale_grade", "")
    opt_timeout, cec_timeout, stats_timeout, profile_payload = timeout_profile(
        config, candidate.get("timeout_profile", "default"), scale
    )
    input_sha = sha256_file(input_blif)
    key = cache_key(
        candidate.get("normalized_steps", ""),
        input_sha,
        abc_sha,
        runner_sha,
        stats_parser_sha,
        candidate.get("timeout_profile", "default"),
        profile_payload,
    )
    cache_path = out_dir / "cache" / f"{key}.json"
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))

    row = base_row(candidate, subset, final_row, key)
    allowed_scales = set(filter(None, candidate.get("allowed_case_scales", "").split("|")))
    if allowed_scales and scale not in allowed_scales:
        row["raw_status"] = "skipped_case_scale"
        row["selected_status"] = "fallback_current_final"
        row["fallback_reason"] = "case scale blocked by candidate timeout guard"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8")
        return row

    disabled_reason = has_disabled_command(candidate, inventory)
    if disabled_reason:
        row["raw_status"] = "skipped_disabled_command"
        row["fallback_reason"] = disabled_reason
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8")
        return row

    if opt_timeout <= 0:
        row["raw_status"] = "skipped_case_scale"
        row["fallback_reason"] = "timeout profile blocks this case scale"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8")
        return row

    case_dir = out_dir / candidate["pipeline_id"] / case
    log_dir = case_dir / "logs"
    candidate_path = case_dir / "raw.candidate.blif"
    selected_path = case_dir / "selected.blif"
    row["candidate_path"] = str(candidate_path)
    row["output_path"] = str(selected_path)
    row["log_dir"] = str(log_dir)

    opt = run_optimization(
        abc,
        input_blif,
        candidate_path,
        candidate.get("normalized_steps", ""),
        opt_timeout,
        log_dir / "raw_opt.log",
    )
    row["opt_runtime_sec"] = f"{opt.runtime_sec:.6f}"
    row["opt_returncode"] = opt.returncode
    peak_rss = opt.peak_mem_mb
    if opt.timed_out:
        row["raw_status"] = "timeout"
        row["fallback_reason"] = "opt_timeout"
    elif opt.returncode != 0 or not candidate_path.exists():
        row["raw_status"] = "crash"
        row["fallback_reason"] = "opt_crash_or_missing_output"
    else:
        cec_pass, cec = run_cec(abc, input_blif, candidate_path, cec_timeout, log_dir / "raw_cec.log")
        row["cec_runtime_sec"] = f"{cec.runtime_sec:.6f}"
        row["cec_returncode"] = cec.returncode
        peak_rss = max(peak_rss, cec.peak_mem_mb)
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
            metrics, stats = collect_stats(abc, candidate_path, stats_timeout, log_dir / "raw_stats.log")
            row["stats_runtime_sec"] = f"{stats.runtime_sec:.6f}"
            peak_rss = max(peak_rss, stats.peak_mem_mb)
            raw_nodes, raw_levels = metric_tuple(metrics)
            if raw_nodes is None or raw_levels is None:
                row["raw_status"] = "stats_failed"
                row["fallback_reason"] = "stats_failed"
            else:
                row["raw_nodes"] = raw_nodes
                row["raw_levels"] = raw_levels
                final_nodes = int(final_row["selected_nodes"])
                final_levels = int(final_row["selected_levels"])
                row["raw_node_delta_vs_final"] = raw_nodes - final_nodes
                row["raw_level_delta_vs_final"] = raw_levels - final_levels
                raw_total = opt.runtime_sec + cec.runtime_sec + stats.runtime_sec
                reasons = regression_reasons(raw_nodes, raw_levels, raw_total, peak_rss, final_row, config["metric_regression_policy"])
                if reasons:
                    row["raw_status"] = "metric_regression"
                    row["metric_regression"] = "true"
                    row["metric_regression_reasons"] = "; ".join(reasons)
                    row["fallback_reason"] = "metric_regression: " + "; ".join(reasons)
                else:
                    row["raw_status"] = "ok"
                    row["selected_nodes"] = raw_nodes
                    row["selected_levels"] = raw_levels
                    row["selected_status"] = "selected_raw"
                    row["fallback_used"] = "false"
                    row["fallback_reason"] = ""

    total_time = num(row["opt_runtime_sec"]) + num(row["cec_runtime_sec"]) + num(row["stats_runtime_sec"])
    row["total_runtime_sec"] = f"{total_time:.6f}"
    row["peak_rss_mb"] = f"{peak_rss:.3f}"
    final_time = final_total_time(final_row)
    final_rss = num(final_row.get("peak_mem_mb"))
    if final_time > 0:
        row["runtime_ratio_vs_final"] = f"{total_time / final_time:.6f}"
    if final_rss > 0:
        row["rss_ratio_vs_final"] = f"{peak_rss / final_rss:.6f}"

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8")
    return row


METRIC_FIELDS = [
    "phase",
    "usage_note",
    "family",
    "pipeline_id",
    "pipeline_hash",
    "candidate_kind",
    "selector_eligible",
    "offline_only",
    "raw_steps",
    "normalized_steps",
    "timeout_profile",
    "allowed_case_scales",
    "case",
    "selection_order",
    "selection_reason",
    "selector_bucket",
    "scale_grade",
    "final_nodes",
    "final_levels",
    "final_total_time_sec",
    "final_peak_rss_mb",
    "raw_nodes",
    "raw_levels",
    "raw_cec_status",
    "raw_status",
    "selected_nodes",
    "selected_levels",
    "selected_status",
    "fallback_used",
    "fallback_reason",
    "metric_regression",
    "metric_regression_reasons",
    "raw_node_delta_vs_final",
    "raw_level_delta_vs_final",
    "opt_runtime_sec",
    "cec_runtime_sec",
    "stats_runtime_sec",
    "total_runtime_sec",
    "peak_rss_mb",
    "runtime_ratio_vs_final",
    "rss_ratio_vs_final",
    "opt_returncode",
    "cec_returncode",
    "output_path",
    "candidate_path",
    "log_dir",
    "cache_key",
]


def summarize(metrics_path: Path, recommended_path: Path, summary_path: Path, config: dict[str, Any]) -> None:
    if not metrics_path.exists():
        return
    rows = read_csv(metrics_path)
    if not rows:
        return
    runtime_limit = float(config["metric_regression_policy"].get("raw_runtime_ratio_max_vs_final", 2.5))
    rss_limit = float(config["metric_regression_policy"].get("raw_rss_ratio_max_vs_final", 2.0))

    by_candidate: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in rows:
        by_candidate.setdefault((row["family"], row["pipeline_id"]), []).append(row)

    candidate_summary: list[dict[str, Any]] = []
    for (family, pipeline_id), items in sorted(by_candidate.items()):
        attempted = [r for r in items if not r["raw_status"].startswith("skipped")]
        passed = [r for r in attempted if r["raw_cec_status"] == "passed"]
        failures = [r for r in attempted if r["raw_status"] in {"crash", "timeout", "cec_failed", "stats_failed"}]
        deltas = [num(r["raw_node_delta_vs_final"]) for r in passed if r["raw_node_delta_vs_final"] != ""]
        total_delta = sum(deltas)
        avg_delta = total_delta / len(deltas) if deltas else 0.0
        wins = sum(1 for r in passed if r["raw_node_delta_vs_final"] != "" and num(r["raw_node_delta_vs_final"]) < 0)
        ties = sum(1 for r in passed if r["raw_node_delta_vs_final"] != "" and num(r["raw_node_delta_vs_final"]) == 0)
        losses = sum(1 for r in passed if r["raw_node_delta_vs_final"] != "" and num(r["raw_node_delta_vs_final"]) > 0)
        level_regressions = sum(1 for r in passed if r["raw_level_delta_vs_final"] != "" and num(r["raw_level_delta_vs_final"]) > 0)
        runtime_warnings = sum(1 for r in attempted if r["runtime_ratio_vs_final"] and num(r["runtime_ratio_vs_final"]) > runtime_limit)
        rss_warnings = sum(1 for r in attempted if r["rss_ratio_vs_final"] and num(r["rss_ratio_vs_final"]) > rss_limit)
        metric_regressions = sum(1 for r in attempted if as_bool(r["metric_regression"]))
        if failures:
            recommendation = "eliminate_candidate"
            reason = "raw failure observed"
        elif not attempted:
            recommendation = "eliminate_candidate"
            reason = "no attempted smoke case"
        elif avg_delta <= 0 and runtime_warnings == 0 and rss_warnings == 0:
            recommendation = "full_search_recommended"
            reason = "non-worse average smoke delta with no cost warning"
        elif wins > 0 and avg_delta <= 50 and runtime_warnings == 0 and rss_warnings == 0:
            recommendation = "full_search_review"
            reason = "has smoke win without high cost warning"
        else:
            recommendation = "eliminate_candidate"
            reason = "smoke worse or high cost"

        first = items[0]
        candidate_summary.append(
            {
                "usage_note": SMOKE_USAGE_NOTE,
                "family": family,
                "pipeline_id": pipeline_id,
                "pipeline_hash": first["pipeline_hash"],
                "selector_eligible": first["selector_eligible"],
                "offline_only": first["offline_only"],
                "timeout_profile": first["timeout_profile"],
                "allowed_case_scales": first["allowed_case_scales"],
                "normalized_steps": first["normalized_steps"],
                "smoke_rows": len(items),
                "smoke_attempted_cases": len(attempted),
                "smoke_skipped_cases": len(items) - len(attempted),
                "smoke_passed_cases": len(passed),
                "crash_count": sum(1 for r in attempted if r["raw_status"] == "crash"),
                "timeout_count": sum(1 for r in attempted if r["raw_status"] == "timeout"),
                "cec_fail_count": sum(1 for r in attempted if r["raw_status"] == "cec_failed"),
                "metric_regression_count": metric_regressions,
                "total_node_delta_vs_final": f"{total_delta:.0f}",
                "avg_node_delta_vs_final": f"{avg_delta:.3f}",
                "wins": wins,
                "ties": ties,
                "losses": losses,
                "level_regression_count": level_regressions,
                "runtime_warning_count": runtime_warnings,
                "rss_warning_count": rss_warnings,
                "recommendation": recommendation,
                "recommendation_reason": reason,
            }
        )

    recommended = [
        row
        for row in candidate_summary
        if row["recommendation"] in {"full_search_recommended", "full_search_review"}
    ]
    rec_fields = list(candidate_summary[0].keys()) if candidate_summary else []
    write_csv(recommended_path, recommended, rec_fields)

    family_rows: list[dict[str, Any]] = []
    for family in sorted({row["family"] for row in candidate_summary}):
        items = [row for row in candidate_summary if row["family"] == family]
        attempted_candidates = sum(1 for row in items if int(row["smoke_attempted_cases"]) > 0)
        passed_candidates = sum(
            1
            for row in items
            if int(row["smoke_attempted_cases"]) > 0
            and int(row["crash_count"]) == 0
            and int(row["timeout_count"]) == 0
            and int(row["cec_fail_count"]) == 0
        )
        total_attempted_rows = sum(int(row["smoke_attempted_cases"]) for row in items)
        total_delta = sum(float(row["total_node_delta_vs_final"]) for row in items)
        avg_delta = total_delta / total_attempted_rows if total_attempted_rows else 0.0
        recommended_count = sum(
            1 for row in items if row["recommendation"] in {"full_search_recommended", "full_search_review"}
        )
        family_rows.append(
            {
                "family": family,
                "attempted_candidates": attempted_candidates,
                "passed_candidates": passed_candidates,
                "crash_count": sum(int(row["crash_count"]) for row in items),
                "timeout_count": sum(int(row["timeout_count"]) for row in items),
                "cec_fail_count": sum(int(row["cec_fail_count"]) for row in items),
                "avg_node_delta_vs_final": avg_delta,
                "level_regression_count": sum(int(row["level_regression_count"]) for row in items),
                "runtime_warning_count": sum(int(row["runtime_warning_count"]) for row in items),
                "rss_warning_count": sum(int(row["rss_warning_count"]) for row in items),
                "recommended_candidates": recommended_count,
                "family_action": "keep_for_full_candidates" if recommended_count else "eliminate_for_full_search",
            }
        )

    lines = [
        "# Smoke Search 2 Summary",
        "",
        f"Usage note: `{SMOKE_USAGE_NOTE}`. These data are only for eliminating unsafe or clearly weak candidates; they are not final performance conclusions.",
        "",
        "## Family Summary",
        "",
        "| family | attempted candidates | passed candidates | crash | timeout | CEC fail | avg node delta vs final | level regressions | runtime warnings | RSS warnings | recommended | action |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in family_rows:
        lines.append(
            f"| {row['family']} | {row['attempted_candidates']} | {row['passed_candidates']} | "
            f"{row['crash_count']} | {row['timeout_count']} | {row['cec_fail_count']} | "
            f"{row['avg_node_delta_vs_final']:.3f} | {row['level_regression_count']} | "
            f"{row['runtime_warning_count']} | {row['rss_warning_count']} | {row['recommended_candidates']} | {row['family_action']} |"
        )

    lines.extend(
        [
            "",
            "## Recommended Full Candidates",
            "",
            "| family | pipeline | avg node delta | wins/ties/losses | level regressions | recommendation |",
            "| --- | --- | ---: | --- | ---: | --- |",
        ]
    )
    for row in recommended:
        lines.append(
            f"| {row['family']} | {row['pipeline_id']} | {row['avg_node_delta_vs_final']} | "
            f"{row['wins']}/{row['ties']}/{row['losses']} | {row['level_regression_count']} | {row['recommendation']} |"
        )
    if not recommended:
        lines.append("| none | none |  |  |  | none |")

    lines.extend(
        [
            "",
            "## Eliminated Commands",
            "",
            "- `compress2rs`: disabled by capability inventory as unavailable.",
            "- `mfs2`: disabled by capability inventory because the probe crashed.",
            "",
            "## Stop Point",
            "",
            "Phase 4 completed. Phase 5 full search has not been run.",
        ]
    )
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--space", required=True, type=Path)
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--subset", required=True, type=Path)
    parser.add_argument("--final", required=True, type=Path)
    parser.add_argument("--inventory", required=True, type=Path)
    parser.add_argument("--cases", required=True, type=Path)
    parser.add_argument("--abc", required=True, type=Path)
    parser.add_argument("--out-dir", default=Path("results/pipeline_search2/smoke"), type=Path)
    parser.add_argument("--metrics", default=Path("reports/smoke_search2_metrics.csv"), type=Path)
    parser.add_argument("--summary", default=Path("reports/smoke_search2_summary.md"), type=Path)
    parser.add_argument("--recommended", default=Path("results/pipeline_search2/candidates_full_recommended.csv"), type=Path)
    parser.add_argument("--family")
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    config = yaml.safe_load(args.space.read_text(encoding="utf-8")) or {}
    candidates = [row for row in read_csv(args.candidates) if as_bool(row.get("run_eligible"))]
    if args.family:
        candidates = [row for row in candidates if row.get("family") == args.family]
    subset = read_csv(args.subset)
    final = {row["case"]: row for row in read_csv(args.final)}
    inventory = load_inventory(args.inventory)

    if args.reset and args.metrics.exists():
        args.metrics.unlink()
    existing: list[dict[str, Any]] = []
    existing_keys: set[tuple[str, str]] = set()
    if args.metrics.exists():
        existing = read_csv(args.metrics)
        existing_keys = {(row["pipeline_id"], row["case"]) for row in existing}

    abc_sha = sha256_file(args.abc)
    runner_sha = sha256_file(Path(__file__))
    stats_parser_sha = sha256_file(Path(__file__).with_name("parse_abc_stats.py"))

    new_rows: list[dict[str, Any]] = []
    for candidate in candidates:
        for case_row in subset:
            key = (candidate["pipeline_id"], case_row["case"])
            if key in existing_keys:
                continue
            print(f"[smoke][{candidate['family']}][{candidate['pipeline_id']}][{case_row['case']}]")
            new_rows.append(
                run_one(
                    args.abc,
                    args.cases,
                    args.out_dir,
                    candidate,
                    case_row,
                    final[case_row["case"]],
                    config,
                    inventory,
                    abc_sha,
                    runner_sha,
                    stats_parser_sha,
                )
            )

    all_rows = existing + new_rows
    write_csv(args.metrics, all_rows, METRIC_FIELDS)
    summarize(args.metrics, args.recommended, args.summary, config)
    print(f"wrote {args.metrics}")
    print(f"wrote {args.summary}")
    print(f"wrote {args.recommended}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
