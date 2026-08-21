# -*- coding: utf-8 -*-
import importlib.util
import unittest
import uuid
from pathlib import Path


MODULE = (
    Path(__file__).resolve().parents[1]
    / "noethys"
    / "Utils"
    / "UTILS_Mises_a_disposition_programmation.py"
)
spec = importlib.util.spec_from_file_location(
    "UTILS_Mises_a_disposition_programmation", str(MODULE)
)
prog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prog)


class CreneauProgrammationTests(unittest.TestCase):
    def setUp(self):
        self.relation = str(uuid.uuid4())

    def test_creneau_valide_jour_horaires_et_duree(self):
        creneau = prog.CreneauProgrammation(
            self.relation,
            2,
            "10:30",
            "11:15",
            groupe="Groupe 1",
        )
        self.assertEqual(creneau.DureePrevueMinutes(), 45)
        self.assertEqual(creneau.GetChampsFusion()["{CRENEAU_JOUR}"], "mercredi")
        self.assertEqual(creneau.GetChampsFusion()["{CRENEAU_HEURE_DEBUT}"], "10:30")

    def test_jour_et_horaires_invalides_sont_refuses(self):
        with self.assertRaises(ValueError):
            prog.CreneauProgrammation(self.relation, 7, "10:00", "11:00")
        with self.assertRaises(ValueError):
            prog.CreneauProgrammation(self.relation, 2, "11:00", "10:00")
        with self.assertRaises(ValueError):
            prog.CreneauProgrammation(self.relation, 2, "10:00", "10:00")

    def test_renouvellement_cree_une_nouvelle_identite_et_garde_la_source(self):
        ancien = prog.CreneauProgrammation(
            self.relation,
            3,
            "16:55",
            "17:40",
            groupe="Éveils Gym",
            lieu="Salle des sports",
        )
        nouvelle_relation = str(uuid.uuid4())
        nouveau = ancien.Renouveler(
            nouvelle_relation,
            date_debut="2026-09-01",
            date_fin="2027-06-30",
        )
        self.assertNotEqual(nouveau.identifiant_stable, ancien.identifiant_stable)
        self.assertEqual(nouveau.identifiant_source, ancien.identifiant_stable)
        self.assertEqual(nouveau.identifiant_relation, nouvelle_relation)
        self.assertEqual(nouveau.etat_renouvellement, prog.RENOUVELLEMENT_INCHANGE)
        self.assertEqual(nouveau.groupe, "Éveils Gym")

    def test_dates_anciennes_ne_sont_pas_reprises_implicitement(self):
        ancien = prog.CreneauProgrammation(
            self.relation,
            1,
            "18:00",
            "19:00",
            date_debut="2025-09-01",
            date_fin="2026-06-30",
        )
        nouveau = ancien.Renouveler(str(uuid.uuid4()))
        self.assertIsNone(nouveau.date_debut)
        self.assertIsNone(nouveau.date_fin)

    def test_modification_d_un_creneau_renouvele_est_tracee(self):
        ancien = prog.CreneauProgrammation(self.relation, 0, "14:00", "15:00")
        nouveau = ancien.Renouveler(str(uuid.uuid4()))
        modifie = nouveau.AvecModifications(heure_fin="15:30", lieu="Gymnase")
        self.assertEqual(modifie.identifiant_stable, nouveau.identifiant_stable)
        self.assertEqual(modifie.identifiant_source, ancien.identifiant_stable)
        self.assertEqual(modifie.etat_renouvellement, prog.RENOUVELLEMENT_MODIFIE)
        self.assertEqual(modifie.DureePrevueMinutes(), 90)


