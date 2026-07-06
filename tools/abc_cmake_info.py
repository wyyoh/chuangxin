#!/usr/bin/env python3
"""Emit the small `make cmake_info` payload expected by ABC's CMakeLists.

The upstream ABC CMake file shells out to GNU make to expand MODULES and SRC.
On Windows machines with Visual Studio but without GNU make, this helper can be
called from a temporary `make.cmd` shim to provide the same four separator lines.
It is intentionally conservative and only emits the module set used by this
repository's Makefile for a no-readline, no-pthread research build.
"""

from __future__ import annotations

import glob
import re
import sys
from pathlib import Path


CUDD_MODULES = [
    "src/bdd/cudd",
    "src/bdd/extrab",
    "src/bdd/dsd",
    "src/bdd/epd",
    "src/bdd/mtr",
    "src/bdd/reo",
    "src/bdd/cas",
    "src/bdd/bbr",
    "src/bdd/llb",
]

MSVC_EXCLUDED_MODULES = {
    "src/opt/eslim",
    "src/opt/ufar",
    "src/opt/untk",
    "src/opt/util",
    "src/sat/cadical",
}

MSVC_EXTRA_SOURCES = [
    "src/sat/cadical/cadicalStub.c",
    "src/opt/sharecone/shareconeBuildStubs.c",
]


def _strip_comments(line: str) -> str:
    return line.split("#", 1)[0].rstrip()


def _module_tokens(abc_root: Path) -> list[str]:
    text = (abc_root / "Makefile").read_text(encoding="utf-8", errors="replace")
    match = re.search(r"MODULES\s*:=\s*\\\n(?P<body>.*?)(?:\n\n|\nall:)", text, re.S)
    if not match:
        raise RuntimeError("could not find MODULES block in ABC Makefile")
    body = match.group("body").replace("\\\n", " ")
    tokens: list[str] = []
    for token in body.split():
        token = token.strip()
        if not token:
            continue
        if token.startswith("$(wildcard") and token.endswith(")"):
            pattern = token[len("$(wildcard") : -1].strip()
            tokens.extend(
                path.relative_to(abc_root).as_posix()
                for path in sorted(abc_root.glob(pattern))
                if path.is_dir()
            )
        elif token.startswith("$("):
            continue
        else:
            tokens.append(token)
    for module in CUDD_MODULES:
        if module not in tokens:
            tokens.append(module)
    return tokens


def _sources_from_module_make(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    text = "\n".join(_strip_comments(line) for line in text.splitlines())
    text = text.replace("\\\n", " ")
    return re.findall(r"\bsrc/[^\s]+?\.(?:c|cc|cpp)\b", text)


def source_list(abc_root: Path) -> list[str]:
    sources: list[str] = []
    seen: set[str] = set()
    for module in _module_tokens(abc_root):
        if module in MSVC_EXCLUDED_MODULES:
            continue
        module_make = abc_root / module / "module.make"
        if not module_make.exists():
            continue
        for source in _sources_from_module_make(module_make):
            if source in seen:
                continue
            if not (abc_root / source).exists():
                continue
            seen.add(source)
            sources.append(source)
    for source in MSVC_EXTRA_SOURCES:
        if source not in seen and (abc_root / source).exists():
            seen.add(source)
            sources.append(source)
    return sources


def main(argv: list[str]) -> int:
    abc_root = Path(argv[1]) if len(argv) > 1 else Path.cwd()
    abc_root = abc_root.resolve()
    sources = source_list(abc_root)
    cflags = [
        "-DABC_USE_STDINT_H=1",
        "-DABC_USE_CUDD=1",
        "-DABC_USE_NO_READLINE=1",
        "-DWIN32_NO_DLL=1",
    ]
    print("SEPARATOR_CFLAGS", *cflags, "SEPARATOR_CFLAGS")
    print("SEPARATOR_CXXFLAGS", *cflags, "SEPARATOR_CXXFLAGS")
    print("SEPARATOR_LIBS", "shlwapi", "SEPARATOR_LIBS")
    print("SEPARATOR_SRC", *sources, "SEPARATOR_SRC")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
