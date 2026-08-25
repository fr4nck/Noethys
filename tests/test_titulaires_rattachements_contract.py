#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import types
import unittest
from pathlib import Path


SOURCE = Path("noethys/Utils/UTILS_Titulaires.py")


def load_get_familles_rattachees(resultats):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    fonction = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "GetFamillesRattachees"
    )
    module = ast.Module(body=[fonction], type_ignores=[])
    ast.fix_missing_locations(module)

    class FakeDB:
        def __init__(self):
            self._resultats = iter(resultats)

        def ExecuterReq(self, req):
            return True

        def ResultatReq(self):
            return next(self._resultats)

        def Close(self):
            return None

    namespace = {
        "GestionDB": types.SimpleNamespace(DB=FakeDB),
        "_": lambda texte: texte,
    }
    exec(compile(module, str(SOURCE), "exec"), namespace)
    return namespace["GetFamillesRattachees"]


class TitulairesRattachementsContractTests(unittest.TestCase):
    def test_trois_titulaires_conservent_tous_les_noms(self):
        fonction = load_get_familles_rattachees([
            [(1, 10, 1, 1, 100)],
            [
                (1, 101, 10, 1, 1, "Alpha", "Ana"),
                (2, 102, 10, 1, 1, "Beta", "Ben"),
                (3, 103, 10, 1, 1, "Gamma", "Gus"),
            ],
        ])

        resultat = fonction(IDindividu=999)

        self.assertEqual(
            resultat[10]["nomsTitulaires"],
            "Alpha Ana, Beta Ben et Gamma Gus",
        )

    def test_categorie_inconnue_ne_provoque_pas_de_variable_locale_absente(self):
        fonction = load_get_familles_rattachees([
            [(1, 10, 99, 0, 100)],
            [],
        ])

        resultat = fonction(IDindividu=999)

        self.assertEqual(resultat[10]["IDcategorie"], 99)
        self.assertEqual(resultat[10]["nomCategorie"], "catégorie inconnue")


if __name__ == "__main__":
    unittest.main()
