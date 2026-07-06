#!/usr/bin/env python3
"""Check R11S release-packaging readiness without creating submit artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


EXPECTED = {
    "nodes": 41004,
    "max_level": 20,
    "total_levels": 285,
    "cases": 30,
    "cec_pass": 30,
    "fallback": 0,
    "inner_fallback": 0,
    "bad_entry": 0,
    "abc_sha256": "85F59E6291A1C4B10B757BF163D14D2152EAA974B21BC6F4E13F44EC49969805",
    "old_formal_submit_sha256": "4B6236AF057009318EA50E39FFC43FFA3A74708B49A07C2F08FD386AB6D1AF8A",
}


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def add(checks: list[Check], name: str, ok: bool, detail: str) -> None:
    checks.append(Check(name=name, ok=bool(ok), detail=detail))


def as_int(row: dict[str, Any], key: str) -> int:
    return int(float(row.get(key) or 0))


def load_metrics(path: Path) -> dict[str, Any]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return {
        "rows": len(rows),
        "nodes": sum(as_int(row, "selected_nodes") for row in rows),
        "max_level": max((as_int(row, "selected_levels") for row in rows), default=0),
        "total_levels": sum(as_int(row, "selected_levels") for row in rows),
        "cec_pass": sum(1 for row in rows if str(row.get("cec_pass", "")).lower() == "true"),
        "fallback": sum(1 for row in rows if row.get("status") != "selected_candidate" or row.get("fallback_reason")),
        "inner_fallback": sum(as_int(row, "inner_fallback_count") for row in rows),
        "bad_entry": sum(1 for row in rows if as_int(row, "entry_returncode") != 0),
    }


def count_log(path: Path) -> dict[str, int]:
    text = path.read_text(encoding="utf-8", errors="replace")
    non_rc_cannot_open = 0
    for line in text.splitlines():
        if "Cannot open" in line and "abc.rc" not in line:
            non_rc_cannot_open += 1
    return {
        "equivalent": text.count("Networks are equivalent"),
        "not_equivalent": text.count("NOT EQUIVALENT"),
        "non_rc_cannot_open": non_rc_cannot_open,
        "failed": text.lower().count("failed"),
        "error": text.lower().count("error"),
    }


def run_abc_help(abc: Path, command: str, expected: str) -> tuple[bool, str]:
    try:
        completed = subprocess.run([str(abc), "-c", command], text=True, capture_output=True, timeout=20)
    except Exception as exc:  # pragma: no cover - diagnostic path
        return False, f"{type(exc).__name__}: {exc}"
    combined = (completed.stdout or "") + (completed.stderr or "")
    ok = completed.returncode == 0 and expected in combined
    return ok, f"returncode={completed.returncode}; has_expected={expected in combined}"


def write_markdown(path: Path, checks: list[Check], payload: dict[str, Any]) -> None:
    passed = sum(1 for check in checks if check.ok)
    lines = [
        "---",
        "research_id: R11S-GIA-DISTILLED-STABLE",
        "status: candidate-ready",
        "baseline_tag: final_selector_v3_20260622",
        "baseline_commit: 7b20c8c4904682cd905f7afb68d5a4a822c4f8d6",
        "branch: release/r11-preflight",
        "created: 2026-06-23",
        "updated: 2026-06-23",
        "affects_final: false",
        "supersedes: []",
        "superseded_by: []",
        "primary_data:",
        "  - reports/r11s_release_readiness_check.json",
        "---",
        "",
        "# R11S Release Readiness Check",
        "",
        "## Objective",
        "",
        "Run a repeatable pre-release checker over R11S candidate evidence without regenerating `submit/` or `submit_sharecone.zip`.",
        "",
        "## Baseline",
        "",
        "- Formal baseline: `final_selector_v3_20260622`",
        "- R11S expected public metrics: `41004` nodes, max level `20`, total levels `285`, CEC `30/30`, fallback `0`",
        "",
        "## Commands",
        "",
        "```powershell",
        "python tools\\check_r11s_release_readiness.py --json-out reports\\r11s_release_readiness_check.json --md-out reports\\r11s_release_readiness_check.md",
        "```",
        "",
        "## Input Data",
        "",
        f"- Metrics: `{payload['paths']['metrics']}`",
        f"- Full CEC log: `{payload['paths']['cec_log']}`",
        f"- Packaged CEC log: `{payload['paths']['packaged_cec_log']}`",
        f"- ABC: `{payload['paths']['abc']}`",
        "",
        "## Results",
        "",
        f"- Checks passed: `{passed}/{len(checks)}`",
        "",
        "| Check | Status | Detail |",
        "| --- | --- | --- |",
    ]
    for check in checks:
        status = "PASS" if check.ok else "FAIL"
        detail = check.detail.replace("|", "\\|")
        lines.append(f"| `{check.name}` | `{status}` | {detail} |")
    lines.extend(
        [
            "",
            "## Correctness",
            "",
            "The checker is read-only. It validates generated metrics, CEC logs, hashes, package-script dependencies, and selector/pipeline contents.",
            "",
            "## Risk",
            "",
            "A passing readiness check does not create a final release. The protected `submit/` directory and `submit_sharecone.zip` still require an explicit release packaging phase.",
            "",
            "## Selector Eligibility",
            "",
            "The check confirms that the R11S selector/pipeline files contain the expected coarse GIA/deepsyn, R10, R9, and R7b entries without public case identity tokens.",
            "",
            "## Conclusion",
            "",
            "Decision: `promote-to-candidate`" if all(check.ok for check in checks) else "Decision: `continue`",
            "",
            "## Next Action",
            "",
            "If approved, run the final release packaging phase and verify the new archive from inside `submit/`.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--abc", default=Path("submit/bin/abc.exe"), type=Path)
    parser.add_argument("--metrics", default=Path("reports/r11s_packaging_dryrun_full30_metrics.csv"), type=Path)
    parser.add_argument("--cec-log", default=Path("logs/r11s_packaging_dryrun_full30_cec.log"), type=Path)
    parser.add_argument("--packaged-cec-log", default=Path("logs/r11s_packaging_dryrun_reproduce_cec.log"), type=Path)
    parser.add_argument("--packaged-cec-inside-log", default=Path("logs/r11s_packaging_dryrun_reproduce_cec_inside.log"), type=Path)
    parser.add_argument("--packaged-singlecase-cec-log", default=Path("logs/r11s_packaged_tc10_cec.log"), type=Path)
    parser.add_argument("--failure-cases", default=Path("reports/r11s_packaging_dryrun_failure_cases.md"), type=Path)
    parser.add_argument("--scoreboard", default=Path("reports/final_scoreboard.xlsx"), type=Path)
    parser.add_argument("--selector", default=Path("configs/final_selector.yaml"), type=Path)
    parser.add_argument("--pipelines", default=Path("configs/pipelines.yaml"), type=Path)
    parser.add_argument("--package-script", default=Path("tools/package_submit.py"), type=Path)
    parser.add_argument("--old-submit-zip", default=Path("submit_sharecone.zip"), type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--md-out", type=Path)
    args = parser.parse_args()

    checks: list[Check] = []
    paths = {key: str(value) for key, value in vars(args).items() if isinstance(value, Path)}

    for name in (
        "abc",
        "metrics",
        "cec_log",
        "packaged_cec_log",
        "packaged_cec_inside_log",
        "packaged_singlecase_cec_log",
        "failure_cases",
        "scoreboard",
        "selector",
        "pipelines",
        "package_script",
    ):
        path = getattr(args, name)
        add(checks, f"{name}_exists", path.exists(), str(path))

    metrics: dict[str, Any] = {}
    if args.metrics.exists():
        metrics = load_metrics(args.metrics)
        for key in ("rows", "nodes", "max_level", "total_levels", "cec_pass", "fallback", "inner_fallback", "bad_entry"):
            expected_key = "cases" if key == "rows" else key
            add(checks, f"metrics_{key}", metrics[key] == EXPECTED[expected_key], f"{metrics[key]} expected {EXPECTED[expected_key]}")

    log_payload: dict[str, dict[str, int]] = {}
    for label, path, expected_equiv in (
        ("full_cec", args.cec_log, 30),
        ("packaged_cec", args.packaged_cec_log, 30),
        ("packaged_cec_inside", args.packaged_cec_inside_log, 30),
        ("packaged_singlecase_cec", args.packaged_singlecase_cec_log, 1),
    ):
        if path.exists():
            counts = count_log(path)
            log_payload[label] = counts
            ok = counts["equivalent"] == expected_equiv and counts["not_equivalent"] == 0 and counts["non_rc_cannot_open"] == 0
            add(checks, f"{label}_equivalent", ok, str(counts))

    abc_hash = ""
    if args.abc.exists():
        abc_hash = sha256(args.abc)
        add(checks, "abc_hash", abc_hash == EXPECTED["abc_sha256"], abc_hash)
        ok, detail = run_abc_help(args.abc, "r7win -h", "usage: r7win")
        add(checks, "abc_r7win_help", ok, detail)
        ok, detail = run_abc_help(args.abc, "&deepsyn -h", "&deepsyn")
        add(checks, "abc_deepsyn_help", ok, detail)

    if args.failure_cases.exists():
        text = args.failure_cases.read_text(encoding="utf-8", errors="replace")
        ok = "Unresolved CEC failures: 0" in text and "Fallback-selected cases: 0" in text
        add(checks, "failure_cases_clean", ok, "unresolved=0 fallback=0" if ok else "missing zero-failure summary")

    if args.scoreboard.exists():
        add(checks, "scoreboard_nonempty", args.scoreboard.stat().st_size > 0, f"bytes={args.scoreboard.stat().st_size}")

    if args.selector.exists():
        selector_text = args.selector.read_text(encoding="utf-8", errors="replace")
        active_selector = "\n".join(line for line in selector_text.splitlines() if not line.strip().startswith("#"))
        required = (
            "r11_deepsyn_large_low_pi_small_po",
            "r11_deepsyn_small_small_pi_medium_po",
            "medium_runtime_fraig_cleanup",
            "large_smallpo_fraig_cleanup",
            "r7b_eligible",
        )
        missing = [token for token in required if token not in active_selector]
        forbidden = [token for token in ("tc_public", "hash", "directory") if token in active_selector.lower()]
        add(checks, "selector_r11s_rules", not missing and not forbidden, f"missing={missing}; forbidden={forbidden}")

    if args.pipelines.exists():
        pipeline_text = args.pipelines.read_text(encoding="utf-8", errors="replace")
        required = (
            "r11_gia_deepsyn_tiny",
            "&deepsyn -I 1 -J 20 -T 5",
            "r10_medium_fraig_cleanup",
            "r9_dc2_fraig_cleanup",
            "r7b_r7win_fraig_high",
        )
        missing = [token for token in required if token not in pipeline_text]
        add(checks, "pipelines_r11s_present", not missing, f"missing={missing}")

    if args.package_script.exists():
        script = args.package_script.read_text(encoding="utf-8", errors="replace")
        required = (
            "optimize_one_r8_order_choosebest.py",
            "extract_r7b_features.py",
            "r7b_port_order_stress.py",
            "--metrics",
            "--scoreboard",
            "--cec-log",
            "--failure-cases",
        )
        missing = [token for token in required if token not in script]
        add(checks, "package_submit_runtime_deps", not missing, f"missing={missing}")

    zip_hash = ""
    if args.old_submit_zip.exists():
        zip_hash = sha256(args.old_submit_zip)
        add(checks, "old_formal_zip_unchanged", zip_hash == EXPECTED["old_formal_submit_sha256"], zip_hash)

    payload = {
        "status": "pass" if all(check.ok for check in checks) else "fail",
        "expected": EXPECTED,
        "paths": paths,
        "metrics": metrics,
        "logs": log_payload,
        "abc_sha256": abc_hash,
        "old_submit_zip_sha256": zip_hash,
        "checks": [check.__dict__ for check in checks],
    }

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    if args.md_out:
        write_markdown(args.md_out, checks, payload)
    print(json.dumps({"status": payload["status"], "passed": sum(c.ok for c in checks), "total": len(checks)}, sort_keys=True))
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
