# -*- coding: utf-8 -*-
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DLG_FAMILLE = ROOT / "noethys" / "Dlg" / "DLG_Famille.py"
UTIL_CONVENTION = ROOT / "noethys" / "Utils" / "UTILS_Impression_convention.py"


def test_family_tools_exposes_convention_generation():
    source = DLG_FAMILLE.read_text(encoding="utf-8")
    assert "Générer une convention d'encadrement sportif" in source
    assert "def MenuGenererConvention" in source
    assert "UTILS_Impression_convention.Impression(IDfamille=self.IDfamille)" in source


def test_convention_engine_is_dedicated_and_questionnaire_driven():
    source = UTIL_CONVENTION.read_text(encoding="utf-8")
    assert 'QUESTION_SAISON = u"Saison de la convention"' in source
    assert 'QUESTION_TYPE = u"Type de structure"' in source
    assert "UTILS_Questionnaires.ChampsEtReponses" in source
    assert "DLG_Impression_devis" not in source
    assert "UTILS_Impression_facture" not in source
