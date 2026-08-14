#!/usr/bin/env python3
"""Inventorie les chargements dynamiques sensibles au packaging.

Les imports dynamiques non littéraux et la découverte dynamique de modules sont
les motifs pertinents pour PyInstaller. Les appels exec/eval historiques sont
signalés séparément mais ne bloquent pas le packaging : ils constituent un sujet
de dette technique/sécurité distinct.

Par défaut le script est informatif. ``--max-import-risks N`` permet à la CI de
bloquer uniquement si le nombre de risques PyInstaller dépasse une baseline
connue, sans casser le dépôt à cause de l'existant.
"""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

ROOT = Path("noethys")
SKIP_DIRS = {".git", "build", "dist", "__pycache__", "venv", ".venv"}


def call_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        parts = []
        current = func
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))
    return ""


def is_literal_string(node: ast.AST | None) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, str)


def scan(path: Path) -> tuple[list[tuple[int, str]], list[tuple[int, str]]]:
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError):
        return [], []

    import_risks: list[tuple[int, str]] = []
    eval_uses: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = call_name(node)
        if name in {"__import__", "importlib.import_module", "import_module"}:
            argument = node.args[0] if node.args else None
            if not is_literal_string(argument):
                import_risks.append((node.lineno, f"import dynamique non littéral via {name}()"))
        elif name in {"pkgutil.iter_modules", "pkgutil.walk_packages", "importlib.util.spec_from_file_location"}:
            import_risks.append((node.lineno, f"découverte dynamique via {name}()"))
        elif name in {"exec", "eval"}:
            eval_uses.append((node.lineno, f"exécution dynamique via {name}()"))
    return sorted(set(import_risks)), sorted(set(eval_uses))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="noethys")
    parser.add_argument("--max-import-risks", type=int, default=None)
    args = parser.parse_args()

    root = Path(args.root)
    import_total = 0
    eval_total = 0
    for path in sorted(root.rglob("*.py")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        import_risks, eval_uses = scan(path)
        for lineno, message in import_risks:
            import_total += 1
            print(f"RISQUE-PYINSTALLER {path}:{lineno}: {message}")
        for lineno, message in eval_uses:
            eval_total += 1
            print(f"INFO-EXEC {path}:{lineno}: {message}")

    print(f"\n{import_total} risque(s) d'import dynamique pour PyInstaller.")
    print(f"{eval_total} usage(s) exec/eval historique(s), informatif(s).")

    if args.max_import_risks is not None and import_total > args.max_import_risks:
        print(
            f"Le nombre de risques PyInstaller dépasse la baseline autorisée "
            f"({import_total} > {args.max_import_risks})."
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
