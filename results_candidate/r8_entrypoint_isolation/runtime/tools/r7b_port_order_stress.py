#!/usr/bin/env python3
"""Generate and compare R7b PI/PO declaration-order randomization stress cases."""

from __future__ import annotations

import argparse
import csv
import random
import shutil
from pathlib import Path


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


def discover_cases(cases_dir: Path) -> list[tuple[str, Path]]:
    cases: list[tuple[str, Path]] = []
    for child in sorted(cases_dir.iterdir(), key=lambda p: p.name):
        if child.is_dir() and (child / "input.blif").exists():
            cases.append((child.name, child / "input.blif"))
    return cases


def wrap_directive(directive: str, tokens: list[str], width: int = 100) -> list[str]:
    if not tokens:
        return [directive]
    out: list[str] = []
    current = directive
    for token in tokens:
        if len(current) + 1 + len(token) > width:
            out.append(current + " \\")
            current = "  " + token
        else:
            current += " " + token
    out.append(current)
    return out


def shuffle_ports(tokens: list[str], rng: random.Random) -> list[str]:
    shuffled = list(tokens)
    rng.shuffle(shuffled)
    return shuffled


def rewrite_blif(
    input_path: Path,
    output_path: Path,
    case: str,
    case_index: int,
    seed: int,
    mode: str,
) -> dict[str, object]:
    lines = logical_lines(input_path)
    rng = random.Random(seed + case_index * 1009)
    input_order: list[str] = []
    output_order: list[str] = []
    shuffled_inputs: list[str] = []
    shuffled_outputs: list[str] = []
    rendered: list[str] = [
        "# R7b port-order stress generated from " + case,
        "# Only .inputs/.outputs declaration order is shuffled; names and logic are preserved.",
    ]
    for line in lines:
        parts = line.split()
        if not parts:
            continue
        if parts[0] == ".model":
            rendered.append(f".model r7b_port_order_stress_{case}")
        elif parts[0] == ".inputs":
            input_order = parts[1:]
            shuffled_inputs = shuffle_ports(input_order, rng) if mode in {"both", "inputs"} else list(input_order)
            rendered.extend(wrap_directive(".inputs", shuffled_inputs))
        elif parts[0] == ".outputs":
            output_order = parts[1:]
            shuffled_outputs = shuffle_ports(output_order, rng) if mode in {"both", "outputs"} else list(output_order)
            rendered.extend(wrap_directive(".outputs", shuffled_outputs))
        else:
            rendered.append(line)
    if not any(line.startswith(".end") for line in lines):
        rendered.append(".end")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(rendered) + "\n", encoding="utf-8")
    return {
        "case": case,
        "mode": mode,
        "input_count": len(input_order),
        "output_count": len(output_order),
        "input_order_changed": input_order != shuffled_inputs,
        "output_order_changed": output_order != shuffled_outputs,
        "original_input_sample": " ".join(input_order[:8]),
        "shuffled_input_sample": " ".join(shuffled_inputs[:8]),
        "original_output_sample": " ".join(output_order[:8]),
        "shuffled_output_sample": " ".join(shuffled_outputs[:8]),
        "output_blif": str(output_path),
    }


def generate(args: argparse.Namespace) -> int:
    if args.out.exists() and args.clean:
        shutil.rmtree(args.out)
    rows: list[dict[str, object]] = []
    for idx, (case, input_path) in enumerate(discover_cases(args.cases), start=1):
        rows.append(rewrite_blif(input_path, args.out / case / "input.blif", case, idx, args.seed, args.mode))
    args.map_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.map_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} order-shuffled cases under {args.out}")
    print(f"wrote {args.map_csv}")
    return 0


def load_rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return {row["case"]: row for row in csv.DictReader(f)}


def as_int(row: dict[str, str], field: str) -> int:
    value = row.get(field, "")
    return int(float(value)) if value not in {"", "None", None} else 0


def as_bool(row: dict[str, str], field: str) -> bool:
    return str(row.get(field, "")).strip().lower() in {"1", "true", "yes"}


