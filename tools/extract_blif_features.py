#!/usr/bin/env python3
"""Extract coarse BLIF structural features for selector rules."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from statistics import mean


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


def extract_one(path: Path, case: str) -> dict[str, object]:
    lines = logical_lines(path)
    pi_count = 0
    po_count = 0
    names_count = 0
    cube_count = 0
    fanins: list[int] = []
    in_names = False
    current_fanin = 0

    for line in lines:
        if line.startswith(".inputs"):
            pi_count += max(0, len(line.split()) - 1)
            in_names = False
        elif line.startswith(".outputs"):
            po_count += max(0, len(line.split()) - 1)
            in_names = False
        elif line.startswith(".names"):
            parts = line.split()
            current_fanin = max(0, len(parts) - 2)
            fanins.append(current_fanin)
            names_count += 1
            in_names = True
        elif line.startswith("."):
            in_names = False
        elif in_names:
            cube_count += 1

    max_fanin = max(fanins, default=0)
    avg_fanin = mean(fanins) if fanins else 0.0
    fanin0 = sum(1 for f in fanins if f == 0)
    fanin1 = sum(1 for f in fanins if f == 1)
    fanin2 = sum(1 for f in fanins if f == 2)
    fanin3_4 = sum(1 for f in fanins if 3 <= f <= 4)
    fanin5p = sum(1 for f in fanins if f >= 5)
    two_input_ratio = fanin2 / names_count if names_count else 0.0
    cube_per_name = cube_count / names_count if names_count else 0.0
    high_fanin_sop = max_fanin >= 5 or (fanin3_4 + fanin5p) / names_count >= 0.20 if names_count else False
    near_two_input_aig = two_input_ratio >= 0.85 and max_fanin <= 2
    scale_grade = bin_count(names_count, [100, 1000, 5000], ["tiny", "small", "medium", "large"])
    if names_count >= 5000 or cube_count >= 10000:
        runtime_size_bin = "runtime_large"
    elif names_count >= 1000 or cube_count >= 2000:
        runtime_size_bin = "runtime_medium"
    elif names_count >= 100 or cube_count >= 200:
        runtime_size_bin = "runtime_small"
    else:
        runtime_size_bin = "runtime_tiny"

    return {
        "case": case,
        "path": str(path),
        "pi_count": pi_count,
        "po_count": po_count,
        "names_count": names_count,
        "cube_count": cube_count,
        "max_fanin": max_fanin,
        "avg_fanin": f"{avg_fanin:.3f}",
        "fanin0_count": fanin0,
        "fanin1_count": fanin1,
        "fanin2_count": fanin2,
        "fanin3_4_count": fanin3_4,
        "fanin5p_count": fanin5p,
        "two_input_ratio": f"{two_input_ratio:.3f}",
        "cube_per_name": f"{cube_per_name:.3f}",
        "high_fanin_sop": str(bool(high_fanin_sop)).lower(),
        "near_two_input_aig": str(bool(near_two_input_aig)).lower(),
        "scale_grade": scale_grade,
        "pi_bin": bin_count(pi_count, [16, 64, 256], ["pi_tiny", "pi_small", "pi_medium", "pi_large"]),
        "po_bin": bin_count(po_count, [8, 32, 128], ["po_tiny", "po_small", "po_medium", "po_large"]),
        "outputs_bin": bin_count(po_count, [8, 32, 128], ["po_tiny", "po_small", "po_medium", "po_large"]),
        "names_bin": bin_count(names_count, [100, 1000, 5000], ["names_tiny", "names_small", "names_medium", "names_large"]),
        "cubes_bin": bin_count(cube_count, [200, 2000, 10000], ["cubes_tiny", "cubes_small", "cubes_medium", "cubes_large"]),
        "max_fanin_bin": bin_count(max_fanin, [3, 5, 9], ["fanin_le2", "fanin_3_4", "fanin_5_8", "fanin_9p"]),
        "average_fanin_bin": bin_float(
            avg_fanin,
            [1.7, 2.1, 3.1],
            ["avg_fanin_low", "avg_fanin_aigish", "avg_fanin_mid", "avg_fanin_high"],
        ),
        "two_input_ratio_bin": bin_float(
            two_input_ratio,
            [0.6, 0.85, 0.97, 0.995],
            ["two_ratio_low", "two_ratio_mid", "two_ratio_high", "two_ratio_very_high", "two_ratio_near_one"],
        ),
        "runtime_size_bin": runtime_size_bin,
    }


def discover_cases(cases_dir: Path) -> list[tuple[str, Path]]:
    cases: list[tuple[str, Path]] = []
    for child in sorted(cases_dir.iterdir(), key=lambda p: p.name):
        if child.is_dir() and (child / "input.blif").exists():
            cases.append((child.name, child / "input.blif"))
    return cases


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", required=True, type=Path)
    parser.add_argument("--csv", required=True, type=Path)
    args = parser.parse_args()

    rows = [extract_one(path, case) for case, path in discover_cases(args.cases)]
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    with args.csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
