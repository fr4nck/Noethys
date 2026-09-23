# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
NOETHYS_DIR = TESTS_DIR.parent / "noethys"
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))
if str(NOETHYS_DIR) not in sys.path:
    sys.path.insert(0, str(NOETHYS_DIR))

from _fixtures_noethys_db import BaseTest
from Data import DATA_Civilites
from Data import DATA_Fonctions_entites
from Utils import UTILS_Fonctions_entites as FE


class FonctionsEntitesTest(unittest.TestCase):

    def _base_deux_entites(self):
        base = BaseTest()
        base.inserer(
            "familles", ["IDfamille"], [(1,), (2,)]
        )
        base.inserer(
            "individus", ["IDindividu", "IDcivilite", "nom", "prenom", "travail_mail", "travail_tel"],
            [
                (1, 7, "CLUB TEST", "", None, None),
                (2, 10, "ECOLE TEST", "", None, None),
                (10, 3, "MARTIN", "Alice", "alice@example.org", "0102030405"),
            ],
        )
        base.inserer(
            "rattachements",
            ["IDrattachement", "IDindividu", "IDfamille", "IDcategorie", "titulaire"],
            [
                (100, 1, 1, 1, 1),
                (101, 10, 1, 1, 0),
                (200, 2, 2, 1, 1),
                (201, 10, 2, 1, 0),
            ],
        )
        return base

    def test_ecole_est_une_civilite_institutionnelle_stable(self):
        civilites = DATA_Civilites.GetDictCivilites()
        self.assertEqual(civilites[10]["civiliteLong"], "École")
        self.assertEqual(DATA_Fonctions_entites.GetTypeDepuisCivilite(10), "ecole")

    def test_type_entite_est_deduit_sans_modifier_la_famille(self):
        with self._base_deux_entites() as base:
            self.assertEqual(FE.GetTypeEntiteFamille(1, DB=base.db), "association")
            self.assertEqual(FE.GetTypeEntiteFamille(2, DB=base.db), "ecole")

    def test_meme_individu_peut_avoir_deux_fonctions_selon_entite(self):
        with self._base_deux_entites() as base:
            FE.EnregistrerFonctionRattachement(
                101, "Présidente", representant=True, signataire=True,
                defaut=True, DB=base.db,
            )
            FE.EnregistrerFonctionRattachement(
                201, "Directrice", representant=True, facturation=True,
                defaut=True, DB=base.db,
            )
            club = FE.GetFonctionRattachement(101, DB=base.db)
            ecole = FE.GetFonctionRattachement(201, DB=base.db)
            self.assertEqual(club["fonction"], "Présidente")
            self.assertEqual(ecole["fonction"], "Directrice")
            self.assertEqual(club["signataire"], 1)
            self.assertEqual(ecole["facturation"], 1)

    def test_contacts_sont_filtres_par_usage(self):
        with self._base_deux_entites() as base:
            FE.EnregistrerFonctionRattachement(
                101, "Présidente", representant=True, signataire=True,
                defaut=True, DB=base.db,
            )
            signataires = FE.GetContactsFamille(1, usage="signataire", DB=base.db)
            facturation = FE.GetContactsFamille(1, usage="facturation", DB=base.db)
            self.assertEqual(len(signataires), 1)
            self.assertEqual(signataires[0]["nom_complet"], "Mme MARTIN Alice")
            self.assertEqual(signataires[0]["mail"], "alice@example.org")
            self.assertEqual(facturation, [])

    def test_contact_defaut_est_prioritaire(self):
        with self._base_deux_entites() as base:
            base.inserer(
                "individus", ["IDindividu", "IDcivilite", "nom", "prenom"],
                [(11, 1, "DUPONT", "Paul")],
            )
            base.inserer(
                "rattachements",
                ["IDrattachement", "IDindividu", "IDfamille", "IDcategorie", "titulaire"],
                [(102, 11, 1, 1, 0)],
            )
            FE.EnregistrerFonctionRattachement(
                101, "Présidente", signataire=True, defaut=False, DB=base.db
            )
            FE.EnregistrerFonctionRattachement(
                102, "Trésorier", signataire=True, defaut=True, DB=base.db
            )
            choix = FE.GetRepresentantConvention(1, DB=base.db)
            self.assertEqual(choix["IDindividu"], 11)
            self.assertEqual(choix["fonction"], "Trésorier")

    def test_saisie_vide_supprime_la_metadonnee_sans_toucher_rattachement(self):
        with self._base_deux_entites() as base:
            FE.EnregistrerFonctionRattachement(
                101, "Présidente", representant=True, DB=base.db
            )
            FE.EnregistrerFonctionRattachement(101, DB=base.db)
            self.assertEqual(
                FE.GetFonctionRattachement(101, DB=base.db)["fonction"], ""
            )
            base.db.ExecuterReq(
                "SELECT IDindividu, IDfamille, IDcategorie, titulaire "
                "FROM rattachements WHERE IDrattachement=101;"
            )
            self.assertEqual(base.db.ResultatReq()[0], (10, 1, 1, 0))

    def test_suggestions_ecole_incluent_direction(self):
        fonctions = DATA_Fonctions_entites.GetFonctions("ecole", sexe="F")
        self.assertIn("Directrice", fonctions)
        self.assertIn("Enseignante", fonctions)


if __name__ == "__main__":
    unittest.main()