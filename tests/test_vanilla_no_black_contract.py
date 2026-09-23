# -*- coding: utf-8 -*-
"""Contrats statiques du rendu clair Vanilla."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _source(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_vanilla_normalise_le_theme_noir():
    source = _source("noethys/Utils/UTILS_Interface.py")
    assert 'if theme in ("Vert", "Bleu")' in source
    assert 'return _NormaliseThemeVanilla(UTILS_Customize.GetValeur' in source
    assert 'theme = GetTheme()' in source


def test_liste_desactivee_ne_prend_plus_le_fond_systeme():
    source = _source("noethys/Ctrl/CTRL_ObjectListView.py")
    debut = source.index("    def Activation(self, etat=True):")
    fin = source.index("    def SetColumns(", debut)
    activation = source[debut:fin]
    assert "SYS_COLOUR_FRAMEBK" not in activation
    assert "self.stEmptyListMsg.SetBackgroundColour(self.GetBackgroundColour())" in activation
