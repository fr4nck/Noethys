#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_editeur_portail_expose_un_bloc_contenu_externe_compatible():
    source = (ROOT / "noethys" / "Dlg" / "DLG_Saisie_portail_bloc.py").read_text(encoding="utf-8")

    assert "CTRL_Portail_contenu_externe" in source
    assert '_(u"Contenu externe")' in source
    assert '_("bloc_contenu_externe")' in source
    assert 'categorie = _("bloc_texte")' in source
    assert "EstContenuExterne(dictParametres)" in source


def test_controle_externe_stocke_configuration_et_html_dans_les_champs_existants():
    source = (ROOT / "noethys" / "Ctrl" / "CTRL_Portail_contenu_externe.py").read_text(encoding="utf-8")

    assert '"parametres": UTILS_Portail_contenus.serialiser_parametres(config)' in source
    assert '"texte_html": UTILS_Portail_contenus.construire_iframe(config)' in source
    assert '"texte_xml": None' in source
    assert "url_externe_valide" in source
