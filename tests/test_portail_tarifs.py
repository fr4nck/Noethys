#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "noethys" / "Utils" / "UTILS_Portail_tarifs.py"
SPEC = importlib.util.spec_from_file_location("UTILS_Portail_tarifs", MODULE_PATH)
TARIFS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TARIFS)


class PortailTarifsTests(unittest.TestCase):

    def test_montant_unique_est_decrit_sans_inventer_de_contexte(self):
        tarif = TARIFS.decrire_tarif({
            "IDtarif": 10,
            "IDactivite": 2,
            "nom_activite": "École multisports",
            "nom_tarif": "Licence annuelle",
            "methode": "montant_unique",
            "date_debut": "2026-09-01",
            "date_fin": "2027-08-31",
            "lignes_calcul": [{"montant_unique": 89}],
        }, date_reference=datetime.date(2026, 9, 2))

        self.assertEqual(tarif["statut"], "en_vigueur")
        self.assertEqual(tarif["methode_label"], "Montant fixe")
        self.assertEqual(tarif["regles"], [{"type": "montant", "montant": "89,00 €"}])
        self.assertTrue(tarif["descriptible"])
        self.assertTrue(tarif["exact_sans_contexte"])
        self.assertEqual(tarif["avertissements"], [])

    def test_qf_preserve_les_paliers_noethys(self):
        tarif = TARIFS.decrire_tarif({
            "nom_tarif": "Journée ALSH",
            "methode": "qf",
            "lignes_calcul": [
                {"qf_min": 0, "qf_max": 699, "montant_unique": 9.35},
                {"qf_min": 700, "qf_max": 999, "montant_unique": 10},
                {"qf_min": 1000, "qf_max": 99999, "montant_unique": 10.35},
            ],
        })

        self.assertEqual(len(tarif["regles"]), 3)
        self.assertEqual(tarif["regles"][0], {
            "type": "qf", "qf_min": 0.0, "qf_max": 699.0, "montant": "9,35 €"
        })
        self.assertEqual(tarif["regles"][2]["montant"], "10,35 €")
        self.assertTrue(tarif["descriptible"])
        self.assertFalse(tarif["exact_sans_contexte"])

    def test_tarif_futur_est_identifie_sans_remplacer_le_tarif_courant(self):
        tarif = TARIFS.decrire_tarif({
            "nom_tarif": "Tarif rentrée",
            "methode": "montant_unique",
            "date_debut": "2026-09-01",
            "lignes_calcul": [{"montant_unique": 12}],
        }, date_reference=datetime.date(2026, 8, 21))
        self.assertEqual(tarif["statut"], "futur")
        self.assertEqual(tarif["date_debut"], "01/09/2026")

    def test_tarif_contextuel_ne_devient_pas_un_faux_prix_personnalise(self):
        tarif = TARIFS.decrire_tarif({
            "nom_tarif": "Garderie",
            "methode": "duree_qf",
            "groupes": [1, 2],
            "filtres": [{"IDquestion": 3}],
            "lignes_calcul": [{"qf_min": 0, "qf_max": 1000, "montant_unique": 0.80}],
        })

        self.assertFalse(tarif["descriptible"])
        self.assertFalse(tarif["exact_sans_contexte"])
        self.assertEqual(tarif["regles"], [])
        texte = " ".join(tarif["avertissements"])
        self.assertIn("groupe de l'inscription", texte)
        self.assertIn("questionnaire", texte)
        self.assertIn("contexte réel", texte)

    def test_dates_et_qf_sont_decrits_ligne_par_ligne(self):
        tarif = TARIFS.decrire_tarif({
            "nom_tarif": "Sortie",
            "methode": "qf_date",
            "lignes_calcul": [
                {"date": "2026-10-21", "qf_min": 0, "qf_max": 699, "montant_unique": 5},
                {"date": "2026-10-21", "qf_min": 700, "qf_max": 999, "montant_unique": 7.5},
            ],
        })
        self.assertEqual(tarif["regles"][0]["date"], "21/10/2026")
        self.assertEqual(tarif["regles"][1]["montant"], "7,50 €")

    def test_html_echappe_les_libelles_et_indique_les_tarifs_contextuels(self):
        descriptions = [
            TARIFS.decrire_tarif({
                "nom_activite": "ALSH <Bais>",
                "nom_tarif": "Journée & repas",
                "methode": "qf",
                "lignes_calcul": [{"qf_min": 0, "qf_max": 699, "montant_unique": 9.35}],
            }),
            TARIFS.decrire_tarif({
                "nom_tarif": "Montant événement",
                "methode": "montant_evenement",
                "lignes_calcul": [],
            }),
        ]
        rendu = TARIFS.construire_html(descriptions, titre="Mes tarifs")

        self.assertIn("ALSH &lt;Bais&gt;", rendu)
        self.assertIn("Journée &amp; repas", rendu)
        self.assertIn("9,35 €", rendu)
        self.assertIn("Le montant dépend de la réservation ou de la situation réelle.", rendu)
        self.assertNotIn("<Bais>", rendu)

    def test_liste_exclut_les_tarifs_expires_par_defaut(self):
        tarifs = [
            {
                "nom_tarif": "Ancien",
                "methode": "montant_unique",
                "date_fin": "2025-12-31",
                "lignes_calcul": [{"montant_unique": 5}],
            },
            {
                "nom_tarif": "Actuel",
                "methode": "montant_unique",
                "date_debut": "2026-01-01",
                "lignes_calcul": [{"montant_unique": 6}],
            },
        ]
        resultat = TARIFS.decrire_tarifs(tarifs, date_reference=datetime.date(2026, 8, 21))
        self.assertEqual([x["nom"] for x in resultat], ["Actuel"])


if __name__ == "__main__":
    unittest.main()
