#!/usr/bin/env python3
"""Apply coarse feature-selector rules to BLIF feature CSV rows."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from eval_public import load_yaml_like


FORBIDDEN_EXACT_KEYS = {
    "pi_count",
    "po_count",
    "names_count",
    "cube_count",
    "line_count",
    "hash",
    "path",
    "case",
    "directory",
}


def as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def validate_selector(config: dict[str, Any]) -> None:
    for rule in config.get("rules", []):
        when = rule.get("when", {})
        for key in when:
            if key in FORBIDDEN_EXACT_KEYS or key.endswith("_eq"):
                raise ValueError(
                    f"selector rule '{rule.get('name', '<unnamed>')}' uses forbidden exact/fingerprint key: {key}"
                )


def match_rule(row: dict[str, str], when: dict[str, Any]) -> bool:
    for key, expected in when.items():
        if key.endswith("_in"):
            field = key[:-3]
            if row.get(field) not in set(map(str, expected)):
                return False
        elif key.endswith("_min"):
            field = key[:-4]
            if float(row.get(field, 0) or 0) < float(expected):
                return False
        elif key.endswith("_max"):
            field = key[:-4]
            if float(row.get(field, 0) or 0) > float(expected):
                return False
        else:
            actual = row.get(key)
            if isinstance(expected, bool):
                if as_bool(actual) != expected:
                    return False
            elif str(actual) != str(expected):
                return False
    return True


def choose(row: dict[str, str], config: dict[str, Any]) -> tuple[str, str]:
    for rule in config.get("rules", []):
        if match_rule(row, rule.get("when", {})):
            return str(rule["pipeline"]), str(rule.get("name", "rule"))
    return str(config.get("default_pipeline", "baseline")), "default"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    config = load_yaml_like(args.config)
    validate_selector(config)
    with args.features.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    out_rows = []
    for row in rows:
        pipeline, reason = choose(row, config)
        out_rows.append({**row, "selected_pipeline": pipeline, "selector_reason": reason})

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()) if out_rows else [])
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
