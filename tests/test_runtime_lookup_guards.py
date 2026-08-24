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
            "Dlg/DLG_Famille_factures.py": "self.IDcompte_payeur = listeDonnees[0][0] if listeDonnees else 0",
            "Dlg/DLG_Saisie_prelevement_lot.py": "creancier_rue = creancier_cp = creancier_ville = creancier_siret = u\"\"",
            "Dlg/DLG_Saisie_reglement.py": "IDfamille, email_recus = None, None",
            "Utils/UTILS_Locations.py": "if not listeDonnees:",
            "Utils/UTILS_Organisateur.py": "logo, logo_update = None, None",
        }
        for relative, expected in checks.items():
            with self.subTest(relative=relative):
                self.assertIn(expected, self.source(relative))

    def test_stats_distance_origin_is_always_defined(self):
        source = self.source("Utils/UTILS_Stats_individus.py")
        self.assertIn("origine = None", source)
        self.assertIn("if origine is not None and key in dictDistances", source)

    def test_missing_product_returns_empty_availability(self):
        source = self.source("Utils/UTILS_Locations.py")
        marker = "if not listeDonnees:"
        self.assertIn(marker, source)
        self.assertIn("return {}", source[source.index(marker):source.index(marker) + 180])

    def test_avatar_query_failure_has_an_empty_fallback(self):
        source = self.source("Utils/UTILS_Utilisateurs.py")
        marker = "# chargement avatars"
        section = source[source.index(marker):source.index("dictAvatars = {}", source.index(marker))]
        self.assertIn("listeAvatars = []", section)

    def test_nomadhys_aborts_before_ready_state_when_listen_setup_fails(self):
        source = self.source("Ctrl/CTRL_Serveur_nomade.py")
        start = source.index("def StartServer")
        ready = source.index("Serveur prêt sur le port", start)
        section = source[start:ready]
        failure = section.index("Erreur dans le lancement du serveur Nomadhys [factory]")
        self.assertIn("return", section[failure:])


if __name__ == "__main__":
    unittest.main()
