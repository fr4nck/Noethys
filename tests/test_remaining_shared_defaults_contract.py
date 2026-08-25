# -*- coding: utf-8 -*-
import ast
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _charger_fonction(chemin, nom, contexte=None):
    path = ROOT / "noethys" / chemin
    arbre = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    fonctions = [
        noeud
        for noeud in ast.walk(arbre)
        if isinstance(noeud, ast.FunctionDef) and noeud.name == nom
    ]
    if len(fonctions) != 1:
        raise AssertionError("Fonction %s introuvable ou ambiguë dans %s" % (nom, path))

    module = ast.Module(body=[fonctions[0]], type_ignores=[])
    ast.fix_missing_locations(module)
    espace = {} if contexte is None else dict(contexte)
    exec(compile(module, str(path), "exec"), espace)
    return espace[nom]


class _ConfigVide:
    def SetItemsConfig(self, parametres):
        self.parametres = parametres


class _BaseEnEchec:
    echec = 1


class RemainingSharedDefaultsTests(unittest.TestCase):
    def test_melange_dictionnaires_isole_les_appels_sans_destination(self):
        fonction = _charger_fonction("Dlg/DLG_Saisie_transport.py", "MelangeDictionnaires")

        premier = fonction(d2={"a": 1})
        second = fonction(d2={"b": 2})

        self.assertEqual(premier, {"a": 1})
        self.assertEqual(second, {"b": 2})
        self.assertIsNot(premier, second)

    def test_melange_dictionnaires_continue_de_modifier_la_destination_fournie(self):
        fonction = _charger_fonction("Dlg/DLG_Saisie_transport.py", "MelangeDictionnaires")
        destination = {"a": 1}

        resultat = fonction(destination, {"b": 2})

        self.assertIs(resultat, destination)
        self.assertEqual(destination, {"a": 1, "b": 2})

    def test_set_parametres_ne_retourne_pas_un_dictionnaire_partage(self):
        faux_wx = types.SimpleNamespace(GetApp=lambda: (_ for _ in ()).throw(RuntimeError()))
        fonction = _charger_fonction(
            "Utils/UTILS_Config.py",
            "SetParametres",
            {"wx": faux_wx, "FichierConfig": _ConfigVide},
        )

        premier = fonction()
        premier["contamination"] = True
        second = fonction()

        self.assertEqual(second, {})
        self.assertIsNot(premier, second)

    def test_parametres_categorie_isole_le_repli_si_la_base_est_indisponible(self):
        gestion_db = types.SimpleNamespace(DB=lambda nomFichier="": _BaseEnEchec())
        fonction = _charger_fonction(
            "Utils/UTILS_Parametres.py",
            "ParametresCategorie",
            {"GestionDB": gestion_db},
        )

        premier = fonction()
        premier["contamination"] = True
        second = fonction()

        self.assertEqual(second, {})
        self.assertIsNot(premier, second)


if __name__ == "__main__":
    unittest.main()
