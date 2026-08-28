#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import unittest
from pathlib import Path

from scripts import audit_branch_assignment_gaps


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

    def test_consumption_state_mapping_covers_historical_domain(self):
        assignment = next(
            node for node in self.tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "ETATS_CONSOMMATION" for target in node.targets)
        )
        mapping = ast.literal_eval(assignment.value)
        self.assertEqual(
            {
                "reservation": ("reservation", "reservation"),
                "attente": ("attente", "reservation"),
                "refus": ("refus", "reservation"),
                "present": ("reservation", "present"),
                "absenti": ("reservation", "absenti"),
                "absentj": ("reservation", "absentj"),
            },
            mapping,
        )

    def test_unknown_consumption_state_and_action_are_explicit_errors(self):
        self.assertIn('_(u"État de consommation inconnu : %s") % track.etat', self.source)
        self.assertIn('_(u"Action de consommation inconnue : %s") % track.action', self.source)
        self.assertIn('elif track.action == "supprimer"', self.source)

    def test_targeted_branch_assignment_gaps_are_gone(self):
        findings = audit_branch_assignment_gaps.scan_file(SOURCE_PATH.resolve())
        targets = {
            ("ArchiverFichiers", "intro"),
            ("run", "mode"),
            ("run", "etat"),
            ("run", "resultat"),
        }
        remaining = [
            item for item in findings
            if (item["function"], item["name"]) in targets
        ]
        self.assertEqual([], remaining)


if __name__ == "__main__":
    unittest.main()
