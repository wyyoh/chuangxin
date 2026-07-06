#!/usr/bin/env python3
"""Verify every case output with ABC CEC and write a combined log."""

from __future__ import annotations

import argparse
from pathlib import Path

from eval_public import discover_cases
from run_abc_case import run_cec


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--abc", required=True, type=Path)
    parser.add_argument("--cases", required=True, type=Path)
    parser.add_argument("--outputs", required=True, type=Path)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--timeout", type=float, default=300.0)
    args = parser.parse_args()

    args.log.parent.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    with args.log.open("w", encoding="utf-8", errors="replace") as combined:
        for case_name, input_blif in discover_cases(args.cases):
            output_blif = args.outputs / case_name / "output.blif"
            case_log = args.outputs / case_name / "logs" / "final_cec_verify.log"
            combined.write(f"===== {case_name} =====\n")
            if not output_blif.exists():
                combined.write(f"missing output: {output_blif}\n\n")
                failures.append(case_name)
                continue
            passed, result = run_cec(args.abc, input_blif, output_blif, args.timeout, case_log)
            combined.write(result.stdout)
            if result.stdout and not result.stdout.endswith("\n"):
                combined.write("\n")
            combined.write(result.stderr)
            if result.stderr and not result.stderr.endswith("\n"):
                combined.write("\n")
            combined.write(f"passed={passed} returncode={result.returncode} runtime_sec={result.runtime_sec:.6f}\n\n")
            if not passed:
                failures.append(case_name)
    if failures:
        print("CEC failures: " + ", ".join(failures))
        return 1
    print(f"all CEC checks passed; wrote {args.log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
