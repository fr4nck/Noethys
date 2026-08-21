#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
if str(NOETHYS) not in sys.path:
    sys.path.insert(0, str(NOETHYS))

from Data.DATA_Tables import DB_DATA
from Utils import UTILS_Portail_tarifs_donnees as DONNEES


class FakeDB(object):
    def __init__(self, nouvelle_activite=False):
        self.requetes = []
        self.nouvelle_activite = nouvelle_activite

    def ExecuterReq(self, requete):
        self.requetes.append(requete)
        return True

    def ResultatReq(self):
        requete = self.requetes[-1]
        if "FROM activites" in requete:
            lignes = [(1, "ALSH Bais"), (2, "École multisports")]
            if self.nouvelle_activite:
                lignes.append((3, "Sport-Santé"))
            return lignes
        if "FROM categories_tarifs" in requete:
            lignes = [(10, 1, "QF A"), (11, 1, "QF B"), (20, 2, "EMS")]
            if self.nouvelle_activite:
                lignes.append((30, 3, "Sport-Santé"))
            return lignes
        if "FROM tarifs_lignes" in requete:
            champs = [champ[0] for champ in DB_DATA["tarifs_lignes"]]

            def ligne(IDtarif, IDactivite, code, num_ligne, qf_min, qf_max, montant):
                valeurs = {champ: None for champ in champs}
                valeurs.update({
                    "IDligne": IDtarif * 100 + num_ligne,
                    "IDactivite": IDactivite,
                    "IDtarif": IDtarif,
                    "code": code,
                    "num_ligne": num_ligne,
                    "qf_min": qf_min,
                    "qf_max": qf_max,
                    "montant_unique": montant,
                    "IDmodele": None,
                })
                return tuple(valeurs[champ] for champ in champs)

            lignes = [
                ligne(100, 1, "qf", 1, 0, 699, 9.35),
                ligne(100, 1, "qf", 2, 700, 999, 10.00),
                ligne(200, 2, "montant_unique", 1, None, None, 89.00),
            ]
            if self.nouvelle_activite:
                lignes.append(ligne(300, 3, "montant_unique", 1, None, None, 109.00))
            return lignes
        if "FROM questionnaire_filtres" in requete:
            return [(501, 100)]
        if "FROM tarifs" in requete:
            # Ordre strictement identique à CHAMPS_TARIFS.
            lignes = [
                (
                    100, 1, 1000, "Journée", "2026-09-01", "2027-08-31",
                    0, 0, 0, 0, 0, "qf",
                    "10;11", "1;2", None, "JOURN", None, None,
                    None, None, None, None, "706", None, 0,
                    None, "reservation;present", 1, "Accueil journée", "Journée", "", None,
                ),
                (
                    200, 2, 2000, "Licence EMS", "2026-09-01", "2027-08-31",
                    0, 0, 0, 0, 0, "montant_unique",
                    "20", None, None, "FORFAIT", None, None,
                    None, None, None, None, "706", None, 0,
                    None, None, 1, "Licence annuelle", "EMS", "", None,
                ),
            ]
            if self.nouvelle_activite:
                lignes.append((
                    300, 3, 3000, "Sport-Santé annuel", "2026-09-01", "2027-08-31",
                    0, 0, 0, 0, 0, "montant_unique",
                    "30", None, None, "FORFAIT", None, None,
                    None, None, None, None, "706", None, 0,
                    None, None, 1, "Adhésion Sport-Santé", "Sport-Santé", "", None,
                ))
            return lignes
        raise AssertionError("Requête inattendue : %s" % requete)


