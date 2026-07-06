#!/usr/bin/env python3
"""Evaluate all public BLIF cases with a configured pipeline or selector."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

from run_abc_case import CaseResult, normalize_pipeline_steps, run_case, write_csv


def load_yaml_like(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        return yaml.safe_load(text) or {}

    def parse_scalar(value: str) -> Any:
        value = value.strip()
        if not value:
            return ""
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            if not inner:
                return []
            return [parse_scalar(part) for part in inner.split(",")]
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            return value[1:-1]
        lowered = value.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        return value

    # Minimal fallback for the simple pipeline and selector configs used here.
    data: dict[str, Any] = {}
    section: str | None = None
    current_pipeline: str | None = None
    current_rule: dict[str, Any] | None = None
    in_when = False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line:
            continue
        stripped = line.strip()
        indent = len(line) - len(line.lstrip(" "))
        if indent == 0 and stripped.endswith(":"):
            section = stripped[:-1]
            data.setdefault(section, [] if section == "rules" else {})
            current_pipeline = None
            current_rule = None
            in_when = False
        elif section == "pipelines" and indent == 2 and stripped.endswith(":"):
            current_pipeline = stripped[:-1]
            data.setdefault("pipelines", {})[current_pipeline] = {}
        elif section == "pipelines" and indent >= 4 and current_pipeline:
            key, _, value = line.strip().partition(":")
            data["pipelines"][current_pipeline][key] = parse_scalar(value)
        elif section == "rules" and indent == 2 and stripped.startswith("- "):
            current_rule = {}
            data.setdefault("rules", []).append(current_rule)
            current_pipeline = None
            in_when = False
            rest = stripped[2:].strip()
            if rest:
                key, _, value = rest.partition(":")
                current_rule[key] = parse_scalar(value)
        elif section == "rules" and current_rule is not None and indent == 4:
            if stripped == "when:":
                current_rule.setdefault("when", {})
                in_when = True
            elif ":" in stripped:
                key, _, value = stripped.partition(":")
                current_rule[key] = parse_scalar(value)
                in_when = False
        elif section == "rules" and current_rule is not None and in_when and indent >= 6 and ":" in stripped:
            key, _, value = stripped.partition(":")
            current_rule.setdefault("when", {})[key] = parse_scalar(value)
        elif indent == 0 and ":" in stripped:
            key, _, value = stripped.partition(":")
            data[key] = parse_scalar(value)
    return data


def discover_cases(cases_dir: Path) -> list[tuple[str, Path]]:
    cases: list[tuple[str, Path]] = []
    for child in sorted(cases_dir.iterdir(), key=lambda p: p.name):
        if not child.is_dir():
            continue
        input_blif = child / "input.blif"
        if input_blif.exists():
            cases.append((child.name, input_blif))
    return cases


def load_case_list(path: Path) -> set[str]:
    cases: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        cases.add(Path(line).name)
    return cases


def load_pipeline_steps(config: dict[str, Any], name: str) -> str:
    pipelines = config.get("pipelines", {})
    if name not in pipelines:
        raise KeyError(f"pipeline not found in config: {name}")
    entry = pipelines[name] or {}
    return normalize_pipeline_steps(entry.get("steps", ""))


def _as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _match_selector_rule(row: dict[str, Any], when: dict[str, Any]) -> bool:
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
                if _as_bool(actual) != expected:
                    return False
            elif str(actual) != str(expected):
                return False
    return True


def selector_choice(selector_config: dict[str, Any], features_by_case: dict[str, dict[str, Any]], case: str) -> str:
    default = selector_config.get("default_pipeline") or selector_config.get("default") or "baseline"
    row = features_by_case.get(case, {})
    for rule in selector_config.get("rules", []):
        if _match_selector_rule(row, rule.get("when", {})):
            return str(rule["pipeline"])
    return str(default)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--abc", required=True, type=Path)
    parser.add_argument("--cases", required=True, type=Path)
    parser.add_argument("--case-list", type=Path)
    parser.add_argument("--pipeline")
    parser.add_argument("--selector", type=Path)
    parser.add_argument("--pipelines", type=Path, default=Path("configs/pipelines.yaml"))
    parser.add_argument("--features", type=Path, default=Path("reports/features.csv"))
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--baseline-dir", type=Path, default=Path("results/baseline"))
    parser.add_argument("--opt-timeout", type=float, default=300.0)
    parser.add_argument("--cec-timeout", type=float, default=300.0)
    parser.add_argument("--stats-timeout", type=float, default=120.0)
    args = parser.parse_args()

    if bool(args.pipeline) == bool(args.selector):
        parser.error("provide exactly one of --pipeline or --selector")

    config = load_yaml_like(args.pipelines)
    baseline_steps = load_pipeline_steps(config, "baseline")
    selector_config: dict[str, Any] = {}
    features_by_case: dict[str, dict[str, Any]] = {}
    if args.selector:
        selector_config = load_yaml_like(args.selector)
        if args.features and args.features.exists():
            with args.features.open(newline="", encoding="utf-8") as f:
                features_by_case = {row["case"]: row for row in csv.DictReader(f)}

    cases = discover_cases(args.cases)
    if args.case_list:
        requested_cases = load_case_list(args.case_list)
        available_cases = {case_name for case_name, _ in cases}
        missing_cases = sorted(requested_cases - available_cases)
        if missing_cases:
            print(
                f"case-list contains cases not found under {args.cases}: {', '.join(missing_cases)}",
                file=sys.stderr,
            )
            return 2
        cases = [(case_name, input_blif) for case_name, input_blif in cases if case_name in requested_cases]
    if not cases:
        print(f"no cases found under {args.cases}", file=sys.stderr)
        return 2

    rows: list[CaseResult] = []
    args.out.mkdir(parents=True, exist_ok=True)
    for case_name, input_blif in cases:
        if args.pipeline:
            pipeline_name = args.pipeline
        else:
            pipeline_name = selector_choice(selector_config, features_by_case, case_name)
        pipeline_steps = load_pipeline_steps(config, pipeline_name)
        case_out_dir = args.out / case_name
        output_blif = case_out_dir / "output.blif"
        baseline_output = args.baseline_dir / case_name / "output.blif"
        log_dir = case_out_dir / "logs"
        print(f"[{case_name}] pipeline={pipeline_name}")
        result = run_case(
            args.abc,
            input_blif,
            output_blif,
            pipeline_name,
            pipeline_steps,
            baseline_output,
            baseline_steps,
            log_dir,
            case_name,
            {"opt": args.opt_timeout, "cec": args.cec_timeout, "stats": args.stats_timeout},
        )
        rows.append(result)
        print(
            f"[{case_name}] status={result.status} selected={result.selected_pipeline} "
            f"nodes={result.selected_nodes} levels={result.selected_levels}"
        )

    write_csv(args.csv, rows)
    print(f"wrote {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
