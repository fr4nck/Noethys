#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inventorie des pièges sémantiques transverses sans modifier le code applicatif.

L'audit privilégie le rappel : chaque signal reste à qualifier humainement avant
correction ou attribution à l'upstream. Les catégories visent des défauts qui
échappent facilement à une recherche textuelle simple : état partagé par défaut,
asymétrie validation/sauvegarde, cycle de vie modal et blocage de la boucle wx.
"""

from __future__ import annotations

import argparse
import ast
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
EXCLUDED_PARTS = {"ObjectListView", "Outils"}
MUTATING_METHODS = {
    "append", "extend", "insert", "remove", "pop", "clear", "sort", "reverse",
    "update", "setdefault", "add", "discard", "difference_update",
    "intersection_update", "symmetric_difference_update",
}
UI_CALLBACK_PREFIXES = ("On", "Timer", "Handle", "Traitement", "Refresh", "MAJ")


def iter_python_files(root=NOETHYS):
    for path in root.rglob("*.py"):
        relative = path.relative_to(root)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        yield path


def _mutable_default_names(function):
    positional = list(function.args.posonlyargs) + list(function.args.args)
    defaults = [None] * (len(positional) - len(function.args.defaults)) + list(function.args.defaults)
    pairs = list(zip(positional, defaults))
    pairs.extend(zip(function.args.kwonlyargs, function.args.kw_defaults))
    result = {}
    for arg, default in pairs:
        if isinstance(default, (ast.List, ast.Dict, ast.Set)):
            result[arg.arg] = type(default).__name__.lower()
    return result


def _name_is_mutated(function, name):
    for node in ast.walk(function):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == name and node.func.attr in MUTATING_METHODS:
                return True, node.lineno, node.func.attr
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Delete)):
            targets = []
            if isinstance(node, ast.Assign):
                targets = node.targets
            elif isinstance(node, ast.AnnAssign):
                targets = [node.target]
            elif isinstance(node, ast.AugAssign):
                targets = [node.target]
            else:
                targets = node.targets
            for target in targets:
                if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name) and target.value.id == name:
                    return True, node.lineno, "item_mutation"
    return False, 0, ""


def _name_escapes(function, name):
    for node in ast.walk(function):
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Name) and node.value.id == name:
            return True, node.lineno
    return False, 0


def _attribute_calls(function, method_name):
    found = []
    for node in ast.walk(function):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != method_name:
            continue
        owner = node.func.value
        if isinstance(owner, ast.Attribute) and isinstance(owner.value, ast.Name) and owner.value.id == "self":
            found.append((owner.attr, node.lineno))
    return found


def _assigned_dialog_names(function):
    dialogs = {}
    for node in ast.walk(function):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        target = node.targets[0].id
        value = node.value
        if not isinstance(value, ast.Call):
            continue
        callee = value.func
        text = ""
        if isinstance(callee, ast.Attribute):
            text = callee.attr
        elif isinstance(callee, ast.Name):
            text = callee.id
        if "Dialog" in text or text.startswith("DLG_") or text in {"MessageDialog", "TextEntryDialog", "SingleChoiceDialog", "MultiChoiceDialog"}:
            dialogs[target] = node.lineno
    return dialogs


def _method_calls_on_name(function, name, method):
    lines = []
    for node in ast.walk(function):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != method:
            continue
        if isinstance(node.func.value, ast.Name) and node.func.value.id == name:
            lines.append(node.lineno)
    return lines


def _qualified_name(node):
    parts = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    return ".".join(reversed(parts))


def scan_file(path, root=NOETHYS):
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError):
        return []

    rel = str(path.relative_to(root)).replace("\\", "/")
    findings = []

    for function in (node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))):
        for name, default_type in _mutable_default_names(function).items():
            mutated, line, operation = _name_is_mutated(function, name)
            escapes, return_line = _name_escapes(function, name)
            if mutated:
                findings.append({
                    "kind": "mutable_default_mutated",
                    "priority": "high",
                    "file": rel,
                    "function": function.name,
                    "line": line,
                    "parameter": name,
                    "default_type": default_type,
                    "detail": operation,
                })
            elif escapes:
                findings.append({
                    "kind": "mutable_default_escape",
                    "priority": "medium",
                    "file": rel,
                    "function": function.name,
                    "line": return_line,
                    "parameter": name,
                    "default_type": default_type,
                    "detail": "returned_directly",
                })

        validations = _attribute_calls(function, "Validation")
        saves = {name for name, _line in _attribute_calls(function, "Sauvegarde")}
        if validations and function.name.lower() in {"onboutonok", "onboutonvalider", "valider", "sauvegarder", "sauvegarde"}:
            for control, line in validations:
                if control not in saves:
                    findings.append({
                        "kind": "validation_without_save",
                        "priority": "high",
                        "file": rel,
                        "function": function.name,
                        "line": line,
                        "control": control,
                        "detail": "Validation() sans Sauvegarde() dans le même chemin de confirmation",
                    })

        for name, create_line in _assigned_dialog_names(function).items():
            shown = _method_calls_on_name(function, name, "ShowModal")
            destroyed = _method_calls_on_name(function, name, "Destroy")
            if shown and not destroyed:
                findings.append({
                    "kind": "modal_without_destroy",
                    "priority": "medium",
                    "file": rel,
                    "function": function.name,
                    "line": shown[0],
                    "dialog": name,
                    "detail": f"dialogue créé ligne {create_line}",
                })

        if function.name.startswith(UI_CALLBACK_PREFIXES):
            for node in ast.walk(function):
                if not isinstance(node, ast.Call):
                    continue
                if _qualified_name(node.func) in {"time.sleep", "sleep"}:
                    findings.append({
                        "kind": "blocking_sleep_ui_callback",
                        "priority": "high",
                        "file": rel,
                        "function": function.name,
                        "line": node.lineno,
                        "detail": _qualified_name(node.func),
                    })

    return findings


def build_report(root=NOETHYS):
    findings = []
    for path in iter_python_files(root):
        findings.extend(scan_file(path, root))
    findings.sort(key=lambda item: (item["priority"] != "high", item["kind"], item["file"], item["line"]))
    return {
        "count": len(findings),
        "kinds": dict(Counter(item["kind"] for item in findings)),
        "priorities": dict(Counter(item["priority"] for item in findings)),
        "findings": findings,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", default="", metavar="FILE")
    args = parser.parse_args(argv)
    report = build_report()
    print(f"SEMANTIC_TRAPS={report['count']} — {report['kinds']} — {report['priorities']}")
    for item in report["findings"]:
        if item["priority"] == "high":
            print(f"- HIGH {item['kind']} {item['file']}:{item['line']} {item['function']}")
    if args.json:
        output = Path(args.json)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Rapport JSON exporté : {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
