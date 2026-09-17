# -*- coding: utf-8 -*-
"""Static contract for the dedicated sports convention engine."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "noethys" / "Utils" / "UTILS_Impression_convention.py"


def _source():
    return SOURCE.read_text(encoding="utf-8")


def test_convention_engine_is_valid_python():
    ast.parse(_source())


def test_convention_engine_does_not_reuse_devis_printer():
    source = _source()
    assert "UTILS_Impression_facture" not in source
    assert "DLG_Impression_devis" not in source


def test_convention_engine_uses_native_family_questionnaire_formatter():
    source = _source()
    assert "UTILS_Questionnaires.ChampsEtReponses(type=\"famille\")" in source
    assert "Saison de la convention" in source
    assert "Type de structure" in source


def test_convention_engine_uses_planning_hours_and_educator_labels():
    source = _source()
    assert "consommations.heure_debut" in source
    assert "consommations.heure_fin" in source
    assert "consommations.etiquettes" in source
    assert "Éducateur(s) sportif(s) prévu(s)" in source


def test_convention_engine_keeps_only_global_amount_in_annex():
    source = _source()
    assert "Montant prévisionnel global des interventions" in source
    # The annex table itself contains date/start/end/duration only.
    assert 'data = [[_(u"Date"), _(u"Début"), _(u"Fin"), _(u"Durée")]]' in source
