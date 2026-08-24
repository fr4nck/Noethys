#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"


class RuntimeLookupGuardTests(unittest.TestCase):
    def source(self, relative):
        return (NOETHYS / relative).read_text(encoding="utf-8")

    def test_known_direct_result_accesses_are_guarded(self):
        checks = {
            "Ctrl/CTRL_Informations.py": "donneesFamille = self.DB.ResultatReq()",
            "Dlg/DLG_Noedoc.py": "buffer = donneesLogo[0][0] if donneesLogo else None",
            "Ol/OL_Inscriptions.py": "if donneesOrganisateur:",
            "Ctrl/CTRL_Detail_aides.py": "self.IDcompte_payeur = listeDonnees[0][0] if listeDonnees else 0",
            "Ctrl/CTRL_Repartition.py": "self.IDcompte_payeur = listeDonnees[0][0] if listeDonnees else 0",
            "Utils/UTILS_Locations.py": "if not listeDonnees:",
            "Utils/UTILS_Organisateur.py": "if listeDonnees:",
        }
        for relative, expected in checks.items():
            with self.subTest(relative=relative):
                self.assertIn(expected, self.source(relative))

    def test_stats_distance_origin_is_always_defined(self):
        source = self.source("Utils/UTILS_Stats_individus.py")
        self.assertIn("origine = None", source)
        self.assertIn("if origine is not None and key in dictDistances", source)

    def test_reglement_email_lookup_handles_missing_family(self):
        source = self.source("Dlg/DLG_Saisie_reglement.py")
        self.assertIn("IDfamille, email_recus = None, None", source)


if __name__ == "__main__":
    unittest.main()
