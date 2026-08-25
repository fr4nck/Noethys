# -*- coding: utf-8 -*-
import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FICHIER = ROOT / "noethys" / "Ol" / "OL_Etiquettes.py"


def _charger_get_infos_coches():
    arbre = ast.parse(FICHIER.read_text(encoding="utf-8"), filename=str(FICHIER))
    fonction = next(
        noeud
        for noeud in ast.walk(arbre)
        if isinstance(noeud, ast.FunctionDef) and noeud.name == "GetInfosCoches"
    )
    module = ast.Module(body=[fonction], type_ignores=[])
    ast.fix_missing_locations(module)
    espace = {}
    exec(compile(module, str(FICHIER), "exec"), espace)
    return espace["GetInfosCoches"]


class FauxTrack:
    def __init__(self, donnees):
        self.donnees = donnees

    def GetDict(self):
        return dict(self.donnees)


class FauxListe:
    def __init__(self, tracks, dict_inscrits=None):
        self.tracks = tracks
        self.dict_inscrits = dict_inscrits or {}
        self.dictOrganisme = {"{ORGANISME}": "Association"}

    def GetTracksCoches(self):
        return self.tracks


class EtiquettesPython3DictViewTests(unittest.TestCase):
    def test_le_premier_individu_fournit_le_nom_de_famille(self):
        get_infos = _charger_get_infos_coches()
        liste = FauxListe(
            [FauxTrack({"{IDFAMILLE}": 42, "{FAMILLE_NOM}": "Famille"})],
            {
                42: {
                    7: {"nom_complet_individu": "DUPONT Alice"},
                    8: {"nom_complet_individu": "DUPONT Bob"},
                },
            },
        )

        resultat = get_infos(liste)

        self.assertEqual(resultat[0]["{FAMILLE_NOM}"], "DUPONT Alice")
        self.assertEqual(resultat[0]["{ORGANISME}"], "Association")

    def test_une_famille_sans_individu_conserve_son_nom(self):
        get_infos = _charger_get_infos_coches()
        liste = FauxListe([
            FauxTrack({"{IDFAMILLE}": 42, "{FAMILLE_NOM}": "Famille DUPONT"}),
        ])

        resultat = get_infos(liste)

        self.assertEqual(resultat[0]["{FAMILLE_NOM}"], "Famille DUPONT")


if __name__ == "__main__":
    unittest.main()
