#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import unittest
from pathlib import Path


SOURCE_PATH = Path(__file__).resolve().parents[1] / "noethys" / "Ol" / "OL_Individus.py"


class IndividualsRuntimeHardeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE_PATH.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)

    def test_rfid_duplicate_badge_is_rejected_before_database_lookup(self):
        start = self.source.index("def OnTimerRFID")
        end = self.source.index("class BarreRecherche", start)
        section = self.source[start:end]
        duplicate_guard = section.index("if self.dernierRFID == IDbadge")
        query = section.index("FROM questionnaire_reponses")
        self.assertLess(duplicate_guard, query)

    def test_rfid_handler_does_not_block_ui_or_stop_its_timer(self):
        start = self.source.index("def OnTimerRFID")
        end = self.source.index("class BarreRecherche", start)
        section = self.source[start:end]
        self.assertNotIn("time.sleep", section)
        self.assertNotIn("self.timer_rfid.Stop()", section)

    def test_rfid_filtered_individual_does_not_raise_key_error(self):
        start = self.source.index("def OnTimerRFID")
        end = self.source.index("class BarreRecherche", start)
        section = self.source[start:end]
        self.assertIn("self.dictTracks.get(IDindividu)", section)

    def test_new_family_dialog_is_destroyed(self):
        start = self.source.index("def Ajouter(self, event)")
        end = self.source.index("def Modifier(self, event)", start)
        section = self.source[start:end]
        self.assertIn("dlg.Destroy()", section)

    def test_empty_initial_database_does_not_turn_list_data_into_none(self):
        self.assertIn("and self.donnees", self.source)

    def test_invalid_individual_barcode_resets_individual_id(self):
        start = self.source.index("# Si code-barres individu saisi")
        end = self.source.index("# Si code-barres famille saisi", start)
        section = self.source[start:end]
        self.assertIn("except Exception:\n                IDindividu = None", section)


if __name__ == "__main__":
    unittest.main()