def compare(args: argparse.Namespace) -> int:
    clean = load_rows(args.clean_csv)
    stress = load_rows(args.stress_csv)
    rows: list[dict[str, object]] = []
    for case in sorted(clean):
        c = clean[case]
        s = stress.get(case, {})
        rows.append(
            {
                "case": case,
                "clean_pipeline": c.get("selected_pipeline", ""),
                "stress_pipeline": s.get("selected_pipeline", ""),
                "pipeline_match": c.get("selected_pipeline", "") == s.get("selected_pipeline", ""),
                "clean_nodes": as_int(c, "selected_nodes"),
                "stress_nodes": as_int(s, "selected_nodes"),
                "node_delta": as_int(s, "selected_nodes") - as_int(c, "selected_nodes"),
                "clean_levels": as_int(c, "selected_levels"),
                "stress_levels": as_int(s, "selected_levels"),
                "level_delta": as_int(s, "selected_levels") - as_int(c, "selected_levels"),
                "clean_cec_pass": as_bool(c, "cec_pass"),
                "stress_cec_pass": as_bool(s, "cec_pass"),
                "clean_status": c.get("status", ""),
                "stress_status": s.get("status", ""),
                "clean_fallback": 1 if c.get("status", "") == "fallback" else 0,
                "stress_fallback": 1 if s.get("status", "") == "fallback" else 0,
            }
        )

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)

    total_clean = sum(int(row["clean_nodes"]) for row in rows)
    total_stress = sum(int(row["stress_nodes"]) for row in rows)
    max_clean_level = max((int(row["clean_levels"]) for row in rows), default=0)
    max_stress_level = max((int(row["stress_levels"]) for row in rows), default=0)
    pipeline_mismatches = sum(1 for row in rows if not row["pipeline_match"])
    node_mismatches = sum(1 for row in rows if int(row["node_delta"]) != 0)
    level_mismatches = sum(1 for row in rows if int(row["level_delta"]) != 0)
    cec_failures = sum(1 for row in rows if not row["stress_cec_pass"])
    fallback_count = sum(int(row["stress_fallback"]) for row in rows)
    ok = not any([pipeline_mismatches, node_mismatches, level_mismatches, cec_failures, fallback_count])

    md = [
        "---",
        "research_id: R7b",
        "status: candidate-ready" if ok else "status: research-only",
        "baseline_tag: final_selector_v2_20260526",
        "baseline_commit: 0b0edf4890283e36fac943166a8c84a148c120b8",
        "branch: candidate/r7b-pure",
        "created: 2026-06-22",
        "updated: 2026-06-22",
        "affects_final: false",
        "primary_data:",
        f"  - {args.out_csv.as_posix()}",
        f"  - {args.stress_csv.as_posix()}",
        "---",
        "",
        "# R7b Port-Order Randomization Stress Summary",
        "",
        "## Objective",
        "",
        "Check whether the pure R7b candidate depends on `.inputs` or `.outputs` declaration order by rerunning full public 30 after deterministic PI/PO declaration-order shuffling.",
        "",
        "## Baseline",
        "",
        "The comparator is the clean R7b candidate reproduction in `reports/r7b_pure_clean_metrics.csv`: 44559 nodes, max level 21, CEC 30/30, fallback 0.",
        "",
        "## Commands",
        "",
        "```powershell",
        "python tools\\r7b_port_order_stress.py generate --cases data\\tc_public --out data\\tc_public_portorder_r7b_stress --map-csv results_candidate\\r7b_port_order_stress\\port_order_map.csv --seed 20260622 --mode both --clean",
        "python tools\\extract_blif_features.py --cases data\\tc_public_portorder_r7b_stress --csv results_candidate\\r7b_port_order_stress\\base_features.csv",
        "python tools\\extract_r7b_features.py --abc C:\\Users\\yy257\\abc_r7b_candidate_ninja_build2\\abc.exe --cases data\\tc_public_portorder_r7b_stress --base-features results_candidate\\r7b_port_order_stress\\base_features.csv --csv results_candidate\\r7b_port_order_stress\\features.csv --work-dir results_candidate\\r7b_port_order_stress\\feature_profile --timeout 120",
        "python tools\\eval_public.py --abc C:\\Users\\yy257\\abc_r7b_candidate_ninja_build2\\abc.exe --cases data\\tc_public_portorder_r7b_stress --selector configs\\final_selector_r7b_candidate.yaml --features results_candidate\\r7b_port_order_stress\\features.csv --pipelines configs\\pipelines_r7b_pure_candidate.yaml --out results_candidate\\r7b_port_order_stress\\public30 --csv reports\\r7b_port_order_stress_metrics.csv --opt-timeout 300 --cec-timeout 300 --stats-timeout 120",
        "python tools\\verify_all_cec.py --abc C:\\Users\\yy257\\abc_r7b_candidate_ninja_build2\\abc.exe --cases data\\tc_public_portorder_r7b_stress --outputs results_candidate\\r7b_port_order_stress\\public30 --log logs\\r7b_port_order_stress_cec.log --timeout 300",
        "python tools\\r7b_port_order_stress.py compare --clean-csv reports\\r7b_pure_clean_metrics.csv --stress-csv reports\\r7b_port_order_stress_metrics.csv --out-csv reports\\r7b_port_order_stress_compare.csv --report reports\\r7b_port_order_stress_summary.md",
        "```",
        "",
        "## Input Data",
        "",
        "- Original cases: `data/tc_public/*/input.blif`",
        "- Order-shuffled cases: `data/tc_public_portorder_r7b_stress/*/input.blif`",
        "- Order map: `results_candidate/r7b_port_order_stress/port_order_map.csv`",
        "",
        "## Results",
        "",
        f"- Stress total nodes: `{total_stress}`",
        f"- Clean total nodes: `{total_clean}`",
        f"- Stress max level: `{max_stress_level}`",
        f"- Clean max level: `{max_clean_level}`",
        f"- Pipeline mismatches: `{pipeline_mismatches}`",
        f"- Node mismatches: `{node_mismatches}`",
        f"- Level mismatches: `{level_mismatches}`",
        f"- Stress CEC failures in evaluator CSV: `{cec_failures}`",
        f"- Stress fallback count: `{fallback_count}`",
        "",
        "## Correctness",
        "",
        "Each stress output is CEC-checked against its order-shuffled input inside the evaluator; the independent CEC log is `logs/r7b_port_order_stress_cec.log`.",
        "",
        "## Risk",
        "",
        "This stress isolates declaration-order changes while preserving case directories and all PI/PO names. It complements the randomized case-name and port-name stresses.",
        "",
        "## Selector Eligibility",
        "",
        "Strengthened if all mismatches are zero: R7b remains selected by generated structural overlap features, not declaration order.",
        "",
        "## Conclusion",
        "",
        "promote-to-candidate" if ok else "research-only",
        "",
        "## Next Action",
        "",
        "Stop at the user approval point before formal merge or submit packaging.",
        "",
    ]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(md), encoding="utf-8")
    print(f"wrote {args.out_csv}")
    print(f"wrote {args.report}")
    print(
        f"total_stress={total_stress} max_level={max_stress_level} "
        f"mismatches pipeline/node/level={pipeline_mismatches}/{node_mismatches}/{level_mismatches} "
        f"cec_failures={cec_failures} fallback={fallback_count}"
    )
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_gen = sub.add_parser("generate")
    p_gen.add_argument("--cases", required=True, type=Path)
    p_gen.add_argument("--out", required=True, type=Path)
    p_gen.add_argument("--map-csv", required=True, type=Path)
    p_gen.add_argument("--seed", default=20260622, type=int)
    p_gen.add_argument("--mode", choices=["both", "inputs", "outputs"], default="both")
    p_gen.add_argument("--clean", action="store_true")
    p_cmp = sub.add_parser("compare")
    p_cmp.add_argument("--clean-csv", required=True, type=Path)
    p_cmp.add_argument("--stress-csv", required=True, type=Path)
    p_cmp.add_argument("--out-csv", required=True, type=Path)
    p_cmp.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    if args.cmd == "generate":
        return generate(args)
    if args.cmd == "compare":
        return compare(args)
    raise AssertionError(args.cmd)


if __name__ == "__main__":
    raise SystemExit(main())
