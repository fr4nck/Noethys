#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit statique des contrats de construction wxPython.

Objectif : repérer les contrôles qui confondent encore leur parent visuel wx
avec un contrôleur métier, ainsi que les callbacks exécutés trop tôt pendant
``__init__``. L'audit est volontairement informatif : chaque occurrence doit
être relue puis corrigée à la source avant de rendre une catégorie bloquante.
"""

from __future__ import annotations

import argparse
import ast
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
UI_LAYERS = {"Ctrl", "Dlg", "Ol"}
EXCLUS = {"ObjectListView", "Outils", "__pycache__"}

# Méthodes purement visuelles usuelles : leur appel via le parent wx n'implique
# pas, à lui seul, un couplage métier.
WX_PARENT_METHODS = {
    "Bind", "Centre", "Center", "Close", "Destroy", "Disable", "Enable",
    "Fit", "Freeze", "GetBackgroundColour", "GetClientSize", "GetFont",
    "GetForegroundColour", "GetId", "GetName", "GetParent", "GetPosition",
    "GetSize", "GetSizer", "GetTopLevelParent", "Hide", "Layout", "PopupMenu",
    "Refresh", "SendSizeEvent", "SetBackgroundColour", "SetFocus", "SetFont",
    "SetForegroundColour", "SetMinSize", "SetSize", "SetSizer", "Show", "Thaw",
    "Update",
}

EARLY_SELF_CALLS = {
    "MAJ", "Actualise", "Actualiser", "Importation", "Refresh", "Update",
}
LAYOUT_MARKERS = {"__do_layout", "DoLayout", "Layout", "SetSizer", "SetSizerAndFit"}


def _ui_file(path: Path) -> bool:
    rel = path.relative_to(NOETHYS)
    return (
        bool(rel.parts)
        and rel.parts[0] in UI_LAYERS
        and not any(part in EXCLUS for part in rel.parts)
    )


def _attr_chain(node: ast.AST) -> list[str] | None:
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
        return list(reversed(parts))
    return None


def _call_name(node: ast.Call) -> list[str] | None:
    return _attr_chain(node.func)


def _line(lines: list[str], lineno: int) -> str:
    if 1 <= lineno <= len(lines):
        return lines[lineno - 1].strip()[:180]
    return ""


def _looks_like_wx_constructor(init: ast.FunctionDef) -> bool:
    for node in ast.walk(init):
        if not isinstance(node, ast.Call):
            continue
        chain = _call_name(node)
        if not chain:
            continue
        if chain[:1] == ["wx"] and chain[-1] == "__init__":
            return True
        if chain[:1] == ["super"] and chain[-1] == "__init__":
            return True
    return False


def _stores_visual_parent(init: ast.FunctionDef) -> bool:
    for node in ast.walk(init):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        value = node.value
        if not isinstance(value, ast.Name) or value.id != "parent":
            continue
        for target in targets:
            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                if target.value.id == "self" and target.attr == "parent":
                    return True
    return False


def _scan_parent_coupling(path: Path, tree: ast.AST, lines: list[str]) -> list[dict]:
    findings: list[dict] = []
    rel = str(path.relative_to(ROOT)).replace("\\", "/")

    for cls in (node for node in tree.body if isinstance(node, ast.ClassDef)):
        init = next(
            (node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == "__init__"),
            None,
        )
        if init is None:
            continue
        if "parent" not in {arg.arg for arg in init.args.args}:
            continue
        if not _looks_like_wx_constructor(init) or not _stores_visual_parent(init):
            continue

        for method in (node for node in cls.body if isinstance(node, ast.FunctionDef)):
            for node in ast.walk(method):
                if not isinstance(node, ast.Attribute):
                    continue
                chain = _attr_chain(node)
                if not chain or len(chain) < 3 or chain[:2] != ["self", "parent"]:
                    continue
                member = chain[2]
                if member in WX_PARENT_METHODS:
                    continue
                findings.append({
                    "kind": "visual_parent_business_coupling",
                    "file": rel,
                    "class": cls.name,
                    "method": method.name,
                    "line": node.lineno,
                    "member": member,
                    "snippet": _line(lines, node.lineno),
                })

    return findings


def _top_level_calls(function: ast.FunctionDef):
    for statement in function.body:
        for node in ast.walk(statement):
            if isinstance(node, ast.Call):
                yield node


def _scan_constructor_order(path: Path, tree: ast.AST, lines: list[str]) -> list[dict]:
    findings: list[dict] = []
    rel = str(path.relative_to(ROOT)).replace("\\", "/")

    for cls in (node for node in tree.body if isinstance(node, ast.ClassDef)):
        init = next(
            (node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == "__init__"),
            None,
        )
        if init is None:
            continue

        layout_seen = False
        for call in _top_level_calls(init):
            chain = _call_name(call)
            if not chain:
                continue

            # Le premier marqueur de layout clôt la phase dangereuse.
            if chain[:1] == ["self"] and chain[-1] in LAYOUT_MARKERS:
                layout_seen = True
                continue

            if not layout_seen and chain[:1] == ["self"] and chain[-1] in EARLY_SELF_CALLS:
                findings.append({
                    "kind": "constructor_callback_before_layout",
                    "file": rel,
                    "class": cls.name,
                    "method": "__init__",
                    "line": call.lineno,
                    "member": chain[-1],
                    "snippet": _line(lines, call.lineno),
                })

            if not layout_seen and chain[:1] == ["parent"] and len(chain) >= 2:
                member = chain[1]
                if member not in WX_PARENT_METHODS:
                    findings.append({
                        "kind": "constructor_parent_callback",
                        "file": rel,
                        "class": cls.name,
                        "method": "__init__",
                        "line": call.lineno,
                        "member": member,
                        "snippet": _line(lines, call.lineno),
                    })

    return findings


def scan() -> list[dict]:
    findings: list[dict] = []
    for path in sorted(NOETHYS.rglob("*.py")):
        if not _ui_file(path):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(text, filename=str(path))
        except (OSError, SyntaxError):
            continue
        lines = text.splitlines()
        findings.extend(_scan_parent_coupling(path, tree, lines))
        findings.extend(_scan_constructor_order(path, tree, lines))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path)
    parser.add_argument("--fail-on", action="append", default=[])
    args = parser.parse_args()

    findings = scan()
    counts = Counter(item["kind"] for item in findings)
    kinds = {
        "visual_parent_business_coupling",
        "constructor_callback_before_layout",
        "constructor_parent_callback",
    }

    print("Audit contrats wxPython")
    print("=======================")
    print("Occurrences : %d" % len(findings))
    for kind in sorted(kinds):
        print("  %-36s %d" % (kind + ":", counts.get(kind, 0)))

    hotspots = Counter(item["file"] for item in findings)
    print("\nFichiers prioritaires :")
    for filename, count in hotspots.most_common(30):
        print("  %4d  %s" % (count, filename))

    print("\nPremières occurrences :")
    for item in findings[:80]:
        print(
            "  {kind}  {file}:{line}  {class}.{method} -> {member}  {snippet}".format(**item)
        )

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps({"counts": dict(counts), "findings": findings}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    unknown = set(args.fail_on).difference(kinds)
    if unknown:
        print("\nCatégorie(s) inconnue(s) : %s" % ", ".join(sorted(unknown)))
        return 2
    if any(counts.get(kind, 0) for kind in args.fail_on):
        print("\nContrat wx bloquant encore présent : %s" % ", ".join(sorted(args.fail_on)))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
