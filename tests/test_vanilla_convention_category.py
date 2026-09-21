# -*- coding: utf-8 -*-
"""Categorie 'convention' du concepteur Noedoc : additive, sans regression
sur les categories existantes (famille, facture) ni sur le modele
historique "Convention" (categorie="famille") deja present en base chez
au moins un client reel, qui doit rester lisible et inchange.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

NOETHYS_DIR = Path(__file__).resolve().parents[1] / "noethys"
if str(NOETHYS_DIR) not in sys.path:
    sys.path.insert(0, str(NOETHYS_DIR))

from Dlg import DLG_Modeles_docs  # noqa: E402
from Dlg import DLG_Noedoc  # noqa: E402


class CategorieConventionTests(unittest.TestCase):
    def test_convention_est_listee_dans_les_categories(self):
        codes = [code for code, label in DLG_Modeles_docs.LISTE_CATEGORIES]
        self.assertIn("convention", codes)

    def test_classe_convention_expose_les_champs_attendus(self):
        infos = DLG_Noedoc.Convention()
        self.assertEqual(infos.code, "convention")
        codes_champs = {champ[2] for champ in infos.champs}
        for attendu in (
            "{IDFAMILLE}",
            "{ORGANISATEUR_NOM}",
            "{CONVENTION_REPRESENTANT_NOM}",
            "{CONVENTION_REPRESENTANT_PRENOM}",
            "{CONVENTION_REPRESENTANT_NOM_COMPLET}",
            "{CONVENTION_REPRESENTANT_FONCTION}",
            "{CONVENTION_SAISON}",
            "{CONVENTION_PLANNING_DETAIL}",
            "{CONVENTION_PLANNING_TOTAL_HEURES}",
            "{CONVENTION_PLANNING_TOTAL_MONTANT}",
            "{CONVENTION_TARIF_HORAIRE}",
            "{CONVENTION_TARIF_ADULTE}",
            "{CONVENTION_TARIF_ENFANT}",
        ):
            self.assertIn(attendu, codes_champs)

    def test_convention_declare_un_cadre_principal_obligatoire(self):
        infos = DLG_Noedoc.Convention()
        cadres = [s for s in infos.speciaux if s["champ"] == "cadre_principal"]
        self.assertEqual(len(cadres), 1)
        self.assertTrue(cadres[0]["obligatoire"])

    def test_anciens_champs_representant_rattache_restent_inchanges(self):
        """L'ancien mecanisme {REPRESENTANT_RATTACHE_x_*} (utilise par un
        modele reel deja en base sous categorie='famille') n'est pas
        remplace : il continue d'etre expose par la categorie Famille,
        exactement comme avant l'ajout de la categorie Convention."""
        infos = DLG_Noedoc.Famille()
        codes_famille = {champ[2] for champ in infos.champs}
        self.assertTrue(any("REPRESENTANT_RATTACHE" in code for code in codes_famille))

    def test_categorie_famille_non_perturbee_par_convention(self):
        infos = DLG_Noedoc.Famille()
        self.assertEqual(infos.code, "famille")
        codes_champs = {champ[2] for champ in infos.champs}
        self.assertIn("{FAMILLE_NOM}", codes_champs)
        self.assertNotIn("{CONVENTION_SAISON}", codes_champs)

    def test_categorie_facture_non_perturbee_par_convention(self):
        infos = DLG_Noedoc.Facture()
        self.assertEqual(infos.code, "facture")
        codes_champs = {champ[2] for champ in infos.champs}
        self.assertIn("{NUM_FACTURE}", codes_champs)

    def test_dispatch_categorie_convention_est_cable_une_seule_fois(self):
        """Vérifie que le if categorie=="convention" est bien branché dans
        le dispatch unique de Dialog.__init__ (pas un deuxième registre
        concurrent)."""
        source = (NOETHYS_DIR / "Dlg" / "DLG_Noedoc.py").read_text(encoding="utf-8")
        occurrences = source.count('if categorie == "convention"')
        self.assertEqual(occurrences, 1)


if __name__ == "__main__":
    unittest.main()
