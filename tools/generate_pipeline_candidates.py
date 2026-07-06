#!/usr/bin/env python3
"""Generate Pipeline Search 2.0 candidate CSVs from a structured YAML space."""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path
from typing import Any

import yaml


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def normalize_steps(steps: list[str] | str) -> str:
    """Normalize separators only; do not reorder or remove stateful repeats."""

    if isinstance(steps, str):
        raw_parts = steps.split(";")
    else:
        raw_parts = []
        for step in steps:
            raw_parts.extend(str(step).split(";"))
    parts = [part.strip() for part in raw_parts if part.strip()]
    return "; ".join(parts)


def stable_id(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def load_inventory(path: Path | None) -> tuple[dict[str, dict[str, str]], bool]:
    if path is None or not path.exists():
        return {}, False
    return {row["command"]: row for row in read_csv(path)}, True


def capability_status(requires: list[str], inventory: dict[str, dict[str, str]], inventory_present: bool) -> tuple[bool, str, str]:
    if not inventory_present:
        return False, "inventory_missing", "capability inventory missing; generated as core-safe only if no gated tokens"
    disabled_reasons: list[str] = []
    warnings: list[str] = []
    for token in requires:
        row = inventory.get(token)
        if row is None:
            warnings.append(f"{token}:not_in_inventory")
            continue
        category = row.get("failure_category", "")
        generation_status = row.get("generation_status", "")
        if generation_status == "disabled" or category in {"unavailable", "timeout", "crash"}:
            disabled_reasons.append(f"{token}:{category or generation_status}")
        elif category == "context_failed":
            warnings.append(f"{token}:context_dependent")
    if disabled_reasons:
        return True, "disabled_by_capability", "; ".join(disabled_reasons)
    return False, "enabled", "; ".join(warnings)


def bool_text(value: Any) -> str:
    return str(bool(value)).lower()


def build_rows(config: dict[str, Any], inventory: dict[str, dict[str, str]], inventory_present: bool, mode: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    metric_profile = str(config.get("metric_regression_policy", {}).get("name", "current_final_guard_v2"))
    cache_version = str(config.get("cache_policy", {}).get("version", "pipeline_search2_cache_v1"))
    schema_version = str(config.get("runner_result_schema", {}).get("version", "pipeline_search2_result_v1"))

    for family_name, family in (config.get("families") or {}).items():
        rules = family.get("generation_rules") or {}
        budget_key = "smoke_budget" if mode == "smoke" else "full_seed_budget"
        budget = int(rules.get(budget_key, len(family.get("candidates") or [])))
        selected = list(family.get("candidates") or [])[:budget]
        for index, cand in enumerate(selected, start=1):
            raw_steps = "; ".join(str(step).strip() for step in cand.get("steps", []) if str(step).strip())
            normalized = normalize_steps(cand.get("steps", []))
            if normalized in seen:
                continue
            seen.add(normalized)
            requires = [str(token) for token in cand.get("requires", [])]
            disabled, capability_status_text, capability_note = capability_status(requires, inventory, inventory_present)
            offline_only = bool(cand.get("offline_only", rules.get("offline_only", False)))
            selector_eligible = (
                bool(cand.get("selector_eligible", rules.get("final_selector_allowed", False)))
                and not offline_only
                and not disabled
            )
            rows.append(
                {
                    "mode": mode,
                    "candidate_kind": "pipeline",
                    "family": family_name,
                    "family_goal": family.get("goal", ""),
                    "pipeline_id": str(cand.get("id") or f"{family_name}_{index:03d}"),
                    "pipeline_hash": stable_id(normalized),
                    "raw_steps": raw_steps,
                    "normalized_steps": normalized,
                    "selector_eligible": bool_text(selector_eligible),
                    "offline_only": bool_text(offline_only),
                    "oracle_only": "false",
                    "oracle_note": "",
                    "run_eligible": bool_text(not disabled),
                    "disabled": bool_text(disabled),
                    "disable_reason": capability_status_text if disabled else "",
                    "capability_note": capability_note,
                    "requires_tokens": "|".join(requires),
                    "timeout_profile": str(cand.get("timeout_profile", rules.get("timeout_profile", "default"))),
                    "allowed_case_scales": "|".join(cand.get("allowed_case_scales", rules.get("allowed_case_scales", ["tiny", "small", "medium", "large"]))),
                    "max_sequence_length": rules.get("max_sequence_length", ""),
                    "allow_repeated_tokens": rules.get("allow_repeated_tokens", ""),
                    "normalization_policy": "trim whitespace; collapse semicolons; drop empty commands only; preserve order and repeats",
                    "metric_regression_profile": metric_profile,
                    "cache_key_contract_version": cache_version,
                    "runner_result_schema_version": schema_version,
                    "truncation_reason": "",
                }
            )

    if mode != "smoke":
        for cand in config.get("analysis_only_candidates", []) or []:
            rows.append(
                {
                    "mode": mode,
                    "candidate_kind": "oracle_analysis",
                    "family": str(cand.get("family", "oracle")),
                    "family_goal": cand.get("goal", ""),
                    "pipeline_id": str(cand.get("id", "best_family_per_case_oracle")),
                    "pipeline_hash": "",
                    "raw_steps": "",
                    "normalized_steps": "",
                    "selector_eligible": "false",
                    "offline_only": "true",
                    "oracle_only": "true",
                    "oracle_note": "ORACLE_ONLY_DO_NOT_SUBMIT",
                    "run_eligible": "false",
                    "disabled": "true",
                    "disable_reason": "oracle_only_do_not_submit",
                    "capability_note": "",
                    "requires_tokens": "",
                    "timeout_profile": "analysis_only",
                    "allowed_case_scales": "",
                    "max_sequence_length": "",
                    "allow_repeated_tokens": "",
                    "normalization_policy": "not applicable",
                    "metric_regression_profile": metric_profile,
                    "cache_key_contract_version": cache_version,
                    "runner_result_schema_version": schema_version,
                    "truncation_reason": "",
                }
            )
    return rows


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    fields = [
        "mode",
        "candidate_kind",
        "family",
        "family_goal",
        "pipeline_id",
        "pipeline_hash",
        "raw_steps",
        "normalized_steps",
        "selector_eligible",
        "offline_only",
        "oracle_only",
        "oracle_note",
        "run_eligible",
        "disabled",
        "disable_reason",
        "capability_note",
        "requires_tokens",
        "timeout_profile",
        "allowed_case_scales",
        "max_sequence_length",
        "allow_repeated_tokens",
        "normalization_policy",
        "metric_regression_profile",
        "cache_key_contract_version",
        "runner_result_schema_version",
        "truncation_reason",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--space", required=True, type=Path)
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--mode", choices=["smoke", "full"], default="smoke")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--full-seed-out", type=Path)
    args = parser.parse_args()

    config = yaml.safe_load(args.space.read_text(encoding="utf-8")) or {}
    inventory, inventory_present = load_inventory(args.inventory)

    rows = build_rows(config, inventory, inventory_present, "smoke" if args.mode == "smoke" else "full")
    write_rows(args.out, rows)
    if args.full_seed_out:
        write_rows(args.full_seed_out, build_rows(config, inventory, inventory_present, "full_seed"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
