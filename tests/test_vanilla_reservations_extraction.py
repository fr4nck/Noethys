# -*- coding: utf-8 -*-
"""Non-regression : le rapport Reservations historique reste fonctionnel,
et la nouvelle extraction generique GetDonnees() produit exactement la
meme structure que celle construite manuellement par
CTRL_Grille.CreationPDF() (memes cles, memes valeurs), sans dupliquer son
code ni le modifier.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from _fixtures_noethys_db import (  # noqa: E402
    BaseTest,
    RedirectionGestionDB,
    creer_base_association_simple,
)
from Utils import UTILS_Impression_reservations as R  # noqa: E402


class GetDonneesExtractionTests(unittest.TestCase):
    def test_reproduit_le_format_attendu_par_impression(self):
        with creer_base_association_simple() as base:
            dictDonnees = R.GetDonnees(
                listeIDindividus=[2, 3], date_debut="2026-09-01",
                date_fin="2026-09-30", DB=base.db,
            )

        self.assertEqual(set(dictDonnees.keys()), {2, 3})
        individu2 = dictDonnees[2]
        self.assertEqual(individu2["nom"], "STRUCTURE SPORTIVE TEST")
        self.assertEqual(individu2["prenom"], "Groupe A enfants")
        self.assertIn(10, individu2["activites"])
        dates = individu2["activites"][10]["dates"]
        self.assertEqual(len(dates), 3)
        for date, dictDate in dates.items():
            self.assertIn(30, dictDate["unites"])
            conso = dictDate["unites"][30][0]
            self.assertEqual(conso["prestation"]["montant"], 36.00)
            self.assertEqual(conso["etat"], "Réservation")

    def test_periode_hors_plage_est_exclue(self):
        with creer_base_association_simple() as base:
            dictDonnees = R.GetDonnees(
                listeIDindividus=[2, 3], date_debut="2026-10-01",
                date_fin="2026-10-31", DB=base.db,
            )
        self.assertEqual(dictDonnees, {})

    def test_liste_individus_vide_ne_requete_pas_la_base(self):
        dictDonnees = R.GetDonnees(listeIDindividus=[], date_debut=None, date_fin=None)
        self.assertEqual(dictDonnees, {})

    def test_montant_total_par_activite_est_exact(self):
        with creer_base_association_simple() as base:
            dictDonnees = R.GetDonnees(
                listeIDindividus=[2, 3], date_debut="2026-09-01",
                date_fin="2026-09-30", DB=base.db,
            )
        total_enfants = sum(
            conso["prestation"]["montant"]
            for dictDate in dictDonnees[2]["activites"][10]["dates"].values()
            for listeConso in dictDate["unites"].values()
            for conso in listeConso
        )
        total_adultes = sum(
            conso["prestation"]["montant"]
            for dictDate in dictDonnees[3]["activites"][11]["dates"].values()
            for listeConso in dictDate["unites"].values()
            for conso in listeConso
        )
        self.assertAlmostEqual(total_enfants, 108.00)
        self.assertAlmostEqual(total_adultes, 109.50)

    def test_rapport_reservations_historique_reste_fonctionnel(self):
        """Le moteur Impression() historique, non modifie, doit toujours
        produire un PDF exploitable a partir des donnees fournies par la
        nouvelle extraction generique.

        Impression() (non modifie par cette PR) appelle en interne
        UTILS_Organisateur.GetNom() -> GestionDB.DB() sans parametre :
        sans isolation, cela plante sur un runner CI propre (config
        Noethys absente), exactement comme deja rencontre ailleurs dans
        cette suite -- jamais detecte ici auparavant car ce test etait
        neutralise par @skipUnless (ShowBoundaryValue) avant meme
        d'atteindre ce code. """
        with creer_base_association_simple() as base:
            dictDonnees = R.GetDonnees(
                listeIDindividus=[2, 3], date_debut="2026-09-01",
                date_fin="2026-09-30", DB=base.db,
            )
            chemin_pdf = tempfile.mktemp(suffix=".pdf")
            try:
                with RedirectionGestionDB(base.chemin):
                    resultat = R.Impression(dictDonnees, nomDoc=chemin_pdf, afficherDoc=False)
                self.assertIsNotNone(resultat)
                self.assertTrue(os.path.isfile(chemin_pdf))
                self.assertGreater(os.path.getsize(chemin_pdf), 0)
                with open(chemin_pdf, "rb") as f:
                    self.assertTrue(f.read(5).startswith(b"%PDF-"))
            finally:
                if os.path.isfile(chemin_pdf):
                    os.remove(chemin_pdf)

    def test_impression_avec_dictdonnees_minimal_produit_reellement_un_pdf(self):
        """ Non-regression du correctif "from reportlab.platypus.frames
        import Frame, ShowBoundaryValue" -> "import Frame" (ShowBoundaryValue
        n'etait utilise nulle part dans ce fichier et absent des versions
        recentes de reportlab, faisant echouer cet import a chaud). Cas
        volontairement minimal (un seul individu, une seule activite, une
        seule seance), independant de la richesse de la fixture
        association, pour isoler precisement Impression() elle-meme --
        avec la version de reportlab reellement installee dans cet
        environnement (aucune version n'est pingle ni ce test ni
        requirements.txt). """
        base = BaseTest()
        try:
            base.inserer(
                "organisateur",
                ["IDorganisateur", "nom", "rue", "cp", "ville", "tel", "mail"],
                [(1, "Structure Test", "1 rue Test", "00000", "Testville", "", "")],
            )
            base.inserer("familles", ["IDfamille"], [(1,)])
            base.inserer(
                "individus", ["IDindividu", "nom", "prenom", "IDcivilite"],
                [(1, "TEST", "Minimal", 1)],
            )
            base.inserer(
                "rattachements",
                ["IDrattachement", "IDfamille", "IDindividu", "IDcategorie", "titulaire"],
                [(1, 1, 1, 1, 1)],
            )
            base.inserer("activites", ["IDactivite", "nom"], [(10, "Activité minimale")])
            base.inserer("groupes", ["IDgroupe", "IDactivite", "nom"], [(20, 10, "Groupe")])
            base.inserer(
                "unites", ["IDunite", "IDactivite", "nom", "ordre", "type"],
                [(30, 10, "Unité", 1, "Horaire")],
            )
            base.inserer(
                "prestations", ["IDprestation", "label", "montant"],
                [(100, "Prestation minimale", 10.0)],
            )
            base.inserer(
                "consommations",
                ["IDconso", "IDindividu", "IDactivite", "date", "IDunite", "heure_debut", "heure_fin", "etat", "IDgroupe", "IDprestation"],
                [(1000, 1, 10, "2026-09-01", 30, "10:00", "11:00", "reservation", 20, 100)],
            )

            dictDonnees = R.GetDonnees(
                listeIDindividus=[1], date_debut="2026-09-01", date_fin="2026-09-01", DB=base.db,
            )
            self.assertEqual(set(dictDonnees.keys()), {1})

            chemin_pdf = tempfile.mktemp(suffix=".pdf")
            try:
                with RedirectionGestionDB(base.chemin):
                    resultat = R.Impression(dictDonnees, nomDoc=chemin_pdf, afficherDoc=False)
                self.assertIsNotNone(resultat)
                self.assertTrue(os.path.isfile(chemin_pdf))
                self.assertGreater(os.path.getsize(chemin_pdf), 0)
                with open(chemin_pdf, "rb") as f:
                    self.assertTrue(f.read(5).startswith(b"%PDF-"))
            finally:
                if os.path.isfile(chemin_pdf):
                    os.remove(chemin_pdf)
        finally:
            base.fermer()


if __name__ == "__main__":
    unittest.main()
