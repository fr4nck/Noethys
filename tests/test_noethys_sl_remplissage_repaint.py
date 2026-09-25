#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CTRL = ROOT / "noethys" / "Ctrl" / "CTRL_Remplissage.py"


class TestRemplissageRepaint(unittest.TestCase):

    def test_reconstruction_est_batchée(self):
        source = CTRL.read_text(encoding="utf-8")
        self.assertIn("self.BeginBatch()", source)
        self.assertIn("self.EndBatch()", source)
        self.assertIn("self.Freeze()", source)
        self.assertIn("self.Thaw()", source)

    def test_un_seul_repaint_final(self):
        source = CTRL.read_text(encoding="utf-8")
        debut = source.index("    def MAJ(self):")
        fin = source.index("    def MAJ_donnees", debut)
        bloc = source[debut:fin]
        self.assertIn("self.ForceRefresh()", bloc)

        debut = source.index("    def MAJ_affichage(self):")
        fin = source.index("    def InitGrid", debut)
        bloc = source[debut:fin]
        self.assertNotIn("self.Refresh()", bloc)

    def test_double_buffering_est_active_si_disponible(self):
        source = CTRL.read_text(encoding="utf-8")
        self.assertIn("self.SetDoubleBuffered(True)", source)
        self.assertIn("self.GetGridWindow().SetDoubleBuffered(True)", source)


if __name__ == "__main__":
    unittest.main()
