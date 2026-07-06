#!/usr/bin/env python3
"""Reproduce CEC checks for a generated submit directory."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--submit", required=True, type=Path)
    parser.add_argument("--cases", required=True, type=Path)
    parser.add_argument("--abc", required=True, type=Path)
    parser.add_argument("--log", required=True, type=Path)
    args = parser.parse_args()

    cmd = [
        sys.executable,
        str(args.submit / "tools" / "verify_all_cec.py"),
        "--abc",
        str(args.abc),
        "--cases",
        str(args.cases),
        "--outputs",
        str(args.submit / "results" / "final_public"),
        "--log",
        str(args.log),
    ]
    args.log.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(cmd, text=True)
    for cache_dir in (args.submit / "tools").glob("__pycache__"):
        shutil.rmtree(cache_dir, ignore_errors=True)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
