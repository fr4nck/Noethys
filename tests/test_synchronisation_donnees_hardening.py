#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "noethys" / "Dlg" / "DLG_Synchronisation_donnees.py"


class SynchronisationDonneesHardeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE_PATH.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)

    def test_anomaly_branch_does_not_read_previous_result(self):
        self.assertNotIn('texte = track.detail + u" -> " + resultat\n                    self.parent.parent.EcritLog(track.anomalie)', self.source)

    def test_single_existing_memo_is_updated_instead_of_duplicated(self):
        self.assertIn("if len(listeMemos) > 0 :", self.source)
        self.assertNotIn("if len(listeMemos) > 1 :", self.source)

    def test_thread_state_uses_python3_api(self):
        self.assertIn("self.traitement.is_alive()", self.source)
        self.assertNotIn("self.traitement.isAlive()", self.source)

    def test_anomaly_list_is_initialized_before_processing_try(self):
        marker = "nbre_tracks = len(self.parent.listeTracks)"
        section = self.source[self.source.index(marker):self.source.index("except Abort", self.source.index(marker))]
        self.assertLess(section.index("listeAnomalies = []"), section.index("try:"))


if __name__ == "__main__":
    unittest.main()
