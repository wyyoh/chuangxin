#!/usr/bin/env python3
"""R30b release integration wrapper.

The formal v7 optimizer is still the base entrypoint. This layer profiles the
v7 output with coarse multi-output TFI overlap features, then tries one guarded
ODC-style post-pass only for the R30b balanced structural buckets. A trial is
accepted only after CEC, node decrease, and level non-regression.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from eval_public import load_yaml_like
from optimize_one_r29_postpass_candidate import optimize_one as optimize_v7
from run_abc_case import collect_stats, run_cec, run_optimization


DEFAULT_R30_POSTPASS = "r30b_odc_resub_f1"
PROFILE_PO_LIMIT = 2048
PROFILE_NODE_LIMIT = 200000


def int_metric(value: Any) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return 0


def abc_reported_error(*texts: str) -> bool:
    combined = "\n".join(texts)
    return "Error:" in combined or "usage:" in combined or "Cannot find" in combined


def logical_lines(path: Path) -> list[str]:
    merged: list[str] = []
    current = ""
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.endswith("\\"):
            current += line[:-1].strip() + " "
            continue
        merged.append((current + line).strip())
        current = ""
    if current.strip():
        merged.append(current.strip())
    return merged


@dataclass
class BlifGraph:
    inputs: list[str]
    outputs: list[str]
    fanins: dict[str, list[str]]


def parse_blif_graph(path: Path) -> BlifGraph:
    inputs: list[str] = []
    outputs: list[str] = []
    fanins: dict[str, list[str]] = {}
    for line in logical_lines(path):
        parts = line.split()
        if not parts:
            continue
        if parts[0] == ".inputs":
            inputs.extend(parts[1:])
        elif parts[0] == ".outputs":
            outputs.extend(parts[1:])
        elif parts[0] == ".names" and len(parts) >= 2:
            fanins[parts[-1]] = parts[1:-1]
    return BlifGraph(inputs=inputs, outputs=outputs, fanins=fanins)


def tfi_for_output(graph: BlifGraph, output: str) -> set[str]:
    seen: set[str] = set()
    stack = [output]
    input_set = set(graph.inputs)
    while stack:
        node = stack.pop()
        for fanin in graph.fanins.get(node, []):
            if fanin in input_set or fanin in seen:
                continue
            seen.add(fanin)
            stack.append(fanin)
    if output in graph.fanins and output not in input_set:
        seen.add(output)
    return seen


def cluster_bucket(score: float, pairs: int, largest: int) -> str:
    if score >= 80 and largest >= 4 and pairs >= 8:
        return "cluster_high"
    if score >= 55 and pairs >= 2:
        return "cluster_medium"
    if pairs > 0:
        return "cluster_low"
    return "cluster_none"


def connected_components(edges: dict[int, set[int]], nodes: list[int], max_cluster_size: int = 8) -> list[list[int]]:
    unseen = set(nodes)
    comps: list[list[int]] = []
    while unseen:
        start = min(unseen)
        queue: deque[int] = deque([start])
        unseen.remove(start)
        comp: list[int] = []
        while queue and len(comp) < max_cluster_size:
            cur = queue.popleft()
            comp.append(cur)
            for nxt in sorted(edges.get(cur, set())):
                if nxt not in unseen:
                    continue
                unseen.remove(nxt)
                queue.append(nxt)
                if len(comp) + len(queue) >= max_cluster_size:
                    break
        comps.append(comp)
    return comps


def profile_output(path: Path) -> tuple[dict[str, Any], float]:
    start = time.perf_counter()
    try:
        graph = parse_blif_graph(path)
        po_count = len(graph.outputs)
        node_count = len(graph.fanins)
        if po_count < 2:
            return {
                "profile_status": "skipped",
                "profile_skip_reason": "po_count_lt2",
                "po_count": po_count,
                "node_count": node_count,
                "cluster_bucket": "cluster_none",
                "cluster_potential_score": "0.000000",
                "high_overlap_pairs": 0,
                "largest_cluster_size": 0,
            }, time.perf_counter() - start
        if po_count > PROFILE_PO_LIMIT or node_count > PROFILE_NODE_LIMIT:
            return {
                "profile_status": "skipped",
                "profile_skip_reason": "profile_size_cap",
                "po_count": po_count,
                "node_count": node_count,
                "cluster_bucket": "cluster_none",
                "cluster_potential_score": "0.000000",
                "high_overlap_pairs": 0,
                "largest_cluster_size": 0,
            }, time.perf_counter() - start

        po_tfis = [tfi_for_output(graph, po) for po in graph.outputs]
        coverage: dict[str, int] = defaultdict(int)
        for tfi in po_tfis:
            for node in tfi:
                coverage[node] += 1
        unique_tfi = len(coverage)
        sum_tfi = sum(len(tfi) for tfi in po_tfis)
        duplicate = max(0, sum_tfi - unique_tfi)
        shared_nodes = [node for node, count in coverage.items() if count >= 2]
        shared_count = len(shared_nodes)
        shared_ratio = shared_count / unique_tfi if unique_tfi else 0.0

        high_pairs = 0
        max_containment = 0.0
        max_jaccard = 0.0
        pair_edges: dict[int, set[int]] = defaultdict(set)
        for i, left in enumerate(po_tfis):
            if not left:
                continue
            for j in range(i + 1, po_count):
                right = po_tfis[j]
                if not right:
                    continue
                shared = len(left & right)
                if shared <= 0:
                    continue
                containment = shared / max(1, min(len(left), len(right)))
                jaccard = shared / max(1, len(left | right))
                max_containment = max(max_containment, containment)
                max_jaccard = max(max_jaccard, jaccard)
                if shared >= 16 and (containment >= 0.75 or jaccard >= 0.20):
                    high_pairs += 1
                    pair_edges[i].add(j)
                    pair_edges[j].add(i)

        comps = connected_components(pair_edges, list(pair_edges.keys())) if pair_edges else []
        eligible = [comp for comp in comps if len(comp) >= 2]
        largest = max((len(comp) for comp in eligible), default=0)
        dup_ratio = duplicate / unique_tfi if unique_tfi else 0.0
        score = min(
            100.0,
            20.0 * math.log1p(high_pairs)
            + 100.0 * shared_ratio
            + 8.0 * min(6.0, dup_ratio)
            + 6.0 * largest,
        )
        return {
            "profile_status": "ok",
            "profile_skip_reason": "",
            "po_count": po_count,
            "node_count": node_count,
            "unique_tfi_nodes": unique_tfi,
            "sum_tfi_nodes": sum_tfi,
            "duplicate_tfi_exposure": duplicate,
            "shared_node_count": shared_count,
            "shared_node_ratio": f"{shared_ratio:.6f}",
            "max_containment": f"{max_containment:.6f}",
            "max_jaccard": f"{max_jaccard:.6f}",
            "clusters_seen": len(comps),
            "eligible_clusters": len(eligible),
            "cluster_potential_score": f"{score:.6f}",
            "cluster_bucket": cluster_bucket(score, high_pairs, largest),
            "high_overlap_pairs": high_pairs,
            "largest_cluster_size": largest,
        }, time.perf_counter() - start
    except Exception as exc:  # Keep the formal path on v7 if profiling fails.
        return {
            "profile_status": "error",
            "profile_skip_reason": type(exc).__name__,
            "cluster_bucket": "cluster_none",
            "cluster_potential_score": "0.000000",
            "high_overlap_pairs": 0,
            "largest_cluster_size": 0,
        }, time.perf_counter() - start


def balanced_gate(profile: dict[str, Any], nodes: int, levels: int) -> tuple[bool, str]:
    bucket = str(profile.get("cluster_bucket") or "")
    pairs = int_metric(profile.get("high_overlap_pairs"))
    largest = int_metric(profile.get("largest_cluster_size"))
    if bucket == "cluster_none" and nodes >= 5000 and levels >= 18 and pairs == 0:
        return True, "huge_highlevel_low_overlap"
    if bucket == "cluster_high" and 800 <= nodes <= 1500 and pairs >= 100 and largest >= 8:
        return True, "mid_nodes_high_overlap_cluster"
    if bucket == "cluster_medium" and nodes >= 300 and levels >= 10 and pairs >= 5 and largest >= 5:
        return True, "medium_cluster_mid_nodes"
    return False, "gate_not_matched"


def load_postpass_steps(config_path: Path, postpass_name: str) -> str:
    config = load_yaml_like(config_path)
    entry = (config.get("pipelines", {}) or {}).get(postpass_name)
    if not entry:
        raise KeyError(f"R30b post-pass not found: {postpass_name}")
    return str((entry or {}).get("steps", "")).strip()


def run_postpass(
    *,
    abc: Path,
    original_input: Path,
    v7_output: Path,
    postpass_name: str,
    postpass_steps: str,
    baseline_nodes: int,
    baseline_levels: int,
    work_dir: Path,
    timeouts: dict[str, float],
    gate_reason: str,
) -> dict[str, Any]:
    cand_dir = work_dir / "r30b_postpass" / postpass_name
    cand_dir.mkdir(parents=True, exist_ok=True)
    output = cand_dir / "output.blif"
    if output.exists():
        output.unlink()

    opt = run_optimization(
        abc,
        v7_output,
        output,
        postpass_steps,
        timeouts["opt"],
        cand_dir / "opt.log",
        env={"R30B_GATE": gate_reason, "R30B_POSTPASS": postpass_name},
    )
    opt_error = abc_reported_error(opt.stdout, opt.stderr)
    opt_ok = opt.returncode == 0 and not opt.timed_out and not opt_error and output.exists()

    cec_pass = False
    cec = None
    stats_result = None
    stats: dict[str, Any] = {}
    nodes = 0
    levels = 0
    reject_reason = ""
    if opt_ok:
        cec_pass, cec = run_cec(abc, original_input, output, timeouts["cec"], cand_dir / "cec.log")
        if cec_pass:
            stats, stats_result = collect_stats(abc, output, timeouts["stats"], cand_dir / "stats.log")
            nodes = int_metric(stats.get("aig_nodes"))
            levels = int_metric(stats.get("levels"))
        else:
            (cand_dir / "stats.log").write_text("stats skipped because trial CEC failed\n", encoding="utf-8")
    else:
        (cand_dir / "cec.log").write_text("cec skipped because optimization failed\n", encoding="utf-8")
        (cand_dir / "stats.log").write_text("stats skipped because optimization failed\n", encoding="utf-8")

    if opt.timed_out or (cec and cec.timed_out) or (stats_result and stats_result.timed_out):
        reject_reason = "timeout"
    elif not opt_ok:
        reject_reason = "opt_failed"
    elif not cec_pass:
        reject_reason = "cec_failed"
    elif nodes <= 0:
        reject_reason = "stats_missing"
    elif nodes >= baseline_nodes:
        reject_reason = "no_node_gain"
    elif levels > baseline_levels:
        reject_reason = "level_regression"

    accepted = reject_reason == ""
    peak = max(
        opt.peak_mem_mb,
        cec.peak_mem_mb if cec else 0.0,
        stats_result.peak_mem_mb if stats_result else 0.0,
    )
    return {
        "candidate": postpass_name,
        "steps": postpass_steps,
        "accepted": accepted,
        "reject_reason": reject_reason,
        "output_path": str(output),
        "nodes": nodes,
        "levels": levels,
        "node_delta_vs_v7": nodes - baseline_nodes if nodes else "",
        "level_delta_vs_v7": levels - baseline_levels if levels else "",
        "opt_returncode": opt.returncode,
        "opt_error": opt_error,
        "cec_returncode": cec.returncode if cec else "",
        "cec_pass": cec_pass,
        "opt_runtime_sec": float(f"{opt.runtime_sec:.6f}"),
        "cec_runtime_sec": float(f"{cec.runtime_sec:.6f}") if cec else 0.0,
        "stats_runtime_sec": float(f"{stats_result.runtime_sec:.6f}") if stats_result else 0.0,
        "peak_mem_mb": float(f"{peak:.3f}"),
    }


def r30_empty_fields(
    *,
    gate: str,
    status: str,
    postpass: str,
    reject_reason: str,
    profile: dict[str, Any],
    profile_runtime: float,
) -> dict[str, Any]:
    return {
        "r30b_postpass_gate": gate,
        "r30b_postpass_status": status,
        "r30b_postpass": postpass,
        "r30b_postpass_accepted": "",
        "r30b_postpass_reject_reason": reject_reason,
        "r30b_postpass_opt_returncode": "",
        "r30b_postpass_cec_pass": "",
        "r30b_postpass_opt_error": "",
        "r30b_node_delta_vs_v7": 0,
        "r30b_level_delta_vs_v7": 0,
        "r30b_profile_runtime_sec": float(f"{profile_runtime:.6f}"),
        "r30b_profile_status": profile.get("profile_status", ""),
        "r30b_profile_skip_reason": profile.get("profile_skip_reason", ""),
        "r30b_cluster_bucket": profile.get("cluster_bucket", ""),
        "r30b_cluster_potential_score": profile.get("cluster_potential_score", ""),
        "r30b_high_overlap_pairs": profile.get("high_overlap_pairs", ""),
        "r30b_largest_cluster_size": profile.get("largest_cluster_size", ""),
        "r30b_po_count": profile.get("po_count", ""),
        "r30b_node_count": profile.get("node_count", ""),
    }


def optimize_one(args: argparse.Namespace) -> dict[str, Any]:
    v7_output = args.work_dir / "v7" / "output.blif"
    v7_args = argparse.Namespace(**vars(args))
    v7_args.output = v7_output
    v7_args.work_dir = args.work_dir / "v7" / "work"
    v7_args.metrics_json = args.work_dir / "v7" / "metrics.json"
    v7_payload = optimize_v7(v7_args)
    v7_args.metrics_json.parent.mkdir(parents=True, exist_ok=True)
    v7_args.metrics_json.write_text(json.dumps(v7_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    profile: dict[str, Any] = {}
    profile_runtime = 0.0
    if not v7_payload.get("cec_pass"):
        shutil.copyfile(v7_output if v7_output.exists() else args.input, args.output)
        return {
            **v7_payload,
            "output_path": str(args.output),
            **r30_empty_fields(
                gate="v7_cec_failed",
                status="v7_cec_failed",
                postpass=args.r30_postpass,
                reject_reason="v7_cec_failed",
                profile=profile,
                profile_runtime=profile_runtime,
            ),
        }

    baseline_nodes = int_metric(v7_payload.get("selected_nodes"))
    baseline_levels = int_metric(v7_payload.get("selected_levels"))
    profile, profile_runtime = profile_output(v7_output)
    matched, gate_reason = balanced_gate(profile, baseline_nodes, baseline_levels)
    if not matched:
        shutil.copyfile(v7_output, args.output)
        payload = dict(v7_payload)
        payload.update(
            {
                "output_path": str(args.output),
                "opt_runtime_sec": float(f"{float(v7_payload.get('opt_runtime_sec') or 0.0) + profile_runtime:.6f}"),
                **r30_empty_fields(
                    gate=gate_reason,
                    status="skipped",
                    postpass=args.r30_postpass,
                    reject_reason="gate_not_matched",
                    profile=profile,
                    profile_runtime=profile_runtime,
                ),
            }
        )
        return payload

    postpass_steps = load_postpass_steps(args.r30_pipelines, args.r30_postpass)
    attempt = run_postpass(
        abc=args.abc,
        original_input=args.input,
        v7_output=v7_output,
        postpass_name=args.r30_postpass,
        postpass_steps=postpass_steps,
        baseline_nodes=baseline_nodes,
        baseline_levels=baseline_levels,
        work_dir=args.work_dir,
        timeouts={"opt": args.post_opt_timeout, "cec": args.cec_timeout, "stats": args.stats_timeout},
        gate_reason=gate_reason,
    )

    selected_source = Path(attempt["output_path"]) if attempt["accepted"] else v7_output
    shutil.copyfile(selected_source, args.output)

    final_cec_pass = bool(v7_payload.get("cec_pass"))
    final_cec_returncode: Any = v7_payload.get("cec_returncode", "")
    final_cec_runtime = 0.0
    final_stats_runtime = 0.0
    final_peak = 0.0
    selected_nodes = int_metric(v7_payload.get("selected_nodes"))
    selected_levels = int_metric(v7_payload.get("selected_levels"))
    fallback_reason = ""

    if attempt["accepted"]:
        final_cec_pass, final_cec = run_cec(
            args.abc,
            args.input,
            args.output,
            args.cec_timeout,
            args.work_dir / "logs" / "r30b_final_cec.log",
        )
        final_cec_returncode = final_cec.returncode
        final_cec_runtime = final_cec.runtime_sec
        final_peak = max(final_peak, final_cec.peak_mem_mb)
        if not final_cec_pass:
            shutil.copyfile(v7_output, args.output)
            fallback_reason = "r30b_final_cec_failed"
        final_stats, final_stats_result = collect_stats(
            args.abc,
            args.output,
            args.stats_timeout,
            args.work_dir / "logs" / "r30b_final_stats.log",
        )
        final_stats_runtime = final_stats_result.runtime_sec
        final_peak = max(final_peak, final_stats_result.peak_mem_mb)
        selected_nodes = int_metric(final_stats.get("aig_nodes"))
        selected_levels = int_metric(final_stats.get("levels"))

    post_opt_runtime = profile_runtime + float(attempt.get("opt_runtime_sec") or 0.0)
    post_cec_runtime = float(attempt.get("cec_runtime_sec") or 0.0) + final_cec_runtime
    post_stats_runtime = float(attempt.get("stats_runtime_sec") or 0.0) + final_stats_runtime
    post_peak = max(float(attempt.get("peak_mem_mb") or 0.0), final_peak)
    v7_peak = float(v7_payload.get("peak_mem_mb") or 0.0)

    payload = dict(v7_payload)
    payload.update(
        {
            "output_path": str(args.output),
            "selected_nodes": selected_nodes,
            "selected_levels": selected_levels,
            "cec_pass": bool(final_cec_pass),
            "cec_returncode": final_cec_returncode,
            "status": "selected_candidate" if final_cec_pass and not fallback_reason else "fallback_baseline",
            "fallback_reason": fallback_reason,
            "selected_pipeline": (
                f"{v7_payload.get('selected_pipeline')}+{args.r30_postpass}"
                if attempt["accepted"] and not fallback_reason
                else str(v7_payload.get("selected_pipeline"))
            ),
            "opt_runtime_sec": float(f"{float(v7_payload.get('opt_runtime_sec') or 0.0) + post_opt_runtime:.6f}"),
            "cec_runtime_sec": float(f"{float(v7_payload.get('cec_runtime_sec') or 0.0) + post_cec_runtime:.6f}"),
            "stats_runtime_sec": float(f"{float(v7_payload.get('stats_runtime_sec') or 0.0) + post_stats_runtime:.6f}"),
            "peak_mem_mb": float(f"{max(v7_peak, post_peak):.3f}"),
            "log_dir": str(args.work_dir / "logs"),
            "r30b_postpass_gate": gate_reason,
            "r30b_postpass_status": "accepted" if attempt["accepted"] and not fallback_reason else "rejected",
            "r30b_postpass": args.r30_postpass,
            "r30b_postpass_accepted": args.r30_postpass if attempt["accepted"] and not fallback_reason else "",
            "r30b_postpass_reject_reason": attempt["reject_reason"] or fallback_reason,
            "r30b_postpass_opt_returncode": attempt["opt_returncode"],
            "r30b_postpass_cec_pass": attempt["cec_pass"],
            "r30b_postpass_opt_error": attempt["opt_error"],
            "r30b_node_delta_vs_v7": selected_nodes - baseline_nodes,
            "r30b_level_delta_vs_v7": selected_levels - baseline_levels,
            "r30b_profile_runtime_sec": float(f"{profile_runtime:.6f}"),
            "r30b_profile_status": profile.get("profile_status", ""),
            "r30b_profile_skip_reason": profile.get("profile_skip_reason", ""),
            "r30b_cluster_bucket": profile.get("cluster_bucket", ""),
            "r30b_cluster_potential_score": profile.get("cluster_potential_score", ""),
            "r30b_high_overlap_pairs": profile.get("high_overlap_pairs", ""),
            "r30b_largest_cluster_size": profile.get("largest_cluster_size", ""),
            "r30b_po_count": profile.get("po_count", ""),
            "r30b_node_count": profile.get("node_count", ""),
            "r30b_attempt": attempt,
        }
    )
    return payload
