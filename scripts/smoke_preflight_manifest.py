#!/usr/bin/env python3
"""Vérifie la cohérence interne de scripts/package_preflight.py."""
from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PREFLIGHT = ROOT / "scripts" / "package_preflight.py"


def main() -> int:
    source = PREFLIGHT.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(PREFLIGHT))

    checks_node = None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "CHECKS":
                    checks_node = node.value
                    break

    if not isinstance(checks_node, (ast.Tuple, ast.List)):
        print("CHECKS introuvable ou non littéral dans package_preflight.py")
        return 1

    labels: list[str] = []
    scripts: list[str] = []
    errors: list[str] = []

    for index, item in enumerate(checks_node.elts, start=1):
        if not isinstance(item, ast.Tuple) or len(item.elts) != 3:
            errors.append(f"Entrée CHECKS #{index} invalide")
            continue

        label_node, command_node, blocking_node = item.elts
        if not isinstance(label_node, ast.Constant) or not isinstance(label_node.value, str):
            errors.append(f"Entrée CHECKS #{index}: libellé non littéral")
            continue
        labels.append(label_node.value)

        if not isinstance(blocking_node, ast.Constant) or not isinstance(blocking_node.value, bool):
            errors.append(f"{label_node.value}: niveau bloquant non booléen")

        if not isinstance(command_node, (ast.List, ast.Tuple)) or len(command_node.elts) < 2:
            errors.append(f"{label_node.value}: commande invalide")
            continue

        script_node = command_node.elts[1]
        if isinstance(script_node, ast.Constant) and isinstance(script_node.value, str):
            script = script_node.value
            if script.endswith(".py"):
                scripts.append(script)
                if not (ROOT / script).is_file():
                    errors.append(f"{label_node.value}: script absent: {script}")

    duplicate_labels = [name for name, count in Counter(labels).items() if count > 1]
    duplicate_scripts = [name for name, count in Counter(scripts).items() if count > 1]
    for label in duplicate_labels:
        errors.append(f"Libellé dupliqué: {label}")
    for script in duplicate_scripts:
        errors.append(f"Script référencé plusieurs fois: {script}")

    if errors:
        print("Préflight incohérent :")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Manifest du préflight cohérent : {len(labels)} contrôle(s), {len(scripts)} script(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