class PortailTarifsDonneesTests(unittest.TestCase):

    def test_conversion_du_format_historique_de_listes(self):
        self.assertEqual(DONNEES.convertir_liste_ids("1;2;3"), [1, 2, 3])
        self.assertEqual(DONNEES.convertir_liste_ids("reservation;present", type_texte=True), ["reservation", "present"])
        self.assertIsNone(DONNEES.convertir_liste_ids(""))

    def test_politique_automatique_est_le_defaut(self):
        politique = DONNEES.normaliser_politique()
        self.assertEqual(politique, {
            "mode": "automatique",
            "IDsactivites": [],
            "IDsactivites_exclues": [],
        })

    def test_charge_les_baremes_et_les_developpe_par_categorie(self):
        tarifs = DONNEES.charger_baremes(FakeDB())

        # Le tarif ALSH attaché à deux catégories devient deux descriptions
        # distinctes ; le tarif EMS n'en produit qu'une.
        self.assertEqual(len(tarifs), 3)
        alsh_a = tarifs[0]
        alsh_b = tarifs[1]
        ems = tarifs[2]

        self.assertEqual(alsh_a["nom_activite"], "ALSH Bais")
        self.assertEqual(alsh_a["IDcategorie_tarif"], 10)
        self.assertEqual(alsh_a["nom_categorie_tarif"], "QF A")
        self.assertEqual(alsh_b["IDcategorie_tarif"], 11)
        self.assertEqual(alsh_b["nom_categorie_tarif"], "QF B")
        self.assertEqual(len(alsh_a["lignes_calcul"]), 2)
        self.assertEqual(alsh_a["lignes_calcul"][0]["montant_unique"], 9.35)
        self.assertEqual(alsh_a["filtres"], [{"IDfiltre": 501}])
        self.assertEqual(alsh_a["groupes"], [1, 2])
        self.assertEqual(alsh_a["etats"], ["reservation", "present"])

        self.assertEqual(ems["nom_activite"], "École multisports")
        self.assertEqual(ems["nom_categorie_tarif"], "EMS")
        self.assertEqual(ems["lignes_calcul"][0]["montant_unique"], 89.0)
        self.assertEqual(ems["filtres"], [])

    def test_selection_explicite_reste_disponible(self):
        tarifs = DONNEES.charger_baremes(FakeDB(), IDsactivites=[2])
        self.assertEqual(len(tarifs), 1)
        self.assertEqual(tarifs[0]["IDactivite"], 2)
        self.assertEqual(DONNEES.charger_baremes(FakeDB(), IDsactivites=[]), [])

    def test_nouvelle_activite_tarifee_est_incluse_sans_modifier_la_configuration(self):
        publication = DONNEES.construire_publication(
            FakeDB(nouvelle_activite=True),
            date_reference=datetime.date(2026, 9, 2),
        )

        self.assertEqual(publication["politique"]["mode"], "automatique")
        self.assertIn(3, publication["IDsactivites_publiees"])
        self.assertIn("Sport-Santé", publication["html"])
        self.assertIn("109,00 €", publication["html"])

    def test_exclusion_explicite_survit_a_la_decouverte_automatique(self):
        publication = DONNEES.construire_publication(
            FakeDB(nouvelle_activite=True),
            politique={"mode": "automatique", "IDsactivites_exclues": [3]},
            date_reference=datetime.date(2026, 9, 2),
        )

        self.assertNotIn(3, publication["IDsactivites_publiees"])
        self.assertNotIn("Sport-Santé", publication["html"])
        self.assertIn("École multisports", publication["html"])

    def test_publication_relit_la_source_noethys_et_signale_les_conditions(self):
        publication = DONNEES.construire_publication(
            FakeDB(),
            IDsactivites=[1, 2],
            date_reference=datetime.date(2026, 9, 2),
        )

        self.assertEqual(len(publication["baremes"]), 3)
        self.assertEqual(len(publication["descriptions"]), 3)
        html = publication["html"]
        self.assertIn("Tarifs des activités", html)
        self.assertIn("ALSH Bais", html)
        self.assertIn("École multisports", html)
        self.assertIn("QF A", html)
        self.assertIn("9,35 €", html)
        self.assertIn("89,00 €", html)
        # Le tarif ALSH fictif porte groupe, filtre et états : la publication
        # doit l'indiquer au lieu de le présenter comme un prix personnalisé.
        self.assertIn("groupe de l&#x27;inscription", html)
        self.assertIn("questionnaire", html)
        self.assertIn("état de la consommation", html)


if __name__ == "__main__":
    unittest.main()
