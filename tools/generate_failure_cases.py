#!/usr/bin/env python3
"""Generate a markdown failure/fallback report from real metrics CSV."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    with args.metrics.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    cec_failures = [r for r in rows if str(r.get("cec_pass", "")).lower() != "true" and not r.get("status", "").startswith("fallback")]
    fallbacks = [r for r in rows if r.get("status", "").startswith("fallback")]

    lines = [
        "# Failure Cases",
        "",
        f"Source metrics: `{args.metrics}`",
        "",
        f"- Total cases: {len(rows)}",
        f"- Unresolved CEC failures: {len(cec_failures)}",
        f"- Fallback-selected cases: {len(fallbacks)}",
        "",
    ]
    if cec_failures:
        lines.extend(["## Unresolved CEC Failures", ""])
        for row in cec_failures:
            lines.append(f"- `{row['case']}`: requested `{row['requested_pipeline']}`, log `{row['log_dir']}`")
        lines.append("")
    if fallbacks:
        lines.extend(["## Fallbacks", ""])
        for row in fallbacks:
            lines.append(
                f"- `{row['case']}`: requested `{row['requested_pipeline']}` -> selected "
                f"`{row['selected_pipeline']}`; reason `{row['fallback_reason']}`"
            )
        lines.append("")
    if not cec_failures and not fallbacks:
        lines.append("No unresolved CEC failures and no fallback-selected cases in the final metrics.")
        lines.append("")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
