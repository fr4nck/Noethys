# -*- coding: utf-8 -*-
"""Deuxieme cas de recette : convention scolaire longue (type
"La Providence"), sur un modele et des donnees entierement fictifs et
anonymises. Verifie que le MEME moteur generique (aucun code specifique
a l'ecole) produit un PDF correct avec plusieurs groupes/cycles,
plusieurs periodes (dont un vrai trou de vacances) et une pagination
naturelle sur plusieurs pages.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
NOETHYS_DIR = TESTS_DIR.parent / "noethys"
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

import wx  # noqa: E402

_APP = wx.App(False)

from _fixtures_noethys_db import (  # noqa: E402
    RedirectionGestionDB,
    creer_base_ecole_simple,
    inserer_modele_convention_scolaire_fictif,
)
from Utils import UTILS_Convention_champs as CC  # noqa: E402
from Utils import UTILS_Impression_convention as UIC  # noqa: E402
from Utils import UTILS_Impression_reservations as RESA  # noqa: E402


def _lire_nombre_de_pages(chemin_pdf):
    """ Compte les pages sans dependance externe : chaque page produit un
    objet /Type /Page dans le PDF. Exclut explicitement /Type /Pages
    (le catalogue racine de l'arbre des pages, dont le nom est un
    prefixe de "/Type /Page" et faussait donc le compte de 1). """
    import re
    contenu = Path(chemin_pdf).read_bytes()
    return len(re.findall(rb"/Type\s*/Page(?!s)", contenu))


class ConventionScolaireIndividusTests(unittest.TestCase):
    """ Verifie ce que Noethys peut reellement reconstruire pour la
    famille ecole fictive, avant tout rendu PDF. """

    def test_trois_cycles_distincts_sont_rattaches(self):
        with creer_base_ecole_simple() as base:
            with RedirectionGestionDB(base.chemin):
                individus = CC._GetIndividusRattaches(2, DB=base.db)
        # 10 (titulaire école), 11 (représentant), 20/21/22 (3 cycles)
        self.assertEqual(len(individus), 5)

    def test_planning_couvre_les_trois_cycles_avec_gestion_du_trou(self):
        with creer_base_ecole_simple() as base:
            with RedirectionGestionDB(base.chemin):
                champs, dictDonnees = CC.GetChampsConvention(
                    IDfamille=2, listeIDindividus=[20, 21, 22], DB=base.db,
                )
        detail = champs["{CONVENTION_PLANNING_DETAIL}"]
        self.assertIn("CE2-CM1-CM2 CYCLE FICTIF 3", detail)
        self.assertIn("CP-CE1-CE2 CYCLE FICTIF 2", detail)
        self.assertIn("PS-MS-GS CYCLE FICTIF 1", detail)
        # Le cycle 2 (trou de vacances) a le même jour/horaire dans ses
        # deux blocs, mais l'écart de plusieurs mois doit produire deux
        # ConventionPeriode distinctes, jamais un seul intervalle
        # continu qui masquerait l'interruption réelle.
        periodes_cycle2 = [
            p for p in CC.ConstruirePeriodes(dictDonnees) if p.groupe == "CP-CE1-CE2 CYCLE FICTIF 2"
        ]
        self.assertEqual(len(periodes_cycle2), 2)
        for periode in periodes_cycle2:
            self.assertEqual(periode.nombre_seances, 4)

    def test_tarif_scolaire_unique_est_detecte(self):
        """ Les trois cycles de la fixture école partagent le même taux
        horaire (20€/h) : mode "unique" attendu, comme pour le cas réel
        La Providence (taux horaire unique constaté). """
        with creer_base_ecole_simple() as base:
            with RedirectionGestionDB(base.chemin):
                champs, dictDonnees = CC.GetChampsConvention(
                    IDfamille=2, listeIDindividus=[20, 21, 22], DB=base.db,
                )
        tarifs = CC.DetecterTarifs(dictDonnees)
        self.assertEqual(tarifs["mode"], "unique")
        self.assertEqual(tarifs["taux"], __import__("decimal").Decimal("20.00"))
        self.assertEqual(champs["{CONVENTION_TARIF_HORAIRE}"], 20.0)

    def test_representant_scolaire_reellement_nomme_est_retrouve(self):
        with creer_base_ecole_simple() as base:
            with RedirectionGestionDB(base.chemin):
                champs, _ = CC.GetChampsConvention(
                    IDfamille=2, listeIDindividus=[20, 21, 22], DB=base.db,
                )
        self.assertEqual(champs["{CONVENTION_REPRESENTANT_PRENOM}"], "Alice")
        self.assertEqual(champs["{CONVENTION_REPRESENTANT_NOM}"], "MARTIN")


class ConventionScolairePDFTests(unittest.TestCase):
    def test_pipeline_complet_ecole_produit_un_pdf_multipage_correct(self):
        with creer_base_ecole_simple() as base:
            IDmodele = inserer_modele_convention_scolaire_fictif(base)
            chemin_pdf = tempfile.mktemp(suffix=".pdf")
            try:
                with RedirectionGestionDB(base.chemin):
                    resultat = UIC.Impression(
                        IDfamille=2, IDmodele=IDmodele,
                        date_debut="2026-08-01", date_fin="2027-07-31",
                        saison="2026-2027", listeIDindividus=[20, 21, 22],
                        nomDoc=chemin_pdf, afficherDoc=False,
                    )
                self.assertIsInstance(resultat, dict, "génération échouée : %r" % (resultat,))
                self.assertTrue(os.path.isfile(chemin_pdf))
                taille = os.path.getsize(chemin_pdf)
                self.assertGreater(taille, 0)

                nb_pages = _lire_nombre_de_pages(chemin_pdf)
                self.assertGreaterEqual(nb_pages, 2, "un document scolaire complet doit tenir sur plusieurs pages")

                champs = resultat["champs"]
                # Aucun code métier n'a fabriqué de discipline ni de lieu :
                # seuls les champs générés automatiquement apparaissent.
                for texte_interdit in ("Athlétisme", "Lutte", "BUMBALL", "Motricité", "Acrosport", "Tennis"):
                    self.assertNotIn(texte_interdit, champs["{CONVENTION_PLANNING_DETAIL}"])
                self.assertIn("CYCLE FICTIF", champs["{CONVENTION_PLANNING_DETAIL}"])
            finally:
                if os.path.isfile(chemin_pdf):
                    os.remove(chemin_pdf)

    def test_cas_association_reste_fonctionnel_apres_ajout_du_cas_scolaire(self):
        """ Non-régression explicite du premier jalon : le même moteur
        continue de produire le cas association court. """
        from _fixtures_noethys_db import creer_base_association_simple, inserer_modele_convention_fictif
        with creer_base_association_simple() as base:
            IDmodele = inserer_modele_convention_fictif(base)
            chemin_pdf = tempfile.mktemp(suffix=".pdf")
            try:
                with RedirectionGestionDB(base.chemin):
                    resultat = UIC.Impression(
                        IDfamille=1, IDmodele=IDmodele,
                        date_debut="2026-09-01", date_fin="2026-09-30",
                        saison="2026-2027", listeIDindividus=[2, 3],
                        nomDoc=chemin_pdf, afficherDoc=False,
                    )
                self.assertIsInstance(resultat, dict)
                self.assertEqual(_lire_nombre_de_pages(chemin_pdf), 1)
            finally:
                if os.path.isfile(chemin_pdf):
                    os.remove(chemin_pdf)


class ConventionScolairePlanningSepareTests(unittest.TestCase):
    def test_planning_reservations_reste_generable_pour_la_famille_ecole(self):
        """ Le PDF Planning séparé (moteur Réservations historique, non
        modifié) reste utilisable pour la même famille/période que la
        convention scolaire -- toujours deux documents distincts. """
        with creer_base_ecole_simple() as base:
            with RedirectionGestionDB(base.chemin):
                dictDonnees = RESA.GetDonnees(
                    listeIDindividus=[20, 21, 22], date_debut="2026-08-01",
                    date_fin="2027-07-31", DB=base.db,
                )
                chemin_pdf = tempfile.mktemp(suffix=".pdf")
                try:
                    resultat = RESA.Impression(dictDonnees, nomDoc=chemin_pdf, afficherDoc=False)
                    self.assertIsNotNone(resultat)
                    self.assertTrue(os.path.isfile(chemin_pdf))
                    self.assertGreater(os.path.getsize(chemin_pdf), 0)
                finally:
                    if os.path.isfile(chemin_pdf):
                        os.remove(chemin_pdf)


if __name__ == "__main__":
    unittest.main()
