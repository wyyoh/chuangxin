#!/usr/bin/env python3
"""Lightweight ABC command capability inventory for pipeline search."""

from __future__ import annotations

import argparse
import csv
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


UNKNOWN_MARKERS = (
    "unknown command",
    "unknown option",
    "cannot find command",
    "command not found",
    "not recognized",
    "invalid command",
)
CRASH_MARKERS = (
    "segmentation fault",
    "access violation",
    "assertion",
    "aborted",
    "fatal error",
)


@dataclass(frozen=True)
class CommandSpec:
    command: str
    probe: str
    context_note: str
    context_sensitive: bool = False


def abc_path(path: Path) -> str:
    return str(path).replace("\\", "/")


def abc_quote(path: Path) -> str:
    return '"' + abc_path(path) + '"'


def build_specs(probe_case: Path) -> list[CommandSpec]:
    read = f"read_blif {abc_quote(probe_case)}"
    aig = f"{read}; strash"
    sop = f"{read}; sweep"
    gia = f"{read}; strash; &get"
    return [
        CommandSpec("rewrite", f"{aig}; rewrite; ps", "AIG context"),
        CommandSpec("rewrite -z", f"{aig}; rewrite -z; ps", "AIG context"),
        CommandSpec("refactor", f"{aig}; refactor; ps", "AIG context"),
        CommandSpec("refactor -z", f"{aig}; refactor -z; ps", "AIG context"),
        CommandSpec("resub", f"{aig}; resub; ps", "AIG context"),
        CommandSpec("resub -z", f"{aig}; resub -z; ps", "AIG context"),
        CommandSpec("dc2", f"{aig}; dc2; ps", "AIG context"),
        CommandSpec("dch", f"{aig}; dch; ps", "AIG context"),
        CommandSpec("dch -f", f"{aig}; dch -f; ps", "AIG context"),
        CommandSpec("fraig", f"{aig}; fraig; ps", "AIG context"),
        CommandSpec("ifraig", f"{aig}; ifraig; ps", "AIG context"),
        CommandSpec("compress2rs", f"{aig}; compress2rs; ps", "AIG context"),
        CommandSpec("sweep", f"{sop}; ps", "SOP/network context", True),
        CommandSpec("bdd", f"{sop}; bdd; ps", "BDD-capable network context", True),
        CommandSpec("sop", f"{sop}; bdd; sop; ps", "SOP requires BDD-derived context", True),
        CommandSpec("fx", f"{sop}; fx; ps", "SOP/network context", True),
        CommandSpec("if -K 4", f"{aig}; if -K 4; ps", "mapped LUT context", True),
        CommandSpec("if -K 5", f"{aig}; if -K 5; ps", "mapped LUT context", True),
        CommandSpec("if -K 6", f"{aig}; if -K 6; ps", "mapped LUT context", True),
        CommandSpec("mfs2", f"{aig}; if -K 4; mfs2; strash; ps", "post-mapping context", True),
        CommandSpec("mfs3", f"{aig}; if -K 4; mfs3; strash; ps", "post-mapping context", True),
        CommandSpec("st", f"{aig}; if -K 4; st; strash; ps", "post-mapping context", True),
        CommandSpec("&get", f"{gia}; &put; ps", "GIA manager context", True),
        CommandSpec("&put", f"{gia}; &put; ps", "GIA manager context", True),
        CommandSpec("&syn2", f"{gia}; &syn2; &put; ps", "GIA manager context", True),
        CommandSpec("&dc2", f"{gia}; &dc2; &put; ps", "GIA manager context", True),
    ]


def run_abc(abc: Path, command: str, timeout: float) -> tuple[int, bool, float, str, str]:
    start = time.perf_counter()
    proc = subprocess.Popen(
        [str(abc), "-c", command],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        proc.kill()
        stdout, stderr = proc.communicate()
    runtime = time.perf_counter() - start
    return proc.returncode if proc.returncode is not None else -1, timed_out, runtime, stdout, stderr


def classify(returncode: int, timed_out: bool, text: str, spec: CommandSpec) -> tuple[str, str, str]:
    lower = text.lower()
    if timed_out:
        return "false", "timeout", "probe timed out"
    if any(marker in lower for marker in UNKNOWN_MARKERS):
        return "false", "unavailable", "ABC reported unknown or invalid command"
    if returncode == 0:
        return "true", "", ""
    if returncode < 0 or any(marker in lower for marker in CRASH_MARKERS):
        return "false", "crash", f"ABC exited abnormally with returncode {returncode}"
    if spec.context_sensitive:
        return "context_dependent", "context_failed", (
            "probe context failed; keep as context-dependent instead of permanently disabling"
        )
    return "false", "context_failed", f"probe failed in expected context with returncode {returncode}"


def excerpt(text: str, limit: int = 240) -> str:
    compact = " ".join(text.replace("\r", "\n").split())
    return compact[:limit]


def write_text_report(path: Path, rows: list[dict[str, object]]) -> None:
    lines = [
        "# ABC Command Inventory V2",
        "",
        "Failure categories: unavailable, context_failed, timeout, crash.",
        "Context-dependent failures are not permanent disables for commands that require special network types.",
        "",
        "| command | available | generation_status | failure_category | context_note | failure_reason |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {command} | {available} | {generation_status} | {failure_category} | {context_note} | {failure_reason} |".format(
                **{k: str(v).replace("|", "\\|") for k, v in row.items()}
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_csv_report(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "command",
        "available",
        "generation_status",
        "failure_category",
        "failure_reason",
        "context_note",
        "context_sensitive",
        "returncode",
        "timed_out",
        "runtime_sec",
        "probe_command",
        "stdout_excerpt",
        "stderr_excerpt",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--abc", required=True, type=Path)
    parser.add_argument("--probe-case", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    if not args.abc.exists():
        raise SystemExit(f"ABC executable not found: {args.abc}")
    if not args.probe_case.exists():
        raise SystemExit(f"probe BLIF not found: {args.probe_case}")

    rows: list[dict[str, object]] = []
    for spec in build_specs(args.probe_case):
        returncode, timed_out, runtime, stdout, stderr = run_abc(args.abc, spec.probe, args.timeout)
        available, category, reason = classify(returncode, timed_out, stdout + "\n" + stderr, spec)
        generation_status = "enabled"
        if category in {"unavailable", "timeout", "crash"}:
            generation_status = "disabled"
        elif category == "context_failed" and not spec.context_sensitive:
            generation_status = "disabled"
        elif category == "context_failed":
            generation_status = "context_dependent"
        rows.append(
            {
                "command": spec.command,
                "available": available,
                "generation_status": generation_status,
                "failure_category": category,
                "failure_reason": reason,
                "context_note": spec.context_note,
                "context_sensitive": str(spec.context_sensitive).lower(),
                "returncode": returncode,
                "timed_out": str(timed_out).lower(),
                "runtime_sec": f"{runtime:.6f}",
                "probe_command": spec.probe,
                "stdout_excerpt": excerpt(stdout),
                "stderr_excerpt": excerpt(stderr),
            }
        )

    write_text_report(args.out, rows)
    write_csv_report(args.csv, rows)
    print(f"wrote {args.out}")
    print(f"wrote {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
