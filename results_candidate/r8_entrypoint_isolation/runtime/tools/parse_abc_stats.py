#!/usr/bin/env python3
"""Parse ABC `ps` output for AIG-oriented metrics."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


_INT_PATTERNS = {
    "inputs": re.compile(r"\bi/o\s*=\s*(\d+)\s*/\s*(\d+)"),
    "latches": re.compile(r"\blat\s*=\s*(\d+)"),
    "and": re.compile(r"\band\s*=\s*(\d+)"),
    "levels": re.compile(r"\blev\s*=\s*(\d+)"),
    "nodes": re.compile(r"\b(?:nd|nodes?)\s*=\s*(\d+)"),
    "aig": re.compile(r"\baig\s*=\s*(\d+)"),
}


def parse_ps_output(text: str) -> dict[str, Any]:
    """Return the last metric-looking line from ABC `ps` output.

    ABC prints different fields depending on the current network type. For this
    contest we mostly need AIG AND count and levels after `strash`, but the
    parser keeps a few related fields for diagnostics.
    """

    best: dict[str, Any] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if "i/o" not in line and "lev" not in line and "and" not in line:
            continue
        metrics: dict[str, Any] = {"ps_line": line}
        io_match = _INT_PATTERNS["inputs"].search(line)
        if io_match:
            metrics["inputs"] = int(io_match.group(1))
            metrics["outputs"] = int(io_match.group(2))
        for key in ("latches", "and", "levels", "nodes", "aig"):
            match = _INT_PATTERNS[key].search(line)
            if match:
                metrics[key] = int(match.group(1))
        if "and" in metrics:
            metrics["aig_nodes"] = metrics["and"]
        elif "aig" in metrics:
            metrics["aig_nodes"] = metrics["aig"]
        elif "nodes" in metrics:
            metrics["aig_nodes"] = metrics["nodes"]
        best = metrics
    return best


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=Path)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()

    metrics = parse_ps_output(args.log.read_text(encoding="utf-8", errors="replace"))
    if args.json:
        print(json.dumps(metrics, ensure_ascii=False, sort_keys=True))
    else:
        for key, value in metrics.items():
            print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
