#!/usr/bin/env python3
"""Audit R7b r7win command robustness on small representative probes."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from run_abc_case import abc_quote, collect_stats, run_abc_command, run_cec


@dataclass(frozen=True)
class Probe:
    name: str
    case: str | None
    category: str
    command: str
    expected: str
    output_blif: Path | None = None


def parse_diag(text: str) -> dict[str, str]:
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("r7win_diag"):
            continue
        fields: dict[str, str] = {}
        for item in line.split(",")[1:]:
            key, sep, value = item.partition("=")
            if sep:
                fields[key] = value
        return fields
    return {}


def read_ports(path: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    inputs: list[str] = []
    outputs: list[str] = []
    current: list[str] | None = None
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if current is not None:
            current.extend(line.rstrip("\\").split())
            if not line.endswith("\\"):
                current = None
            continue
        if line.startswith(".inputs"):
            inputs.extend(line.rstrip("\\").split()[1:])
            if line.endswith("\\"):
                current = inputs
        elif line.startswith(".outputs"):
            outputs.extend(line.rstrip("\\").split()[1:])
            if line.endswith("\\"):
                current = outputs
    return tuple(inputs), tuple(outputs)


def classify_probe(probe: Probe, text: str, diag: dict[str, str], cec_pass: bool | None, output_written: bool) -> tuple[str, str]:
    if probe.name == "help":
        ok = "usage: r7win" in text and "R7b research-only" in text
        return ("pass" if ok else "fail", "usage_shown" if ok else "usage_missing")
    if probe.name == "invalid_mode":
        ok = "unsupported -mode" in text
        return ("pass" if ok else "fail", "invalid_mode_rejected" if ok else "invalid_mode_not_rejected")
    if probe.name == "missing_mode_arg":
        ok = "missing argument for -mode" in text or "usage: r7win" in text
        return ("pass" if ok else "fail", "missing_mode_rejected" if ok else "missing_mode_not_rejected")
    if probe.name == "non_strash_reject":
        ok = "expects a strashed AIG network" in text
        return ("pass" if ok else "fail", "non_strash_rejected" if ok else "non_strash_not_rejected")

    status = diag.get("rewrite_status", "")
    changed = diag.get("network_changed", "")
    if probe.category == "profile_noop":
        ok = output_written and cec_pass is True and status == "profile_noop" and changed == "0"
        return ("pass" if ok else "fail", status or "missing_diag")
    if probe.category == "rewrite_accept":
        ok = output_written and cec_pass is True and status == "accepted_fraig" and changed == "1"
        return ("pass" if ok else "fail", status or "missing_diag")
    if probe.category == "rewrite_rollback":
        ok = output_written and cec_pass is True and status.startswith("rollback_") and changed == "0"
        return ("pass" if ok else "fail", status or "missing_diag")
    if probe.category == "rewrite_skip":
        ok = output_written and cec_pass is True and status == "skipped_by_guard" and changed == "0"
        reason = diag.get("skip_reason", status or "missing_diag")
        return ("pass" if ok else "fail", reason)
    return ("fail", "unknown_probe_category")


def make_probes(root: Path, out_dir: Path) -> list[Probe]:
    def input_blif(case: str) -> Path:
        return root / "data" / "tc_public" / case / "input.blif"

    probes = [
        Probe("help", None, "usage", "r7win -h", "help prints r7win usage"),
        Probe("invalid_mode", None, "argument_guard", "r7win -mode nope", "invalid mode is rejected"),
        Probe("missing_mode_arg", None, "argument_guard", "r7win -mode", "missing -mode argument is rejected"),
        Probe(
            "non_strash_reject",
            "tc_public_13",
            "network_guard",
            f"read_blif {abc_quote(input_blif('tc_public_13'))}; r7win -mode rewrite -F fraig -G 0 -diag",
            "r7win rejects non-strashed networks",
        ),
    ]

    profile_cases = ["tc_public_1", "tc_public_12", "tc_public_13", "tc_public_14", "tc_public_15", "tc_public_30"]
    for case in profile_cases:
        output = out_dir / "outputs" / f"{case}_profile.blif"
        probes.append(
            Probe(
                f"profile_noop_{case}",
                case,
                "profile_noop",
                (
                    f"read_blif {abc_quote(input_blif(case))}; strash; "
                    f"r7win -profile -F fraig -G 0 -diag -case {case}; "
                    f"write_blif {abc_quote(output)}"
                ),
                "profile mode writes an equivalent unchanged BLIF",
                output,
            )
        )

    for case in ["tc_public_13", "tc_public_14"]:
        output = out_dir / "outputs" / f"{case}_rewrite_accept.blif"
        probes.append(
            Probe(
                f"rewrite_accept_{case}",
                case,
                "rewrite_accept",
                (
                    f"read_blif {abc_quote(input_blif(case))}; strash; "
                    f"r7win -mode rewrite -F fraig -G 0 -diag -case {case}; "
                    f"write_blif {abc_quote(output)}"
                ),
                "eligible high-overlap case accepts guarded FRAIG",
                output,
            )
        )

    output = out_dir / "outputs" / "tc_public_15_rewrite_rollback.blif"
    probes.append(
        Probe(
            "rewrite_rollback_tc_public_15",
            "tc_public_15",
            "rewrite_rollback",
            (
                f"read_blif {abc_quote(input_blif('tc_public_15'))}; strash; "
                f"r7win -mode rewrite -F fraig -G 0 -diag -case tc_public_15; "
                f"write_blif {abc_quote(output)}"
            ),
            "eligible case rolls back when guarded FRAIG has no local gain",
            output,
        )
    )

    for case, reason in [
        ("tc_public_1", "no_high_overlap_pair"),
        ("tc_public_12", "po_count_gt_128"),
        ("tc_public_30", "cluster_potential_lt_70"),
    ]:
        output = out_dir / "outputs" / f"{case}_rewrite_skip.blif"
        probes.append(
            Probe(
                f"rewrite_skip_{case}",
                case,
                "rewrite_skip",
                (
                    f"read_blif {abc_quote(input_blif(case))}; strash; "
                    f"r7win -mode rewrite -F fraig -G 0 -diag -case {case}; "
                    f"write_blif {abc_quote(output)}"
                ),
                f"guard skips with {reason}",
                output,
            )
        )
    return probes


def write_report(csv_path: Path, md_path: Path, rows: list[dict[str, Any]], abc: Path, out_dir: Path) -> None:
    total = len(rows)
    passed = sum(1 for row in rows if row["audit_pass"] == "pass")
    failed = total - passed
    cec_rows = [row for row in rows if row["cec_pass"] not in {"", "None"}]
    cec_pass = sum(1 for row in cec_rows if row["cec_pass"] == "True")
    md = [
        "---",
        "research_id: R7b",
        "status: candidate-ready",
        "baseline_tag: final_selector_v2_20260526",
        "baseline_commit: 0b0edf4890283e36fac943166a8c84a148c120b8",
        "branch: candidate/r7b-pure",
        "created: 2026-06-22",
        "updated: 2026-06-22",
        "affects_final: false",
        "primary_data:",
        f"  - {csv_path.as_posix()}",
        "---",
        "",
        "# R7b r7win Command Robustness Audit",
        "",
        "## Objective",
        "",
        "Audit the candidate-only ABC command `r7win` on argument guards, network guards, profile no-op behavior, guarded FRAIG acceptance, rollback, and skip paths.",
        "",
        "## Baseline",
        "",
        "Formal baseline remains `final_selector_v2_20260526`: 45870 nodes, max level 25, CEC 30/30, fallback 0. This audit does not touch the formal selector or submit archive.",
        "",
        "## Commands",
        "",
        f"- ABC: `{abc}`",
        f"- Output directory: `{out_dir}`",
        f"- CSV: `{csv_path}`",
        "",
        "## Results",
        "",
        f"- Probe pass count: `{passed}/{total}`",
        f"- Probe fail count: `{failed}`",
        f"- CEC-covered outputs: `{cec_pass}/{len(cec_rows)}`",
        "",
        "| Probe | Case | Category | Result | Observed | CEC | Network changed | Skip reason |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        md.append(
            "| {probe} | {case} | {category} | {audit_pass} | {observed_status} | {cec_pass} | {network_changed} | {skip_reason} |".format(
                **row
            )
        )
    md.extend(
        [
            "",
            "## Correctness",
            "",
            "Every probe that writes BLIF is checked with ABC CEC against the original case input. Profile no-op probes additionally require `rewrite_status=profile_noop` and `network_changed=0`.",
            "",
            "## Risk",
            "",
            "ABC returns process code 0 even for some command-level argument errors, so this audit records both the process return code and the command text diagnostics. Promotion should keep using the explicit diagnostic checks rather than process return code alone for CLI misuse cases.",
            "",
            "## Selector Eligibility",
            "",
            "No selector rule is changed by this audit. R7b selection remains driven by generated coarse overlap features, not file names, hashes, or public case IDs.",
            "",
            "## Conclusion",
            "",
            "promote-to-candidate" if failed == 0 else "research-only",
            "",
            "## Next Action",
            "",
            "Stop at the user approval point before formal merge or submit packaging.",
            "",
        ]
    )
    md_path.write_text("\n".join(md), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--abc", required=True, type=Path)
    parser.add_argument("--out", default=Path("results_candidate/r7b_command_robustness"), type=Path)
    parser.add_argument("--csv", default=Path("reports/r7b_command_robustness_audit.csv"), type=Path)
    parser.add_argument("--report", default=Path("reports/r7b_command_robustness_audit.md"), type=Path)
    parser.add_argument("--timeout", default=120.0, type=float)
    args = parser.parse_args()

    root = Path.cwd()
    out_dir = args.out
    logs_dir = out_dir / "logs"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "outputs").mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for probe in make_probes(root, out_dir):
        log_path = logs_dir / f"{probe.name}.log"
        result = run_abc_command(args.abc, probe.command, args.timeout, log_path)
        text = result.stdout + "\n" + result.stderr
        diag = parse_diag(text)
        output_written = bool(probe.output_blif and probe.output_blif.exists())
        cec_pass: bool | None = None
        pi_name_preserved: bool | None = None
        po_name_preserved: bool | None = None
        stats_nodes: int | None = None
        stats_levels: int | None = None
        cec_runtime = 0.0
        stats_runtime = 0.0
        if probe.case and output_written:
            input_blif = root / "data" / "tc_public" / probe.case / "input.blif"
            in_ports = read_ports(input_blif)
            out_ports = read_ports(probe.output_blif)
            pi_name_preserved = in_ports[0] == out_ports[0]
            po_name_preserved = in_ports[1] == out_ports[1]
            cec_pass, cec_result = run_cec(
                args.abc,
                input_blif,
                probe.output_blif,
                args.timeout,
                logs_dir / f"{probe.name}_cec.log",
            )
            cec_runtime = cec_result.runtime_sec
            stats, stats_result = collect_stats(
                args.abc,
                probe.output_blif,
                args.timeout,
                logs_dir / f"{probe.name}_stats.log",
            )
            stats_runtime = stats_result.runtime_sec
            if stats.get("aig_nodes") is not None:
                stats_nodes = int(stats["aig_nodes"])
            if stats.get("levels") is not None:
                stats_levels = int(stats["levels"])

        audit_pass, observed_status = classify_probe(probe, text, diag, cec_pass, output_written)
        rows.append(
            {
                "probe": probe.name,
                "case": probe.case or "",
                "category": probe.category,
                "audit_pass": audit_pass,
                "expected_behavior": probe.expected,
                "observed_status": observed_status,
                "abc_returncode": result.returncode,
                "timed_out": result.timed_out,
                "runtime_sec": f"{result.runtime_sec:.6f}",
                "peak_mem_mb": f"{result.peak_mem_mb:.3f}",
                "cec_pass": str(cec_pass) if cec_pass is not None else "",
                "cec_runtime_sec": f"{cec_runtime:.6f}" if cec_pass is not None else "",
                "stats_runtime_sec": f"{stats_runtime:.6f}" if output_written else "",
                "output_written": output_written,
                "pi_name_preserved": str(pi_name_preserved) if pi_name_preserved is not None else "",
                "po_name_preserved": str(po_name_preserved) if po_name_preserved is not None else "",
                "diag_stage": diag.get("stage", ""),
                "diag_mode": diag.get("mode", ""),
                "diag_proof": diag.get("proof", ""),
                "rewrite_status": diag.get("rewrite_status", ""),
                "network_changed": diag.get("network_changed", ""),
                "skip_reason": diag.get("skip_reason", ""),
                "before_nodes": diag.get("before_nodes", ""),
                "before_levels": diag.get("before_levels", ""),
                "after_nodes": diag.get("after_nodes", ""),
                "after_levels": diag.get("after_levels", ""),
                "stats_nodes": stats_nodes if stats_nodes is not None else "",
                "stats_levels": stats_levels if stats_levels is not None else "",
                "log_path": log_path.as_posix(),
                "output_blif": probe.output_blif.as_posix() if probe.output_blif else "",
            }
        )

    fieldnames = list(rows[0].keys())
    with args.csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    write_report(args.csv, args.report, rows, args.abc, out_dir)
    failed = [row for row in rows if row["audit_pass"] != "pass"]
    print(f"wrote {args.csv} and {args.report}; pass={len(rows)-len(failed)}/{len(rows)}")
    if failed:
        for row in failed:
            print(f"FAIL {row['probe']}: {row['observed_status']}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
