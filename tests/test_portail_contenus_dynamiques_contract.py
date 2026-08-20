#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DLG = ROOT / "noethys" / "Dlg" / "DLG_Saisie_portail_bloc.py"
CTRL = ROOT / "noethys" / "Ctrl" / "CTRL_Portail_contenu_externe.py"


def test_editeur_de_bloc_expose_le_contenu_externe_sans_nouvelle_categorie_persistante():
    dlg = DLG.read_text(encoding="utf-8")
    ctrl = CTRL.read_text(encoding="utf-8")

    assert '_(u"Contenu externe")' in dlg
    assert "CTRL_Portail_contenu_externe.CTRL" in dlg
    assert 'categorie = _("bloc_texte")' in dlg
    assert "EstContenuExterne" in dlg
    assert "construire_iframe" in ctrl
    assert "texte_html" in ctrl
    assert "parametres" in ctrl
