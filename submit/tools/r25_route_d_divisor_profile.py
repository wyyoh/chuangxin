#!/usr/bin/env python3
"""Read-only Route D multi-output divisor recurrence profile."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any


sys.setrecursionlimit(100000)


@dataclass(frozen=True)
class NodeDef:
    output: str
    fanins: tuple[str, ...]
    cubes: tuple[str, ...]


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


def parse_blif(path: Path) -> tuple[list[str], list[str], dict[str, NodeDef], list[NodeDef]]:
    inputs: list[str] = []
    outputs: list[str] = []
    nodes_by_output: dict[str, NodeDef] = {}
    nodes: list[NodeDef] = []
    current_out: str | None = None
    current_fanins: tuple[str, ...] = ()
    current_cubes: list[str] = []

    def flush_current() -> None:
        nonlocal current_out, current_fanins, current_cubes
        if current_out is None:
            return
        node = NodeDef(current_out, current_fanins, tuple(current_cubes))
        nodes_by_output[current_out] = node
        nodes.append(node)
        current_out = None
        current_fanins = ()
        current_cubes = []

    for line in logical_lines(path):
        if line.startswith(".inputs"):
            flush_current()
            inputs.extend(line.split()[1:])
        elif line.startswith(".outputs"):
            flush_current()
            outputs.extend(line.split()[1:])
        elif line.startswith(".names"):
            flush_current()
            parts = line.split()
            if len(parts) >= 2:
                current_out = parts[-1]
                current_fanins = tuple(parts[1:-1])
                current_cubes = []
        elif line.startswith("."):
            flush_current()
        elif current_out is not None:
            current_cubes.append(line)
    flush_current()
    return inputs, outputs, nodes_by_output, nodes


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


def truth_key(node: NodeDef) -> str:
    return f"{len(node.fanins)}|" + "|".join(sorted(node.cubes))


def ordered_pair_key(node: NodeDef) -> str | None:
    if len(node.fanins) != 2:
        return None
    return f"{node.fanins[0]}|{node.fanins[1]}|{truth_key(node)}"


def unordered_pair_key(node: NodeDef) -> str | None:
    if len(node.fanins) != 2:
        return None
    a, b = sorted(node.fanins)
    return f"{a}|{b}|{truth_key(node)}"


def support_key(node: NodeDef) -> str:
    return "|".join(sorted(set(node.fanins)))


def analyze_case(
    case: str,
    input_path: Path,
    metric: dict[str, str],
    feature: dict[str, str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    inputs, outputs, nodes_by_output, nodes = parse_blif(input_path)
    memo: dict[str, frozenset[str]] = {}

    def tfi(signal: str) -> frozenset[str]:
        if signal in memo:
            return memo[signal]
        node = nodes_by_output.get(signal)
        if node is None:
            memo[signal] = frozenset()
            return memo[signal]
        acc: set[str] = {signal}
        for fanin in node.fanins:
            acc.update(tfi(fanin))
        memo[signal] = frozenset(acc)
        return memo[signal]

    po_tfis = {po: tfi(po) for po in outputs}
    coverage: Counter[str] = Counter()
    for tfi_set in po_tfis.values():
        for node_id in tfi_set:
            coverage[node_id] += 1

    tfi_sizes = [len(s) for s in po_tfis.values()]
    unique_tfi_nodes = len(set().union(*po_tfis.values())) if po_tfis else 0
    sum_tfi_nodes = sum(tfi_sizes)
    shared_nodes = [node for node, count in coverage.items() if count >= 2]
    nodes_ge4 = [node for node, count in coverage.items() if count >= 4]
    nodes_ge8 = [node for node, count in coverage.items() if count >= 8]

    ordered_pairs = Counter(k for node in nodes if (k := ordered_pair_key(node)) is not None)
    unordered_pairs = Counter(k for node in nodes if (k := unordered_pair_key(node)) is not None)
    supports = Counter(support_key(node) for node in nodes if len(node.fanins) >= 2)
    truths = Counter(truth_key(node) for node in nodes)

    recurrent_ordered_pairs = {k: v for k, v in ordered_pairs.items() if v >= 2}
    recurrent_unordered_pairs = {k: v for k, v in unordered_pairs.items() if v >= 2}
    recurrent_supports = {k: v for k, v in supports.items() if v >= 2}
    recurrent_truths = {k: v for k, v in truths.items() if v >= 2}

    duplicate_tfi_exposure = max(0, sum_tfi_nodes - unique_tfi_nodes)
    shared_node_ratio = len(shared_nodes) / len(nodes) if nodes else 0.0
    tfi_duplication_ratio = duplicate_tfi_exposure / unique_tfi_nodes if unique_tfi_nodes else 0.0
    max_po_coverage = max(coverage.values(), default=0)
    avg_po_coverage_shared = mean(coverage[node] for node in shared_nodes) if shared_nodes else 0.0

    broad_shared_signal = (
        len(shared_nodes) >= 16
        and max_po_coverage >= 2
        and (tfi_duplication_ratio >= 0.10 or len(nodes_ge4) >= 8)
    )
    recurrence_signal = (
        len(recurrent_unordered_pairs) >= 1
        or len(recurrent_supports) >= 3
        or len(recurrent_truths) >= 3
    )
    candidate_source_signal = broad_shared_signal and recurrence_signal
    outside_v4_high_overlap = metric.get("selector_reason") != "r7b_high_overlap_guarded_fraig"

    row: dict[str, Any] = {
        "case": case,
        "input_path": str(input_path),
        "selector_reason": metric.get("selector_reason", ""),
        "selected_pipeline": metric.get("selected_pipeline", ""),
        "final_selected_nodes": metric.get("selected_nodes", ""),
        "final_selected_levels": metric.get("selected_levels", ""),
        "pi_count": len(inputs),
        "po_count": len(outputs),
        "names_count": len(nodes),
        "scale_grade": feature.get("scale_grade", ""),
        "runtime_size_bin": feature.get("runtime_size_bin", ""),
        "near_two_input_aig": feature.get("near_two_input_aig", ""),
        "high_fanin_sop": feature.get("high_fanin_sop", ""),
        "po_bin": feature.get("po_bin", ""),
        "pi_bin": feature.get("pi_bin", ""),
        "two_input_ratio_bin": feature.get("two_input_ratio_bin", ""),
        "unique_tfi_nodes": unique_tfi_nodes,
        "sum_tfi_nodes": sum_tfi_nodes,
        "duplicate_tfi_exposure": duplicate_tfi_exposure,
        "tfi_duplication_ratio": f"{tfi_duplication_ratio:.6f}",
        "po_tfi_min": min(tfi_sizes, default=0),
        "po_tfi_avg": f"{mean(tfi_sizes):.3f}" if tfi_sizes else "0.000",
        "po_tfi_max": max(tfi_sizes, default=0),
        "shared_node_count": len(shared_nodes),
        "shared_node_ratio": f"{shared_node_ratio:.6f}",
        "nodes_shared_by_ge4_po": len(nodes_ge4),
        "nodes_shared_by_ge8_po": len(nodes_ge8),
        "max_node_po_coverage": max_po_coverage,
        "avg_po_coverage_shared": f"{avg_po_coverage_shared:.3f}",
        "recurrent_ordered_fanin_pair_patterns": len(recurrent_ordered_pairs),
        "recurrent_unordered_fanin_pair_patterns": len(recurrent_unordered_pairs),
        "max_recurrent_unordered_pair_count": max(recurrent_unordered_pairs.values(), default=0),
        "recurrent_support_patterns": len(recurrent_supports),
        "max_recurrent_support_count": max(recurrent_supports.values(), default=0),
        "recurrent_truth_patterns": len(recurrent_truths),
        "max_recurrent_truth_count": max(recurrent_truths.values(), default=0),
        "broad_shared_signal": broad_shared_signal,
        "recurrence_signal": recurrence_signal,
        "candidate_source_signal": candidate_source_signal,
        "outside_v4_high_overlap": outside_v4_high_overlap,
        "route_d_priority": (
            "high"
            if candidate_source_signal and outside_v4_high_overlap
            else "covered_high_overlap"
            if candidate_source_signal
            else "low"
        ),
    }

    top_rows: list[dict[str, Any]] = []
    for kind, counter in [
        ("unordered_fanin_pair", Counter(recurrent_unordered_pairs)),
        ("support_set", Counter(recurrent_supports)),
        ("truth_pattern", Counter(recurrent_truths)),
    ]:
        for rank, (pattern, count) in enumerate(counter.most_common(5), start=1):
            top_rows.append(
                {
                    "case": case,
                    "pattern_kind": kind,
                    "rank": rank,
                    "count": count,
                    "pattern": pattern[:240],
                    "selector_reason": metric.get("selector_reason", ""),
                    "candidate_source_signal": candidate_source_signal,
                    "route_d_priority": row["route_d_priority"],
                }
            )
    return row, top_rows


def summarize(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get(key, ""))].append(row)
    summary: list[dict[str, Any]] = []
    for value, subset in sorted(groups.items()):
        summary.append(
            {
                "group_by": key,
                "group": value,
                "case_count": len(subset),
                "candidate_source_signal_count": sum(str(r["candidate_source_signal"]) == "True" for r in subset),
                "high_priority_count": sum(r["route_d_priority"] == "high" for r in subset),
                "covered_high_overlap_count": sum(r["route_d_priority"] == "covered_high_overlap" for r in subset),
                "avg_shared_node_count": f"{mean(to_int(r['shared_node_count']) for r in subset):.3f}",
                "avg_tfi_duplication_ratio": f"{mean(to_float(r['tfi_duplication_ratio']) for r in subset):.6f}",
                "max_recurrent_unordered_pair_count": max(to_int(r["max_recurrent_unordered_pair_count"]) for r in subset),
                "max_recurrent_truth_count": max(to_int(r["max_recurrent_truth_count"]) for r in subset),
            }
        )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics", type=Path, default=Path("reports/final_metrics.csv"))
    parser.add_argument("--features", type=Path, default=Path("reports/features.csv"))
    parser.add_argument("--csv", type=Path, default=Path("results_research/R25_phase1_route_D_divisor_profile.csv"))
    parser.add_argument("--patterns-csv", type=Path, default=Path("results_research/R25_phase1_route_D_top_patterns.csv"))
    parser.add_argument("--summary-csv", type=Path, default=Path("results_research/R25_phase1_route_D_divisor_profile_summary.csv"))
    args = parser.parse_args()

    metrics = {row["case"]: row for row in read_csv(args.metrics)}
    features = {row["case"]: row for row in read_csv(args.features)}
    rows: list[dict[str, Any]] = []
    top_rows: list[dict[str, Any]] = []
    for case in sorted(metrics):
        metric = metrics[case]
        feature = features.get(case, {})
        row, patterns = analyze_case(case, Path(metric["input_path"]), metric, feature)
        rows.append(row)
        top_rows.extend(patterns)
        print(
            f"[{case}] shared={row['shared_node_count']} "
            f"dup={row['tfi_duplication_ratio']} recurrent_pairs={row['recurrent_unordered_fanin_pair_patterns']} "
            f"priority={row['route_d_priority']}"
        )

    args.csv.parent.mkdir(parents=True, exist_ok=True)
    write_csv(args.csv, rows, list(rows[0].keys()) if rows else [])
    write_csv(args.patterns_csv, top_rows, list(top_rows[0].keys()) if top_rows else [])
    summary_rows = (
        summarize(rows, "selector_reason")
        + summarize(rows, "scale_grade")
        + summarize(rows, "route_d_priority")
    )
    write_csv(args.summary_csv, summary_rows, list(summary_rows[0].keys()) if summary_rows else [])
    print(f"wrote {args.csv}")
    print(f"wrote {args.patterns_csv}")
    print(f"wrote {args.summary_csv}")
    return 0


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
