#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Contrat léger pour garder les règles UI/UX d'Upgrade Noethys visibles dans le dépôt."""

from pathlib import Path


def test_modernisation_ui_rules_are_documented():
    root = Path(__file__).resolve().parents[1]
    path = root / "docs" / "UPGRADE_UI_UX_RULES.md"
    texte = path.read_text(encoding="utf-8")

    assert "monkey-patch" in texte
    assert "wx.SplitterWindow" in texte
    assert "AuiManager" in texte
    assert "Versionner les perspectives" in texte
    assert "Si un vieux layout empêche l'interface de s'adapter" in texte
