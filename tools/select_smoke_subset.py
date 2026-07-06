#!/usr/bin/env python3
"""Create a fixed, bucket-diverse smoke subset for Pipeline Search 2.0."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Callable


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def as_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def i(row: dict[str, str], key: str) -> int:
    return int(float(row.get(key, "0") or 0))


def flt(row: dict[str, str], key: str) -> float:
    return float(row.get(key, "0") or 0)


def bucket_name(row: dict[str, str]) -> str:
    return "|".join(
        [
            row.get("scale_grade", ""),
            "near_aig" if as_bool(row.get("near_two_input_aig", "")) else "non_aig",
            "high_sop" if as_bool(row.get("high_fanin_sop", "")) else "not_sop",
            row.get("po_bin", ""),
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", required=True, type=Path)
    parser.add_argument("--final", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    features = {row["case"]: row for row in read_csv(args.features)}
    final = {row["case"]: row for row in read_csv(args.final)}
    rows: list[dict[str, str]] = []
    for case in sorted(final):
        feat = features.get(case, {})
        met = final[case]
        gain = i(met, "baseline_nodes") - i(met, "selected_nodes")
        rows.append({**feat, **met, "node_gain_vs_baseline": str(gain), "selector_bucket": bucket_name(feat)})

    selected: dict[str, dict[str, object]] = {}

    def add(
        reason: str,
        predicate: Callable[[dict[str, str]], bool],
        sort_key: Callable[[dict[str, str]], tuple[float, ...]],
    ) -> None:
        matches = [row for row in rows if predicate(row)]
        if not matches:
            return
        matches.sort(key=sort_key, reverse=True)
        choice = next((row for row in matches if row["case"] not in selected), matches[0])
        if choice["case"] in selected:
            selected[choice["case"]]["selection_reason"] = (
                str(selected[choice["case"]]["selection_reason"]) + "; " + reason
            )
        else:
            selected[choice["case"]] = {
                "selection_order": len(selected) + 1,
                "case": choice["case"],
                "selection_reason": reason,
                "selector_bucket": choice.get("selector_bucket", ""),
                "scale_grade": choice.get("scale_grade", ""),
                "pi_bin": choice.get("pi_bin", ""),
                "po_bin": choice.get("po_bin", ""),
                "names_bin": choice.get("names_bin", ""),
                "cubes_bin": choice.get("cubes_bin", ""),
                "max_fanin": choice.get("max_fanin", ""),
                "avg_fanin": choice.get("avg_fanin", ""),
                "two_input_ratio": choice.get("two_input_ratio", ""),
                "high_fanin_sop": choice.get("high_fanin_sop", ""),
                "near_two_input_aig": choice.get("near_two_input_aig", ""),
                "final_pipeline": choice.get("requested_pipeline", ""),
                "final_nodes": choice.get("selected_nodes", ""),
                "final_levels": choice.get("selected_levels", ""),
                "baseline_nodes": choice.get("baseline_nodes", ""),
                "node_gain_vs_baseline": choice.get("node_gain_vs_baseline", ""),
                "opt_runtime_sec": choice.get("opt_runtime_sec", ""),
                "cec_runtime_sec": choice.get("cec_runtime_sec", ""),
                "peak_mem_mb": choice.get("peak_mem_mb", ""),
                "usage_note": "SMOKE_ONLY_NOT_FINAL_CONCLUSION",
            }

    add(
        "largest node gain vs baseline",
        lambda r: True,
        lambda r: (i(r, "node_gain_vs_baseline"), i(r, "selected_nodes")),
    )
    add(
        "max-level pressure case",
        lambda r: True,
        lambda r: (i(r, "selected_levels"), i(r, "selected_nodes")),
    )
    add(
        "large near-two-input AIG with small output bin",
        lambda r: r.get("scale_grade") == "large" and as_bool(r.get("near_two_input_aig", "")) and r.get("po_bin") == "po_small",
        lambda r: (i(r, "selected_nodes"), i(r, "node_gain_vs_baseline")),
    )
    add(
        "large near-two-input AIG with medium output bin",
        lambda r: r.get("scale_grade") == "large" and as_bool(r.get("near_two_input_aig", "")) and r.get("po_bin") == "po_medium",
        lambda r: (i(r, "selected_nodes"), i(r, "node_gain_vs_baseline")),
    )
    add(
        "medium non-AIG selector rewrite bucket",
        lambda r: r.get("scale_grade") == "medium" and not as_bool(r.get("near_two_input_aig", "")),
        lambda r: (i(r, "selected_nodes"), i(r, "node_gain_vs_baseline")),
    )
    add(
        "medium near-two-input AIG bucket",
        lambda r: r.get("scale_grade") == "medium" and as_bool(r.get("near_two_input_aig", "")),
        lambda r: (i(r, "selected_nodes"), i(r, "node_gain_vs_baseline")),
    )
    add(
        "tiny high-fanin SOP bucket",
        lambda r: r.get("scale_grade") == "tiny" and as_bool(r.get("high_fanin_sop", "")),
        lambda r: (i(r, "selected_nodes"), flt(r, "two_input_ratio")),
    )
    add(
        "small high-fanin SOP bucket",
        lambda r: r.get("scale_grade") == "small" and as_bool(r.get("high_fanin_sop", "")),
        lambda r: (i(r, "selected_nodes"), flt(r, "two_input_ratio")),
    )
    add(
        "small near-two-input AIG bucket",
        lambda r: r.get("scale_grade") == "small" and as_bool(r.get("near_two_input_aig", "")),
        lambda r: (i(r, "selected_nodes"), i(r, "node_gain_vs_baseline")),
    )
    add(
        "zero-gain guard bucket",
        lambda r: i(r, "node_gain_vs_baseline") == 0,
        lambda r: (i(r, "selected_nodes"), i(r, "selected_levels")),
    )
    add(
        "tiny non-SOP non-AIG guard bucket",
        lambda r: r.get("scale_grade") == "tiny"
        and not as_bool(r.get("high_fanin_sop", ""))
        and not as_bool(r.get("near_two_input_aig", "")),
        lambda r: (i(r, "selected_nodes"), i(r, "selected_levels")),
    )

    out_rows = sorted(selected.values(), key=lambda r: int(r["selection_order"]))
    fields = list(out_rows[0].keys()) if out_rows else []
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
