#!/usr/bin/env python3
"""Inventorie les chargements dynamiques sensibles au packaging.

Les imports dynamiques non littéraux et la découverte dynamique de modules sont
les motifs pertinents pour PyInstaller. Certains chargements sont cependant
volontairement résolus au runtime (extensions utilisateur, fichier models.py
téléchargé) ou encapsulés dans des helpers génériques. Ils sont signalés mais ne
sont pas comptés comme risques PyInstaller non couverts.

Les appels exec/eval historiques sont signalés séparément : ils constituent un
sujet de dette technique/sécurité distinct. La couverture des sources est
bloquante : aucun fichier non lu ou non parsé n'est assimilé à zéro occurrence.
"""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

try:
    from scripts.audit_source_coverage import SourceAuditSession, iter_python_files
except ModuleNotFoundError:
    from audit_source_coverage import SourceAuditSession, iter_python_files

ROOT = Path("noethys")
SKIP_DIRS = {".git", "build", "dist", "__pycache__", "venv", ".venv"}

RUNTIME_EXTERNAL = {
    "noethys/Dlg/DLG_Extensions.py",
    "noethys/Utils/UTILS_Portail_synchro.py",
}
DYNAMIC_HELPERS = {
    "noethys/Outils/mail/module_loading.py",
    "noethys/Utils/UTILS_Adaptations.py",
}
STATICALLY_COVERED = {
    "noethys/Ol/OL_Activites.py",
}


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


def scan_tree(tree: ast.AST) -> tuple[list[tuple[int, str]], list[tuple[int, str]]]:
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


def scan(path: Path) -> tuple[list[tuple[int, str]], list[tuple[int, str]]]:
    session = SourceAuditSession([path])
    loaded = session.parse(path)
    session.require_complete()
    assert loaded is not None
    _source, tree = loaded
    return scan_tree(tree)


def classification(path: Path) -> str:
    rel = path.as_posix()
    if rel in RUNTIME_EXTERNAL:
        return "EXTERNE-RUNTIME"
    if rel in DYNAMIC_HELPERS:
        return "HELPER-DYNAMIQUE"
    if rel in STATICALLY_COVERED:
        return "COUVERT-STATIQUE"
    return "RISQUE-PYINSTALLER"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="noethys")
    parser.add_argument("--max-import-risks", type=int, default=None)
    args = parser.parse_args()

    root = Path(args.root)
    session = SourceAuditSession(iter_python_files(root, skip_dirs=SKIP_DIRS))
    import_total = 0
    qualified_total = 0
    eval_total = 0
    for path in session.paths:
        loaded = session.parse(path)
        if loaded is None:
            continue
        _source, tree = loaded
        import_risks, eval_uses = scan_tree(tree)
        category = classification(path)
        for lineno, message in import_risks:
            if category == "RISQUE-PYINSTALLER":
                import_total += 1
            else:
                qualified_total += 1
            print(f"{category} {path}:{lineno}: {message}")
        for lineno, message in eval_uses:
            eval_total += 1
            print(f"INFO-EXEC {path}:{lineno}: {message}")

    print(f"\n{import_total} risque(s) PyInstaller non qualifié(s).")
    print(f"{qualified_total} import(s) dynamique(s) attendu(s)/qualifié(s).")
    print(f"{eval_total} usage(s) exec/eval historique(s), informatif(s).")
    session.report(prefix="Couverture audit imports dynamiques")
    session.require_complete()

    if args.max_import_risks is not None and import_total > args.max_import_risks:
        print(
            f"Le nombre de risques PyInstaller non qualifiés dépasse la baseline "
            f"autorisée ({import_total} > {args.max_import_risks})."
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
