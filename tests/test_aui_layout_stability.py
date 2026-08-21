# -*- coding: utf-8 -*-
"""Garde-fous contre la réécriture dynamique des perspectives wxAUI."""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AuiLayoutStabilityTests(unittest.TestCase):
    def _read(self):
        text = (ROOT / "noethys/Utils/UTILS_Aui.py").read_text(encoding="utf-8")
        ast.parse(text)
        return text

    def test_repens_ne_pilote_plus_la_geometrie_des_panes(self):
        text = self._read()
        self.assertIn("PERSPECTIVE_LAYOUT_VERSION = 7", text)
        self.assertNotIn("_InstallerResponsive", text)
        self.assertNotIn("_ConfigurerWorkspace", text)
        self.assertNotIn("EVT_AUI_PANE_ACTIVATED", text)
        self.assertNotIn("SetDockSizeConstraint", text)
        self.assertNotIn("dock_proportion", text)

    def test_rechargement_perspective_ne_la_recrit_pas_apres_coup(self):
        text = self._read()
        debut = text.index("def ChargerPerspective")
        bloc = text[debut:]
        self.assertIn("manager.LoadPerspective(candidate)", bloc)
        self.assertIn("ConfigurerManager(manager)", bloc)
        self.assertLess(
            bloc.index("manager.LoadPerspective(candidate)"),
            bloc.index("ConfigurerManager(manager)"),
        )

    def test_reequilibrage_est_un_simple_refresh(self):
        text = self._read()
        debut = text.index("def ReequilibrerWorkspace")
        fin = text.index("def ConfigurerManager", debut)
        bloc = text[debut:fin]
        self.assertIn("manager.Update()", bloc)
        self.assertNotIn("MinSize", bloc)
        self.assertNotIn("BestSize", bloc)
        self.assertNotIn("Right", bloc)
        self.assertNotIn("Layer", bloc)
        self.assertNotIn("Row", bloc)
        self.assertNotIn("Position", bloc)


if __name__ == "__main__":
    unittest.main()
