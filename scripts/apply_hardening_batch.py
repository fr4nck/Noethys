#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Applique les corrections mécaniques de la passe globale de hardening.

Le script est volontairement étroit : aucune reformattage global, aucune
transformation SQL et aucune modification métier implicite.

Lot courant :
- remplacer les ``except:`` nus du code Noethys de premier niveau par
  ``except Exception:`` afin de ne plus avaler ``SystemExit``,
  ``KeyboardInterrupt`` et les autres ``BaseException`` ;
- corriger le rafraîchissement de la recherche individus après lecture d'un
  code-barres famille, qui pouvait appeler ``BarreRecherche.MAJ()`` alors que
  cette méthode n'existe pas.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
EXCLUDED_PARTS = {"ObjectListView", "Outils"}


def iter_first_party_python():
    for path in NOETHYS.rglob("*.py"):
        try:
            relative = path.relative_to(NOETHYS)
        except ValueError:
            continue
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        yield path


def replace_bare_excepts(path: Path) -> int:
    source = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return 0

    bare_lines = sorted(
        {node.lineno for node in ast.walk(tree) if isinstance(node, ast.ExceptHandler) and node.type is None},
        reverse=True,
    )
    if not bare_lines:
        return 0

    lines = source.splitlines(keepends=True)
    changed = 0
    for lineno in bare_lines:
        index = lineno - 1
        line = lines[index]
        replaced, n = re.subn(r"\bexcept\s*:", "except Exception:", line, count=1)
        if n != 1:
            raise RuntimeError(f"Impossible de resserrer le except nu : {path}:{lineno}")
        lines[index] = replaced
        changed += 1

    new_source = "".join(lines)
    # Le fichier modifié doit rester syntaxiquement valide avant écriture.
    ast.parse(new_source)
    path.write_text(new_source, encoding="utf-8")
    return changed


def fix_individual_barcode_refresh() -> bool:
    path = NOETHYS / "Ol" / "OL_Individus.py"
    source = path.read_text(encoding="utf-8")
    old = '''                    # MAJ du remplissage\n                    if self.GetGrandParent().GetName() == "general" :\n                        self.GetGrandParent().MAJ() \n                    else:\n                        self.MAJ() \n                    self.OnCancel(None)\n'''
    new = '''                    # Actualise le conteneur métier quand il expose MAJ,\n                    # sinon recharge directement la liste. BarreRecherche n'a\n                    # volontairement pas de méthode MAJ propre.\n                    actualiser = getattr(self.parent, "MAJ", None)\n                    if callable(actualiser):\n                        actualiser()\n                    else:\n                        self.listView.MAJ(forceActualisation=True)\n                    self.OnCancel(None)\n'''
    if old not in source:
        if new in source:
            return False
        raise RuntimeError("Motif code-barres famille introuvable dans OL_Individus.py")
    source = source.replace(old, new, 1)
    ast.parse(source)
    path.write_text(source, encoding="utf-8")
    return True


def count_bare_excepts() -> int:
    total = 0
    for path in iter_first_party_python():
        source = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        total += sum(
            1 for node in ast.walk(tree)
            if isinstance(node, ast.ExceptHandler) and node.type is None
        )
    return total


def main() -> int:
    bare_before = count_bare_excepts()
    changed_files = 0
    changed_handlers = 0
    for path in iter_first_party_python():
        changed = replace_bare_excepts(path)
        if changed:
            changed_files += 1
            changed_handlers += changed

    barcode_changed = fix_individual_barcode_refresh()
    bare_after = count_bare_excepts()
    if bare_after != 0:
        raise SystemExit(f"Hardening incomplet : {bare_after} except nu(s) subsistent")

    print(f"except nus : {bare_before} -> {bare_after} ({changed_handlers} resserrés dans {changed_files} fichiers)")
    print(f"code-barres famille : {'corrigé' if barcode_changed else 'déjà corrigé'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