class ProgrammationAnnuelleTests(unittest.TestCase):
    def setUp(self):
        self.relation = str(uuid.uuid4())
        self.programmation = prog.ProgrammationAnnuelle(
            self.relation,
            "2025-2026",
            statut=prog.STATUT_PROGRAMMATION_VALIDEE,
        )

    def test_un_creneau_d_une_autre_relation_est_refuse(self):
        autre = prog.CreneauProgrammation(
            str(uuid.uuid4()), 2, "10:00", "11:00"
        )
        with self.assertRaises(ValueError):
            self.programmation.AjouterCreneau(autre)

    def test_renouveler_copie_uniquement_les_creneaux_conserves(self):
        ancien_1 = prog.CreneauProgrammation(
            self.relation, 2, "10:00", "11:00", groupe="Groupe A"
        )
        ancien_2_source = prog.CreneauProgrammation(
            str(uuid.uuid4()), 3, "17:00", "18:00"
        )
        ancien_2 = ancien_2_source.Renouveler(self.relation)
        ancien_2 = ancien_2.MarquerSupprime()
        self.programmation.AjouterCreneau(ancien_1)
        self.programmation.AjouterCreneau(ancien_2)

        nouvelle_relation = str(uuid.uuid4())
        suivante = self.programmation.Renouveler(
            nouvelle_relation,
            "2026-2027",
            date_debut="2026-09-01",
            date_fin="2027-06-30",
        )
        self.assertEqual(suivante.statut, prog.STATUT_PROGRAMMATION_BROUILLON)
        self.assertEqual(suivante.identifiant_source, self.programmation.identifiant_stable)
        self.assertEqual(len(suivante.creneaux), 1)
        self.assertEqual(suivante.creneaux[0].groupe, "Groupe A")
        self.assertEqual(
            suivante.creneaux[0].etat_renouvellement,
            prog.RENOUVELLEMENT_INCHANGE,
        )

    def test_modification_et_suppression_conservent_la_filiation_n_moins_1(self):
        ancien = prog.CreneauProgrammation(self.relation, 4, "14:30", "15:30")
        suivante = prog.ProgrammationAnnuelle(
            str(uuid.uuid4()), "2026-2027"
        )
        herite = ancien.Renouveler(suivante.identifiant_relation)
        suivante.AjouterCreneau(herite)

        modifie = suivante.ModifierCreneau(
            herite.identifiant_stable, heure_debut="15:00", heure_fin="16:00"
        )
        self.assertEqual(modifie.etat_renouvellement, prog.RENOUVELLEMENT_MODIFIE)
        self.assertEqual(modifie.identifiant_source, ancien.identifiant_stable)

        supprime = suivante.SupprimerCreneau(herite.identifiant_stable)
        self.assertEqual(supprime.etat_renouvellement, prog.RENOUVELLEMENT_SUPPRIME)
        self.assertEqual(len(suivante.GetCreneauxConserves()), 0)

    def test_un_creneau_ajoute_puis_supprime_disparait_sans_fausse_trace(self):
        ajoute = prog.CreneauProgrammation(self.relation, 1, "17:00", "18:00")
        self.programmation.AjouterCreneau(ajoute)
        resultat = self.programmation.SupprimerCreneau(ajoute.identifiant_stable)
        self.assertIsNone(resultat)
        self.assertEqual(self.programmation.creneaux, [])

    def test_synthese_distingue_inchange_modifie_supprime_et_ajoute(self):
        nouvelle_relation = str(uuid.uuid4())
        source = prog.CreneauProgrammation(self.relation, 0, "10:00", "11:00")
        source2 = prog.CreneauProgrammation(self.relation, 1, "10:00", "11:00")
        source3 = prog.CreneauProgrammation(self.relation, 2, "10:00", "11:00")
        programmation = prog.ProgrammationAnnuelle(nouvelle_relation, "2026-2027")
        inchange = source.Renouveler(nouvelle_relation)
        modifie = source2.Renouveler(nouvelle_relation).AvecModifications(lieu="Salle A")
        supprime = source3.Renouveler(nouvelle_relation).MarquerSupprime()
        ajoute = prog.CreneauProgrammation(nouvelle_relation, 3, "10:00", "11:00")
        for creneau in (inchange, modifie, supprime, ajoute):
            programmation.AjouterCreneau(creneau)

        synthese = programmation.GetSyntheseRenouvellement()
        self.assertEqual(synthese[prog.RENOUVELLEMENT_INCHANGE], 1)
        self.assertEqual(synthese[prog.RENOUVELLEMENT_MODIFIE], 1)
        self.assertEqual(synthese[prog.RENOUVELLEMENT_SUPPRIME], 1)
        self.assertEqual(synthese[prog.RENOUVELLEMENT_AJOUTE], 1)
        self.assertEqual(
            programmation.GetChampsFusion()["{PROGRAMMATION_NB_CRENEAUX}"],
            "3",
        )

    def test_donnees_sont_entierement_serialisables(self):
        creneau = prog.CreneauProgrammation(
            self.relation,
            5,
            "09h30",
            "12h05",
            date_debut="2026-09-01",
            date_fin="2027-06-30",
        )
        self.programmation.AjouterCreneau(creneau)
        donnees = self.programmation.GetDonnees()
        self.assertEqual(donnees["saison"], "2025-2026")
        self.assertEqual(donnees["creneaux"][0]["heure_debut"], "09:30")
        self.assertEqual(donnees["creneaux"][0]["date_debut"], "2026-09-01")


if __name__ == "__main__":
    unittest.main()
