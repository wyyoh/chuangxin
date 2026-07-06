#!/usr/bin/env python3
"""Check R8 release-packaging readiness without creating submit artifacts."""

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
    "nodes": 43775,
    "max_level": 21,
    "cases": 30,
    "cec_pass": 30,
    "fallback": 0,
    "inner_fallback": 0,
    "abc_sha256": "85F59E6291A1C4B10B757BF163D14D2152EAA974B21BC6F4E13F44EC49969805",
    "release_preflight_submit_sha256": "F2D23DF5CE280304EA3C18F8C713AFBF06577A31E2BA8B3E11E5D2C2B00B8FAD",
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


def load_metrics(path: Path) -> dict[str, Any]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return {
        "rows": len(rows),
        "nodes": sum(int(row.get("selected_nodes") or 0) for row in rows),
        "max_level": max((int(row.get("selected_levels") or 0) for row in rows), default=0),
        "cec_pass": sum(1 for row in rows if str(row.get("cec_pass", "")).lower() == "true"),
        "fallback": sum(1 for row in rows if row.get("status") != "selected_candidate" or row.get("fallback_reason")),
        "inner_fallback": sum(int(row.get("inner_fallback_count") or 0) for row in rows),
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
    }


def run_abc_help(abc: Path) -> tuple[bool, str]:
    try:
        completed = subprocess.run(
            [str(abc), "-c", "r7win -h"],
            text=True,
            capture_output=True,
            timeout=15,
        )
    except Exception as exc:  # pragma: no cover - diagnostic path
        return False, f"{type(exc).__name__}: {exc}"
    combined = (completed.stdout or "") + (completed.stderr or "")
    ok = completed.returncode == 0 and "usage: r7win" in combined and "multi-output window command" in combined
    return ok, f"returncode={completed.returncode}; has_usage={'usage: r7win' in combined}"


