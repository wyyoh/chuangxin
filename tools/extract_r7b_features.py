#!/usr/bin/env python3
"""Generate R7b coarse TFI-overlap features for candidate selectors.

This is research/candidate tooling. It profiles each input with the ABC-native
`r7win -profile -diag` command and appends coarse overlap/containment fields to
an existing BLIF feature CSV. It does not optimize networks or generate submit
artifacts.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from eval_public import discover_cases
from run_abc_case import abc_quote, run_abc_command


R7B_FIELDS = [
    "r7b_eligible",
    "r7b_skip_reason",
    "r7b_cluster_potential_score",
    "r7b_high_overlap_pairs",
    "r7b_clusters_seen",
    "r7b_num_eligible_clusters",
    "r7b_largest_cluster_size",
    "r7b_max_shared_nodes",
    "r7b_max_containment",
    "r7b_max_jaccard",
    "r7b_before_nodes",
    "r7b_before_levels",
    "r7b_profile_returncode",
    "r7b_profile_timeout",
    "r7b_profile_runtime_sec",
    "r7b_profile_log",
]


def parse_diag(text: str) -> dict[str, str]:
    for line in text.splitlines():
        if not line.startswith("r7win_diag"):
            continue
        diag: dict[str, str] = {}
        for part in line.split(",")[1:]:
            key, sep, value = part.partition("=")
            if sep:
                diag[key] = value
        return diag
    return {}


def load_base_features(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    return rows, fields


def run_profile(case: str, input_blif: Path, args: argparse.Namespace) -> dict[str, str]:
    log_dir = args.work_dir / case / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "r7b_profile.log"
    command = (
        f"read_blif {abc_quote(input_blif)}; strash; "
        f"r7win -profile -F fraig -G 0 -diag -case {case}"
    )
    result = run_abc_command(args.abc, command, args.timeout, log_path, env={"SHARECONE_CASE": case})
    diag = parse_diag(result.stdout + "\n" + result.stderr)
    return {
        "r7b_eligible": "true" if diag.get("eligible_for_future_rewrite") == "1" else "false",
        "r7b_skip_reason": diag.get("skip_reason", "profile_failed" if result.returncode != 0 else ""),
        "r7b_cluster_potential_score": diag.get("cluster_potential_score", ""),
        "r7b_high_overlap_pairs": diag.get("num_high_overlap_pairs", ""),
        "r7b_clusters_seen": diag.get("clusters_seen", ""),
        "r7b_num_eligible_clusters": diag.get("num_eligible_clusters", ""),
        "r7b_largest_cluster_size": diag.get("largest_cluster_size", ""),
        "r7b_max_shared_nodes": diag.get("max_shared_nodes", ""),
        "r7b_max_containment": diag.get("max_containment", ""),
        "r7b_max_jaccard": diag.get("max_jaccard", ""),
        "r7b_before_nodes": diag.get("before_nodes", ""),
        "r7b_before_levels": diag.get("before_levels", ""),
        "r7b_profile_returncode": str(result.returncode),
        "r7b_profile_timeout": "true" if result.timed_out else "false",
        "r7b_profile_runtime_sec": f"{result.runtime_sec:.6f}",
        "r7b_profile_log": str(log_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--abc", required=True, type=Path)
    parser.add_argument("--cases", required=True, type=Path)
    parser.add_argument("--base-features", required=True, type=Path)
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args()

    base_rows, base_fields = load_base_features(args.base_features)
    rows_by_case = {row["case"]: row for row in base_rows}
    for case, input_blif in discover_cases(args.cases):
        if case not in rows_by_case:
            rows_by_case[case] = {"case": case, "path": str(input_blif)}
        rows_by_case[case].update(run_profile(case, input_blif, args))
        print(
            f"[{case}] r7b_eligible={rows_by_case[case].get('r7b_eligible')} "
            f"skip={rows_by_case[case].get('r7b_skip_reason')}"
        )

    fields = list(base_fields)
    for field in R7B_FIELDS:
        if field not in fields:
            fields.append(field)
    ordered_rows = [rows_by_case[case] for case, _ in discover_cases(args.cases)]
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    with args.csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(ordered_rows)
    print(f"wrote {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
