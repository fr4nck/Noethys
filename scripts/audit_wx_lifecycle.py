#!/usr/bin/env python3
"""Inventorie les cycles de vie wxPython potentiellement fragiles.

Le contrôle est informatif. Il signale les dialogues modaux sans destruction
visible, les timers démarrés sans arrêt repérable, les appels différés et les
destructions directes qui méritent une revue sous wxPython moderne.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "noethys")
SKIP_DIRS = {".git", ".venv", "__pycache__", "build", "dist", "venv"}


def dotted_name(node: ast.AST) -> str:
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    return ".".join(reversed(parts))


def scan(path: Path) -> list[tuple[int, str]]:
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return []

    findings: list[tuple[int, str]] = []
    methods: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods[node.name] = node

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = dotted_name(node.func)
        tail = name.rsplit(".", 1)[-1]

        if tail == "ShowModal":
            findings.append((node.lineno, "dialogue modal à vérifier : destruction explicite attendue"))
        elif tail in {"Destroy", "DestroyLater"}:
            findings.append((node.lineno, f"destruction de fenêtre via {tail}() à vérifier"))
        elif tail in {"CallAfter", "CallLater"} or name in {"wx.CallAfter", "wx.CallLater"}:
            findings.append((node.lineno, f"appel différé via {tail}() à vérifier"))
        elif tail == "Start":
            findings.append((node.lineno, "timer potentiellement démarré : vérifier Stop()/destruction"))
        elif tail == "Bind" and node.args:
            event_name = dotted_name(node.args[0])
            if "EVT_TIMER" in event_name:
                findings.append((node.lineno, "handler EVT_TIMER à vérifier : arrêt et durée de vie"))

    return sorted(set(findings))


def main() -> int:
    total = 0
    for path in sorted(ROOT.rglob("*.py")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        for lineno, message in scan(path):
            total += 1
            print(f"{path}:{lineno}: {message}")
    print(f"\n{total} point(s) de cycle de vie wxPython à examiner.")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
