# -*- coding: utf-8 -*-
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FICHIER = ROOT / "noethys" / "Utils" / "UTILS_Divers.py"


def _charger_module():
    spec = importlib.util.spec_from_file_location("utils_divers_contract", FICHIER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_dictionnaire_imbrique_ne_partage_pas_le_dictionnaire_par_defaut():
    module = _charger_module()

    premier = module.DictionnaireImbrique(cles=["a"], valeur=1)
    second = module.DictionnaireImbrique(cles=["b"], valeur=2)

    assert premier == {"a": 1}
    assert second == {"b": 2}
    assert premier is not second


def test_dictionnaire_imbrique_conserve_la_mutation_du_dictionnaire_fourni():
    module = _charger_module()
    donnees = {}

    resultat = module.DictionnaireImbrique(donnees, ["a", "b"], 3)

    assert resultat is donnees
    assert donnees == {"a": {"b": 3}}


def test_dictionnaire_imbrique_sans_cles_retourne_un_dictionnaire_vide_neuf():
    module = _charger_module()

    premier = module.DictionnaireImbrique()
    second = module.DictionnaireImbrique()

    assert premier == {}
    assert second == {}
    assert premier is not second
