#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Applique les corrections ciblées d'API Python supprimées.

Chaque remplacement est idempotent et associé à l'audit
``audit_deprecated_runtime_apis.py``. Aucun remplacement générique n'est fait
sans connaître le type/usage du code concerné.
"""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"


def replace_idempotent(relative, old, new, marker):
    path = NOETHYS / relative
    source = path.read_text(encoding="utf-8")
    if old in source:
        source = source.replace(old, new, 1)
        ast.parse(source)
        path.write_text(source, encoding="utf-8")
        return True
    if marker in source:
        return False
    raise RuntimeError(f"Motif runtime introuvable : {relative} / {marker}")


def replace_all_idempotent(relative, old, new, expected_count):
    path = NOETHYS / relative
    source = path.read_text(encoding="utf-8")
    old_count = source.count(old)
    new_count = source.count(new)
    if old_count:
        if old_count != expected_count:
            raise RuntimeError(
                f"Nombre inattendu de motifs runtime : {relative}: {old_count} != {expected_count}"
            )
        source = source.replace(old, new)
        ast.parse(source)
        path.write_text(source, encoding="utf-8")
        return True
    if new_count >= expected_count:
        return False
    raise RuntimeError(f"Motif runtime introuvable : {relative} / {old}")


def fix_updater_thread_state():
    return replace_idempotent(
        "Dlg/DLG_Updater.py",
        "downloadEnCours = self.downloader.isAlive()",
        "downloadEnCours = self.downloader.is_alive()",
        "downloadEnCours = self.downloader.is_alive()",
    )


def fix_processing_dialog_thread_states():
    changed = False
    for relative in (
        "Dlg/DLG_Recalculer_prestations.py",
        "Dlg/DLG_Saisie_lot_conso_global.py",
        "Dlg/DLG_Saisie_lot_forfaits_credits.py",
    ):
        changed = replace_all_idempotent(
            relative,
            "TraitmentEnCours = self.traitement.isAlive()",
            "TraitmentEnCours = self.traitement.is_alive()",
            expected_count=2,
        ) or changed
    return changed


def main():
    fixes = {
        "thread updater is_alive": fix_updater_thread_state(),
        "threads traitements is_alive": fix_processing_dialog_thread_states(),
    }
    for label, changed in fixes.items():
        print(f"{label}: {'corrigé' if changed else 'déjà corrigé'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