def write_markdown(path: Path, checks: list[Check], payload: dict[str, Any]) -> None:
    passed = sum(1 for check in checks if check.ok)
    lines = [
        "---",
        "research_id: R8-READINESS-CHECK",
        "status: candidate-ready",
        "baseline_tag: final_selector_v2_20260526",
        "baseline_commit: 0b0edf4890283e36fac943166a8c84a148c120b8",
        "branch: release/r8-preflight",
        "created: 2026-06-22",
        "updated: 2026-06-22",
        "affects_final: false",
        "supersedes: []",
        "superseded_by: []",
        "primary_data:",
        "  - reports/r8_release_readiness_check.json",
        "---",
        "",
        "# R8 Release Readiness Check",
        "",
        "## Objective",
        "",
        "Run a repeatable pre-release checker over the R8 candidate evidence without generating `submit/` or `submit_sharecone.zip`.",
        "",
        "## Baseline",
        "",
        "- Formal baseline: `final_selector_v2_20260526`",
        "- R8 expected public metrics: `43775` nodes, max level `21`, CEC `30/30`, fallback `0`",
        "",
        "## Commands",
        "",
        "```powershell",
        "python tools\\check_r8_release_readiness.py --json-out reports\\r8_release_readiness_check.json --md-out reports\\r8_release_readiness_check.md",
        "```",
        "",
        "## Input Data",
        "",
        f"- Metrics: `{payload['paths']['metrics']}`",
        f"- CEC log: `{payload['paths']['cec_log']}`",
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
            "The checker is read-only. It validates already-generated metrics, CEC logs, hashes, and packaging-script arguments.",
            "",
            "## Risk",
            "",
            "A passing readiness check does not replace the official release phase. The protected `submit/` directory and `submit_sharecone.zip` still require explicit user approval.",
            "",
            "## Selector Eligibility",
            "",
            "The check confirms that the R8 selector/pipeline files still contain the expected coarse `r7b_eligible` and `r7win` release-preflight entries.",
            "",
            "## Conclusion",
            "",
            "Decision: `promote-to-candidate`" if all(check.ok for check in checks) else "Decision: `continue`",
            "",
            "## Next Action",
            "",
            "Ask the user for explicit approval before official `submit/` regeneration and `submit_sharecone.zip` creation.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--abc", default=Path(r"C:\Users\yy257\abc_r7b_candidate_ninja_build2\abc.exe"), type=Path)
    parser.add_argument("--metrics", default=Path("reports/r8_formal_names_preflight_metrics.csv"), type=Path)
    parser.add_argument("--cec-log", default=Path("logs/r8_formal_names_preflight_cec.log"), type=Path)
    parser.add_argument("--explicit-cec-log", default=Path("logs/r8_packaging_explicit_reports_cec.log"), type=Path)
    parser.add_argument("--failure-cases", default=Path("reports/r8_packaging_failure_cases.md"), type=Path)
    parser.add_argument("--scoreboard", default=Path("reports/r8_packaging_final_scoreboard.xlsx"), type=Path)
    parser.add_argument("--selector", default=Path("configs/final_selector.yaml"), type=Path)
    parser.add_argument("--pipelines", default=Path("configs/pipelines.yaml"), type=Path)
    parser.add_argument("--package-script", default=Path("tools/package_submit.py"), type=Path)
    parser.add_argument("--release-preflight-submit-zip", default=Path("submit_sharecone.zip"), type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--md-out", type=Path)
    args = parser.parse_args()

    checks: list[Check] = []
    paths = {key: str(value) for key, value in vars(args).items() if isinstance(value, Path)}

    for name in ("abc", "metrics", "cec_log", "explicit_cec_log", "failure_cases", "scoreboard", "selector", "pipelines", "package_script"):
        path = getattr(args, name)
        add(checks, f"{name}_exists", path.exists(), str(path))

    if args.metrics.exists():
        metrics = load_metrics(args.metrics)
        for key, expected_key in (
            ("rows", "cases"),
            ("nodes", "nodes"),
            ("max_level", "max_level"),
            ("cec_pass", "cec_pass"),
            ("fallback", "fallback"),
            ("inner_fallback", "inner_fallback"),
        ):
            add(checks, f"metrics_{key}", metrics[key] == EXPECTED[expected_key], f"{metrics[key]} expected {EXPECTED[expected_key]}")
    else:
        metrics = {}

    if args.cec_log.exists():
        counts = count_log(args.cec_log)
        add(checks, "formal_name_cec_30", counts["equivalent"] == 30 and counts["not_equivalent"] == 0 and counts["non_rc_cannot_open"] == 0, str(counts))
    else:
        counts = {}

    if args.explicit_cec_log.exists():
        explicit_counts = count_log(args.explicit_cec_log)
        add(checks, "explicit_package_cec_30", explicit_counts["equivalent"] == 30 and explicit_counts["not_equivalent"] == 0 and explicit_counts["non_rc_cannot_open"] == 0, str(explicit_counts))
    else:
        explicit_counts = {}

    if args.abc.exists():
        abc_hash = sha256(args.abc)
        add(checks, "abc_hash", abc_hash == EXPECTED["abc_sha256"], abc_hash)
        ok, detail = run_abc_help(args.abc)
        add(checks, "abc_r7win_help", ok, detail)
    else:
        abc_hash = ""

    if args.failure_cases.exists():
        text = args.failure_cases.read_text(encoding="utf-8", errors="replace")
        ok = "Unresolved CEC failures: 0" in text and "Fallback-selected cases: 0" in text
        add(checks, "failure_cases_clean", ok, "unresolved=0 fallback=0" if ok else "missing zero-failure summary")

    if args.scoreboard.exists():
        add(checks, "scoreboard_nonempty", args.scoreboard.stat().st_size > 0, f"bytes={args.scoreboard.stat().st_size}")

    if args.selector.exists():
        selector_text = args.selector.read_text(encoding="utf-8", errors="replace")
        active_selector = "\n".join(line for line in selector_text.splitlines() if not line.strip().startswith("#"))
        ok = (
            "r7b_eligible" in active_selector
            and "tc_public" not in active_selector
            and "hash" not in active_selector.lower()
        )
        add(checks, "selector_coarse_r8_rule", ok, "active rules contain r7b_eligible and no tc_public/hash tokens")

    if args.pipelines.exists():
        pipeline_text = args.pipelines.read_text(encoding="utf-8", errors="replace")
        ok = "r7win -mode rewrite -F fraig" in pipeline_text and "r7b_r7win_fraig_high" in pipeline_text
        add(checks, "pipelines_r7win_present", ok, "r7b_r7win_fraig_high present")

    if args.package_script.exists():
        script = args.package_script.read_text(encoding="utf-8", errors="replace")
        required_args = ("--metrics", "--scoreboard", "--cec-log", "--failure-cases")
        missing = [arg for arg in required_args if arg not in script]
        add(checks, "package_submit_explicit_args", not missing, "missing=" + ",".join(missing) if missing else "all explicit report args present")

    if args.release_preflight_submit_zip.exists():
        zip_hash = sha256(args.release_preflight_submit_zip)
        add(checks, "release_preflight_old_zip_unchanged", zip_hash == EXPECTED["release_preflight_submit_sha256"], zip_hash)
    else:
        zip_hash = ""

    payload = {
        "status": "pass" if all(check.ok for check in checks) else "fail",
        "expected": EXPECTED,
        "paths": paths,
        "metrics": metrics,
        "cec_log": counts,
        "explicit_package_cec_log": explicit_counts,
        "abc_sha256": abc_hash,
        "release_preflight_submit_zip_sha256": zip_hash,
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
