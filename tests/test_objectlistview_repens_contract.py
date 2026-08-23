# -*- coding: utf-8 -*-
"""Contrats statiques du raccord ObjectListView -> Repens Design."""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STYLE = ROOT / "noethys" / "Utils" / "UTILS_StyleRepens.py"
OLV_INIT = ROOT / "noethys" / "ObjectListView" / "__init__.py"


def _source(path):
    return path.read_text(encoding="utf-8")


def _fonction(source, nom):
    arbre = ast.parse(source)
    for noeud in arbre.body:
        if isinstance(noeud, (ast.FunctionDef, ast.AsyncFunctionDef)) and noeud.name == nom:
            return ast.get_source_segment(source, noeud) or ""
    raise AssertionError("Fonction %s introuvable" % nom)


class ObjectListViewRepensContractTests(unittest.TestCase):
    def test_repens_owns_default_olv_surfaces(self):
        source = _source(STYLE)
        liste = _fonction(source, "appliquer_liste_riche")

        self.assertIn('couleur("surface_container_lowest")', liste)
        self.assertIn('couleur("surface_container_low")', liste)
        self.assertIn('role_texte="on_surface_variant"', liste)
        self.assertNotIn("SetColumnWidth", liste)
        self.assertNotIn("SetItem", liste)
        self.assertNotIn("wx.Colour", liste)

    def test_group_headers_are_semantic(self):
        source = _source(STYLE)
        groupes = _fonction(source, "appliquer_groupes_liste")

        self.assertIn('police("label")', groupes)
        self.assertIn('couleur("primary_container")', groupes)
        self.assertIn('couleur("on_primary_container")', groupes)
        self.assertNotIn("wx.Colour", groupes)

    def test_vendored_olv_adapter_stays_thin_and_lazy(self):
        source = _source(OLV_INIT)

        self.assertIn("def _appliquer_repens", source)
        self.assertIn("from Utils import UTILS_StyleRepens as Style", source)
        self.assertIn("Style.appliquer_liste_riche(ctrl)", source)
        self.assertIn("Style.appliquer_groupes_liste(ctrl)", source)
        self.assertIn("def SetObjects", source)
        self.assertIn("def _InitializeImages", source)
        self.assertNotIn("SetColumnWidth", source)
        self.assertNotIn("SetItemBackgroundColour", source)
        self.assertNotIn("wx.Colour", source)

    def test_existing_business_adapter_remains_the_owner_of_columns(self):
        ctrl = _source(ROOT / "noethys" / "Ctrl" / "CTRL_ObjectListView.py")
        self.assertIn("class ColumnDefn", ctrl)
        self.assertIn("def SetColumns", ctrl)
        self.assertIn("def Filtrer", ctrl)
        self.assertIn("def GenerationContextMenu", ctrl)


if __name__ == "__main__":
    unittest.main()
