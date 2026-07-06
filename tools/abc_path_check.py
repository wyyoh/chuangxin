#!/usr/bin/env python3
"""Validate an ABC executable path."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--abc", required=True, help="Path to ABC executable")
    args = parser.parse_args()

    abc = os.path.abspath(args.abc)
    if not os.path.exists(abc):
        print(f"ABC executable not found: {abc}", file=sys.stderr)
        return 2
    if not os.path.isfile(abc):
        print(f"ABC path is not a file: {abc}", file=sys.stderr)
        return 2

    proc = subprocess.run([abc, "-c", "help"], text=True, capture_output=True, timeout=20)
    print(proc.stdout[:2000])
    if proc.returncode != 0:
        print(proc.stderr, file=sys.stderr)
        return proc.returncode
    print(f"ABC OK: {abc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

