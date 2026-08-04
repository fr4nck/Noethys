#!/usr/bin/env python3
"""Repère et, sur demande, modernise les ouvertures texte UTF-8 certaines.

Le mode par défaut est un contrôle sans modification. ``--apply`` ajoute
``encoding="utf-8"`` uniquement aux appels ``open()`` mono-ligne dont :

- le chemin est une chaîne littérale avec une extension texte connue ;
- le mode est littéral et non binaire ;
- aucun encodage n'est déjà fourni.

Les appels dynamiques, multilignes, binaires ou ambigus restent signalés par
l'audit général et ne sont jamais réécrits ici.
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

TEXT_EXTENSIONS = {
    ".csv", ".ini", ".json", ".log", ".md", ".sql", ".txt", ".xml",
    ".yaml", ".yml", ".xlang",
}
SKIP_DIRS = {".git", ".venv", "__pycache__", "build", "dist", "venv"}
OPEN_RE = re.compile(
    r"(?P<prefix>\bopen\(\s*)(?P<quote>['\"])(?P<path>[^'\"]+)(?P=quote)"
    r"(?P<rest>\s*(?:,\s*(?P<modequote>['\"])(?P<mode>[^'\"]+)(?P=modequote))?\s*)\)"
)


def is_text_mode(mode: str | None) -> bool:
    effective = mode or "r"
    return "b" not in effective and set(effective) <= set("rwax+t")


def replacement(match: re.Match[str]) -> str:
    path = match.group("path")
    mode = match.group("mode")
    suffix = Path(path).suffix.lower()
    if suffix not in TEXT_EXTENSIONS or not is_text_mode(mode):
        return match.group(0)
    rest = match.group("rest")
    return f"{match.group('prefix')}{match.group('quote')}{path}{match.group('quote')}{rest}, encoding=\"utf-8\")"


def candidates(path: Path) -> list[int]:
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []
    lines = source.splitlines()
    found: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) or node.func.id != "open":
            continue
        if node.end_lineno != node.lineno or not node.args:
            continue
        if any(keyword.arg == "encoding" for keyword in node.keywords):
            continue
        filename = node.args[0]
        if not isinstance(filename, ast.Constant) or not isinstance(filename.value, str):
            continue
        if Path(filename.value).suffix.lower() not in TEXT_EXTENSIONS:
            continue
        mode = None
        if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
            mode = node.args[1].value
        for keyword in node.keywords:
            if keyword.arg == "mode" and isinstance(keyword.value, ast.Constant):
                mode = keyword.value.value
        if isinstance(mode, str) or mode is None:
            if is_text_mode(mode) and OPEN_RE.search(lines[node.lineno - 1]):
                found.append(node.lineno)
    return sorted(set(found))


def apply(path: Path) -> int:
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines(keepends=True)
    target_lines = set(candidates(path))
    changed = 0
    for index in target_lines:
        original = lines[index - 1]
        updated = OPEN_RE.sub(replacement, original, count=1)
        if updated != original:
            lines[index - 1] = updated
            changed += 1
    if changed:
        path.write_text("".join(lines), encoding="utf-8", newline="")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default="noethys")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    root = Path(args.root)
    total = 0
    for path in sorted(root.rglob("*.py")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        lines = candidates(path)
        if not lines:
            continue
        if args.apply:
            count = apply(path)
            total += count
            print(f"{path}: {count} ouverture(s) modernisée(s)")
        else:
            total += len(lines)
            for lineno in lines:
                print(f"{path}:{lineno}: ouverture texte littérale sans encoding=\"utf-8\"")

    if args.apply:
        print(f"\n{total} ouverture(s) modernisée(s).")
        return 0
    print(f"\n{total} ouverture(s) sûre(s) à moderniser.")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
