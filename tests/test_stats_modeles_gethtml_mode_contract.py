#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contrat du mode de Utils/UTILS_Stats_modeles.py::HTML.GetHTML.

``html`` n'est initialisé que pour les modes 'affichage' et 'impression'.
Ces deux valeurs sont les seules jamais transmises par les appelants du
dépôt (Dlg/DLG_Stats.py). Un mode hors contrat doit désormais lever une
erreur explicite plutôt que provoquer un ``UnboundLocalError`` silencieux
au moment du ``return html``.
"""

import ast
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "noethys" / "Utils" / "UTILS_Stats_modeles.py"


def load_gethtml():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    class_node = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "HTML"
    )
    func_node = next(
        node for node in class_node.body
        if isinstance(node, ast.FunctionDef) and node.name == "GetHTML"
    )
    module = ast.Module(body=[func_node], type_ignores=[])
    ast.fix_missing_locations(module)
    ns = {
        "_": lambda value: value,
        "ConvertitCouleur": lambda couleur: "#000000",
        "DateEngFr": lambda date: date,
    }
    exec(compile(module, str(SOURCE), "exec"), ns)
    return ns["GetHTML"]


def make_self():
    fake = types.SimpleNamespace()
    fake.dictParametres = {
        "listeActivites": [1],
        "mode": "inscrits",
        "dictActivites": {1: "Activité test"},
    }
    fake.liste_objets = []
    return fake


class GetHTMLModeContractTests(unittest.TestCase):
    def test_affichage_mode_returns_html_document(self):
        GetHTML = load_gethtml()
        html = GetHTML(make_self(), mode="affichage")
        self.assertTrue(html.startswith("<HTML><BODY><FONT SIZE=-1>"))

    def test_impression_mode_returns_html_document(self):
        GetHTML = load_gethtml()
        html = GetHTML(make_self(), mode="impression")
        self.assertTrue(html.startswith("<HTML><BODY>"))

    def test_empty_activites_short_circuits_before_mode_check(self):
        GetHTML = load_gethtml()
        fake = make_self()
        fake.dictParametres = {"listeActivites": []}
        self.assertEqual(GetHTML(fake, mode="inconnu"), "")

    def test_unsupported_mode_is_explicit_instead_of_unbound(self):
        GetHTML = load_gethtml()
        with self.assertRaises(ValueError):
            GetHTML(make_self(), mode="inconnu")


if __name__ == "__main__":
    unittest.main()
