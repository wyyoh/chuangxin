#!/usr/bin/env python3
"""Final single-case optimizer wrapper for the R8 candidate path.

This candidate wrapper keeps the public hidden-case interface stable while
using the R8 deterministic port-order choose-best policy internally. It builds
coarse BLIF and R7b overlap features, selects one coarse pipeline, tries clean
and declaration-order variants, verifies every accepted output by CEC against
the original input, and writes the lowest-node level-safe result.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from optimize_one_r8_order_choosebest import optimize_one


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--abc", required=True, type=Path)
    parser.add_argument("--input", default=Path("input.blif"), type=Path)
    parser.add_argument("--output", default=Path("output.blif"), type=Path)
    parser.add_argument("--selector", default=Path("configs/final_selector.yaml"), type=Path)
    parser.add_argument("--pipelines", default=Path("configs/pipelines.yaml"), type=Path)
    parser.add_argument("--work-dir", default=Path("work/optimize_one"), type=Path)
    parser.add_argument("--metrics-json", type=Path)
    parser.add_argument("--seed", default=20260622, type=int)
    parser.add_argument("--variant-index", default=1, type=int)
    parser.add_argument("--modes", default="clean,inputs,outputs,both")
    parser.add_argument("--case-label", default="input")
    parser.add_argument("--opt-timeout", type=float, default=300.0)
    parser.add_argument("--cec-timeout", type=float, default=300.0)
    parser.add_argument("--stats-timeout", type=float, default=120.0)
    args = parser.parse_args()

    payload = optimize_one(args)
    if args.metrics_json:
        args.metrics_json.parent.mkdir(parents=True, exist_ok=True)
        args.metrics_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if payload.get("cec_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
