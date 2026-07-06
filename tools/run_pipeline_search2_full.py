#!/usr/bin/env python3
"""Run Pipeline Search 2.0 full search on approved candidates only."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from run_abc_case import collect_stats, metric_tuple, run_cec, run_optimization


USAGE_NOTE = "FULL_SEARCH_PHASE5_NOT_FINAL_DECISION"
APPROVED_PIPELINES = {
    "aig_resyn_resub_zero",
    "dc2_fraig_cleanup",
    "dc2_ifraig_cleanup",
    "choice_fraig_clean",
    "choice_ifraig_clean",
    "choice_fraig_ifraig_recover",
    "high_aig_three_round",
}
FORBIDDEN_TOKENS = {"compress2rs", "mfs2"}


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


def final_total_time(row: dict[str, str]) -> float:
    return num(row.get("opt_runtime_sec")) + num(row.get("cec_runtime_sec")) + num(row.get("stats_runtime_sec"))


def timeout_profile(config: dict[str, Any], name: str, scale: str) -> tuple[float, float, float, str, str]:
    profiles = config.get("timeout_profiles", {})
    profile = profiles.get(name) or profiles.get("default") or {}
    default_profile = profiles.get("default") or {}
    opt_by_scale = profile.get("opt_timeout_sec_by_scale", {})
    opt = float(opt_by_scale.get(scale, opt_by_scale.get("medium", 120)))
    override = ""
    if opt <= 0:
        default_by_scale = default_profile.get("opt_timeout_sec_by_scale", {})
        opt = float(default_by_scale.get(scale, default_by_scale.get("large", 240)))
        override = f"phase5_full_run_override_for_{scale}"
    cec = float(profile.get("cec_timeout_sec", default_profile.get("cec_timeout_sec", 300)))
    stats = float(profile.get("stats_timeout_sec", default_profile.get("stats_timeout_sec", 120)))
    return opt, cec, stats, json.dumps(profile, sort_keys=True), override


def load_inventory(path: Path) -> dict[str, dict[str, str]]:
    return {row["command"]: row for row in read_csv(path)}


def inventory_enabled(inventory: dict[str, dict[str, str]], command: str) -> bool:
    row = inventory.get(command)
    return bool(row) and row.get("generation_status") == "enabled"


def disabled_reason(candidate: dict[str, str], inventory: dict[str, dict[str, str]]) -> str:
    steps = candidate.get("normalized_steps", "")
    for token in FORBIDDEN_TOKENS:
        if token in steps:
            if token == "mfs2" and inventory_enabled(inventory, "mfs2"):
                continue
            return f"forbidden token in full search candidate: {token}"
    if candidate.get("pipeline_id") not in APPROVED_PIPELINES:
        return "not in approved Phase 5 candidate allowlist"
    if "oracle" in candidate.get("pipeline_id", "").lower() or as_bool(candidate.get("oracle_only", "")):
        return "oracle candidates are forbidden in Phase 5"
    return ""


def cache_key(
    normalized_steps: str,
    input_sha: str,
    abc_sha: str,
    runner_sha: str,
    stats_parser_sha: str,
    timeout_profile_name: str,
    timeout_payload: str,
) -> str:
    payload = {
        "normalized_pipeline_steps": normalized_steps,
        "input_blif_sha256": input_sha,
        "abc_binary_sha256": abc_sha,
        "runner_script_hash_or_version": runner_sha,
        "stats_parser_hash_or_version": stats_parser_sha,
        "timeout_profile": timeout_profile_name,
        "timeout_profile_payload": timeout_payload,
    }
    return sha256_text(json.dumps(payload, sort_keys=True))


def regression_reasons(
    raw_nodes: int,
    raw_levels: int,
    raw_total_time: float,
    raw_peak_rss: float,
    final_row: dict[str, str],
    policy: dict[str, Any],
) -> list[str]:
    reasons: list[str] = []
    final_nodes = int(float(final_row.get("selected_nodes", "0") or 0))
    final_levels = int(float(final_row.get("selected_levels", "0") or 0))
    final_time = final_total_time(final_row)
    final_rss = num(final_row.get("peak_mem_mb"))
    node_delta = raw_nodes - final_nodes
    if raw_nodes > final_nodes * float(policy.get("raw_nodes_ratio_max_vs_final", 1.03)) and node_delta >= int(
        policy.get("raw_nodes_abs_worse_min", 25)
    ):
        reasons.append(f"nodes_worse:{node_delta}")
    level_delta = raw_levels - final_levels
    if level_delta > int(policy.get("raw_level_delta_max_vs_final", 2)):
        reasons.append(f"levels_worse:{level_delta}")
    if final_time > 0 and raw_total_time / final_time > float(policy.get("raw_runtime_ratio_max_vs_final", 2.5)):
        reasons.append(f"runtime_ratio:{raw_total_time / final_time:.3f}")
    if final_rss > 0 and raw_peak_rss / final_rss > float(policy.get("raw_rss_ratio_max_vs_final", 2.0)):
        reasons.append(f"rss_ratio:{raw_peak_rss / final_rss:.3f}")
    return reasons


FIELDS = [
    "phase",
    "usage_note",
    "family",
    "pipeline_id",
    "pipeline_hash",
    "selector_eligible",
    "offline_only",
    "normalized_steps",
    "timeout_profile",
    "timeout_profile_override",
    "case",
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
    "selected_node_delta_vs_final",
    "selected_level_delta_vs_final",
    "opt_time",
    "cec_time",
    "stats_time",
    "total_time",
    "peak_RSS",
    "runtime_ratio_vs_final",
    "rss_ratio_vs_final",
    "opt_returncode",
    "cec_returncode",
    "output_path",
    "candidate_path",
    "log_dir",
    "cache_key",
]


def base_row(candidate: dict[str, str], case: str, scale: str, final_row: dict[str, str], cache: str, override: str) -> dict[str, Any]:
    return {
        "phase": "full",
        "usage_note": USAGE_NOTE,
        "family": candidate.get("family", ""),
        "pipeline_id": candidate.get("pipeline_id", ""),
        "pipeline_hash": candidate.get("pipeline_hash", ""),
        "selector_eligible": candidate.get("selector_eligible", ""),
        "offline_only": candidate.get("offline_only", ""),
        "normalized_steps": candidate.get("normalized_steps", ""),
        "timeout_profile": candidate.get("timeout_profile", ""),
        "timeout_profile_override": override,
        "case": case,
        "scale_grade": scale,
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
    case: str,
    scale: str,
    final_row: dict[str, str],
    config: dict[str, Any],
    inventory: dict[str, dict[str, str]],
    abc_sha: str,
    runner_sha: str,
    stats_parser_sha: str,
) -> dict[str, Any]:
    input_blif = cases_dir / case / "input.blif"
    opt_timeout, cec_timeout, stats_timeout, profile_payload, override = timeout_profile(
        config, candidate.get("timeout_profile", "default"), scale
    )
    key = cache_key(
        candidate.get("normalized_steps", ""),
        sha256_file(input_blif),
        abc_sha,
        runner_sha,
        stats_parser_sha,
        candidate.get("timeout_profile", "default"),
        profile_payload + override,
    )
    cache_path = out_dir / "cache" / f"{key}.json"
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))

    row = base_row(candidate, case, scale, final_row, key, override)
    reason = disabled_reason(candidate, inventory)
    if reason:
        row["raw_status"] = "skipped_disabled_candidate"
        row["fallback_reason"] = reason
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
    row["opt_time"] = f"{opt.runtime_sec:.6f}"
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
        row["cec_time"] = f"{cec.runtime_sec:.6f}"
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
            row["stats_time"] = f"{stats.runtime_sec:.6f}"
            peak_rss = max(peak_rss, stats.peak_mem_mb)
            raw_nodes, raw_levels = metric_tuple(metrics)
            if raw_nodes is None or raw_levels is None:
                row["raw_status"] = "stats_failed"
                row["fallback_reason"] = "stats_failed"
            else:
                final_nodes = int(float(final_row["selected_nodes"]))
                final_levels = int(float(final_row["selected_levels"]))
                row["raw_nodes"] = raw_nodes
                row["raw_levels"] = raw_levels
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

    selected_nodes = int(float(row["selected_nodes"] or final_row["selected_nodes"]))
    selected_levels = int(float(row["selected_levels"] or final_row["selected_levels"]))
    row["selected_node_delta_vs_final"] = selected_nodes - int(float(final_row["selected_nodes"]))
    row["selected_level_delta_vs_final"] = selected_levels - int(float(final_row["selected_levels"]))
    total_time = num(row["opt_time"]) + num(row["cec_time"]) + num(row["stats_time"])
    row["total_time"] = f"{total_time:.6f}"
    row["peak_RSS"] = f"{peak_rss:.3f}"
    final_time = final_total_time(final_row)
    final_rss = num(final_row.get("peak_mem_mb"))
    if final_time > 0:
        row["runtime_ratio_vs_final"] = f"{total_time / final_time:.6f}"
    if final_rss > 0:
        row["rss_ratio_vs_final"] = f"{peak_rss / final_rss:.6f}"

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8")
    return row


def summarize(metrics: Path, summary: Path) -> list[dict[str, Any]]:
    rows = read_csv(metrics)
    by_candidate: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_candidate.setdefault(row["pipeline_id"], []).append(row)
    summary_rows: list[dict[str, Any]] = []
    for pipeline_id, items in sorted(by_candidate.items()):
        selected_nodes = sum(int(float(r["selected_nodes"] or 0)) for r in items)
        raw_nodes_values = [int(float(r["raw_nodes"])) for r in items if r["raw_nodes"] != ""]
        raw_nodes_total = sum(raw_nodes_values) if len(raw_nodes_values) == len(items) else ""
        selected_levels = [int(float(r["selected_levels"] or 0)) for r in items]
        raw_levels = [int(float(r["raw_levels"])) for r in items if r["raw_levels"] != ""]
        raw_delta_by_case = sorted(
            [int(float(r["raw_node_delta_vs_final"])) for r in items if r["raw_node_delta_vs_final"] != ""]
        )
        total_gain = -sum(raw_delta_by_case)
        gain_excluding_best = total_gain + raw_delta_by_case[0] if raw_delta_by_case else ""
        gain_excluding_top2 = total_gain + sum(raw_delta_by_case[:2]) if len(raw_delta_by_case) >= 2 else ""
        wins = sum(1 for r in items if r["raw_node_delta_vs_final"] != "" and float(r["raw_node_delta_vs_final"]) < 0)
        ties = sum(1 for r in items if r["raw_node_delta_vs_final"] != "" and float(r["raw_node_delta_vs_final"]) == 0)
        losses = sum(1 for r in items if r["raw_node_delta_vs_final"] != "" and float(r["raw_node_delta_vs_final"]) > 0)
        runtime_warnings = sum(1 for r in items if r["runtime_ratio_vs_final"] and float(r["runtime_ratio_vs_final"]) > 2.5)
        rss_warnings = sum(1 for r in items if r["rss_ratio_vs_final"] and float(r["rss_ratio_vs_final"]) > 2.0)
        summary_rows.append(
            {
                "pipeline_id": pipeline_id,
                "family": items[0]["family"],
                "cases": len(items),
                "raw_cec_passed": sum(1 for r in items if r["raw_cec_status"] == "passed"),
                "selected_total_nodes": selected_nodes,
                "raw_total_nodes": raw_nodes_total,
                "max_selected_level": max(selected_levels) if selected_levels else "",
                "max_raw_level": max(raw_levels) if raw_levels else "",
                "fallback_count": sum(1 for r in items if as_bool(r["fallback_used"])),
                "crash_count": sum(1 for r in items if r["raw_status"] == "crash"),
                "timeout_count": sum(1 for r in items if r["raw_status"] == "timeout"),
                "cec_fail_count": sum(1 for r in items if r["raw_status"] == "cec_failed"),
                "metric_regression_count": sum(1 for r in items if r["raw_status"] == "metric_regression"),
                "wins": wins,
                "ties": ties,
                "losses": losses,
                "raw_gain_vs_final": total_gain,
                "gain_excluding_best_case": gain_excluding_best,
                "gain_excluding_top2_cases": gain_excluding_top2,
                "total_time": sum(float(r["total_time"] or 0) for r in items),
                "peak_RSS": max(float(r["peak_RSS"] or 0) for r in items),
                "runtime_warning_count": runtime_warnings,
                "rss_warning_count": rss_warnings,
                "beats_47338_selected": selected_nodes < 47338,
                "phase6_candidate": (
                    selected_nodes < 47338
                    and sum(1 for r in items if r["raw_status"] in {"crash", "timeout", "cec_failed"}) == 0
                    and runtime_warnings == 0
                    and rss_warnings == 0
                ),
            }
        )

    lines = [
        "# Pipeline Search 2.0 Full Summary",
        "",
        f"Usage note: `{USAGE_NOTE}`. This is Phase 5 full pipeline search only; Phase 6/7/8 were not run.",
        "",
        "| candidate | family | selected nodes | raw nodes | max level | CEC | fallback | crash | timeout | CEC fail | W/T/L | gain excl best | gain excl top2 | Phase 6? |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['pipeline_id']} | {row['family']} | {row['selected_total_nodes']} | {row['raw_total_nodes']} | "
            f"{row['max_selected_level']} | {row['raw_cec_passed']}/30 | {row['fallback_count']} | "
            f"{row['crash_count']} | {row['timeout_count']} | {row['cec_fail_count']} | "
            f"{row['wins']}/{row['ties']}/{row['losses']} | {row['gain_excluding_best_case']} | "
            f"{row['gain_excluding_top2_cases']} | {row['phase6_candidate']} |"
        )

    beating = [row for row in summary_rows if row["beats_47338_selected"]]
    phase6 = [row for row in summary_rows if row["phase6_candidate"]]
    lines.extend(
        [
            "",
            "## Findings",
            "",
            f"- Candidates with selected total nodes < 47338: {', '.join(row['pipeline_id'] for row in beating) if beating else 'none'}.",
            f"- Candidates worth Phase 6 anti-overfit review: {', '.join(row['pipeline_id'] for row in phase6) if phase6 else 'none'}.",
            "- Runtime/RSS warning thresholds: runtime ratio > 2.5x or RSS ratio > 2.0x vs current final per case.",
            "",
            "## Stop Point",
            "",
            "Phase 5 completed. Phase 6 anti-overfit, Phase 7 selector, and Phase 8 decision were not run.",
        ]
    )
    summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary_rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--space", default=Path("configs/pipeline_search_space_v2.yaml"), type=Path)
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--final", required=True, type=Path)
    parser.add_argument("--inventory", required=True, type=Path)
    parser.add_argument("--cases", required=True, type=Path)
    parser.add_argument("--abc", required=True, type=Path)
    parser.add_argument("--features", default=Path("reports/features.csv"), type=Path)
    parser.add_argument("--out-dir", default=Path("results/pipeline_search2/full"), type=Path)
    parser.add_argument("--metrics", default=Path("reports/pipeline_search2_metrics.csv"), type=Path)
    parser.add_argument("--summary", default=Path("reports/pipeline_search2_summary.md"), type=Path)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    config = yaml.safe_load(args.space.read_text(encoding="utf-8")) or {}
    inventory = load_inventory(args.inventory)
    candidates = [row for row in read_csv(args.candidates) if row.get("pipeline_id") in APPROVED_PIPELINES]
    seen = {row["pipeline_id"] for row in candidates}
    missing = sorted(APPROVED_PIPELINES - seen)
    if missing:
        raise SystemExit(f"missing approved candidates: {', '.join(missing)}")
    final_rows = read_csv(args.final)
    final = {row["case"]: row for row in final_rows}
    features = {row["case"]: row for row in read_csv(args.features)} if args.features.exists() else {}
    case_names = [row["case"] for row in final_rows]

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
        if disabled_reason(candidate, inventory):
            raise SystemExit(f"approved candidate is not runnable: {candidate['pipeline_id']}: {disabled_reason(candidate, inventory)}")
        for case in case_names:
            if (candidate["pipeline_id"], case) in existing_keys:
                continue
            scale = features.get(case, {}).get("scale_grade", "medium")
            print(f"[full][{candidate['family']}][{candidate['pipeline_id']}][{case}]")
            new_rows.append(
                run_one(
                    args.abc,
                    args.cases,
                    args.out_dir,
                    candidate,
                    case,
                    scale,
                    final[case],
                    config,
                    inventory,
                    abc_sha,
                    runner_sha,
                    stats_parser_sha,
                )
            )
    all_rows = existing + new_rows
    write_csv(args.metrics, all_rows, FIELDS)
    summary_rows = summarize(args.metrics, args.summary)
    summary_csv = args.summary.with_suffix(".csv")
    write_csv(summary_csv, summary_rows, list(summary_rows[0].keys()) if summary_rows else [])
    print(f"wrote {args.metrics}")
    print(f"wrote {args.summary}")
    print(f"wrote {summary_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
