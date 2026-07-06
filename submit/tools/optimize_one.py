#!/usr/bin/env python3
"""Single-case optimizer wrapper for the R30b guarded ODC release path.

This wrapper keeps the public hidden-case interface stable while running the v7
optimizer first, then trying a guarded R30b ODC-style post-pass only on coarse
multi-output structural buckets. The post-pass is accepted only after CEC, node
decrease, and level non-regression.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from optimize_one_r28_gated_r27_candidate import DEFAULT_POSTPASS as DEFAULT_R28_POSTPASS
from optimize_one_r29_postpass_candidate import DEFAULT_R29_POSTPASS
from optimize_one_r30b_release import DEFAULT_R30_POSTPASS, optimize_one


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--abc", required=True, type=Path)
    parser.add_argument("--input", default=Path("input.blif"), type=Path)
    parser.add_argument("--output", default=Path("output.blif"), type=Path)
    parser.add_argument("--selector", default=Path("configs/final_selector.yaml"), type=Path)
    parser.add_argument("--pipelines", default=Path("configs/pipelines.yaml"), type=Path)
    parser.add_argument("--r28-pipelines", default=Path("configs/pipelines_r28_gated_r27.yaml"), type=Path)
    parser.add_argument("--r28-postpass", default=DEFAULT_R28_POSTPASS)
    parser.add_argument("--r29-pipelines", default=Path("configs/pipelines_r29_postpass_candidate.yaml"), type=Path)
    parser.add_argument("--r29-postpass", default=DEFAULT_R29_POSTPASS)
    parser.add_argument("--r30-pipelines", default=Path("configs/pipelines.yaml"), type=Path)
    parser.add_argument("--r30-postpass", default=DEFAULT_R30_POSTPASS)
    parser.add_argument("--work-dir", default=Path("work/optimize_one"), type=Path)
    parser.add_argument("--metrics-json", type=Path)
    parser.add_argument("--seed", default=20260622, type=int)
    parser.add_argument("--variant-index", default=1, type=int)
    parser.add_argument("--modes", default="clean,inputs,outputs,both")
    parser.add_argument("--case-label", default="input")
    parser.add_argument("--opt-timeout", type=float, default=300.0)
    parser.add_argument("--post-opt-timeout", type=float, default=90.0)
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
