#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Empêche A9068 de transformer une sélection vide en UPDATE global."""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "noethys" / "Utils" / "UTILS_Procedures.py"


def main() -> int:
    source = PATH.read_text(encoding="utf-8")
    marker = "        if not listeIDinscription:\n            DB.Close()\n            return\n"
    dangerous = '        condition = "IDinscription > 0"\n'

    if marker in source and dangerous not in source:
        print("Désinscription vide : déjà protégée")
        return 0

    old_selection = '''    if dlg.ShowModal() == wx.ID_OK:\n        listeIDinscription = [listeInscriptions[index][0]\n                              for index in dlg.GetSelections()]\n        dlg.Destroy()\n    else:\n'''
    new_selection = '''    if dlg.ShowModal() == wx.ID_OK:\n        listeIDinscription = [listeInscriptions[index][0]\n                              for index in dlg.GetSelections()]\n        dlg.Destroy()\n        if not listeIDinscription:\n            DB.Close()\n            return\n    else:\n'''

    old_condition = '''    if len(listeIDinscription) == 0:\n        condition = "IDinscription > 0"\n    elif len(listeIDinscription) == 1:\n        condition = "IDinscription IN (%d)" % listeIDinscription[0]\n    else:\n'''
    new_condition = '''    if len(listeIDinscription) == 1:\n        condition = "IDinscription IN (%d)" % listeIDinscription[0]\n    else:\n'''

    if old_selection not in source:
        raise RuntimeError("Bloc de sélection A9068 introuvable")
    if old_condition not in source:
        raise RuntimeError("Fallback UPDATE global A9068 introuvable")

    source = source.replace(old_selection, new_selection, 1)
    source = source.replace(old_condition, new_condition, 1)
    ast.parse(source)
    PATH.write_text(source, encoding="utf-8")
    print("Désinscription vide : correction appliquée")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
