# -*- coding: utf-8 -*-
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FICHIER = ROOT / "noethys" / "Utils" / "UTILS_Texte.py"


def _charger_module():
    spec = importlib.util.spec_from_file_location("utils_texte_contract", FICHIER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_convert_str_to_liste_ne_partage_pas_un_repli_vide():
    module = _charger_module()
    premier = module.ConvertStrToListe(None)
    second = module.ConvertStrToListe("")

    assert premier == []
    assert second == []
    assert premier is not second

    premier.append(1)
    assert second == []


def test_convert_str_to_liste_copie_le_repli_fourni_par_l_appelant():
    module = _charger_module()
    repli = [7]
    resultat = module.ConvertStrToListe(None, siVide=repli)

    assert resultat == [7]
    assert resultat is not repli

    resultat.append(8)
    assert repli == [7]


def test_convert_str_to_liste_conserve_la_conversion_normale():
    module = _charger_module()
    assert module.ConvertStrToListe("1;2;3") == [1, 2, 3]
