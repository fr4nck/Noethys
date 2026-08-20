#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path


def test_dashboard_rules_are_explicit():
    root = Path(__file__).resolve().parents[1]
    texte = (root / "docs" / "DASHBOARD_MODERNISATION.md").read_text(encoding="utf-8")

    assert "jamais `.Float()` par défaut" in texte
    assert "Perspectives AUI versionnées" in texte
    assert "Messagerie" in texte
    assert "Semaine équipe" in texte
