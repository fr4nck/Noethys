# -*- coding: utf-8 -*-
import datetime
import importlib.util
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UTILS = ROOT / "noethys" / "Utils"


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, str(UTILS / filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mad = _load("UTILS_Mises_a_disposition", "UTILS_Mises_a_disposition.py")
prog = _load(
    "UTILS_Mises_a_disposition_programmation",
    "UTILS_Mises_a_disposition_programmation.py",
)
docs = _load(
    "UTILS_Mises_a_disposition_documents",
    "UTILS_Mises_a_disposition_documents.py",
)


class Noe062DocumentTests(unittest.TestCase):
    def _relation(self):
        beneficiaire = mad.StructureMiseADisposition(
            "Club Test",
            type_structure=mad.TYPE_ASSOCIATION,
            rue="1 rue du Stade",
            cp="35130",
            ville="La Guerche-de-Bretagne",
        )
        payeur = mad.StructureMiseADisposition(
            "Mairie Test",
            type_structure=mad.TYPE_COLLECTIVITE,
            cp="35130",
            ville="La Guerche-de-Bretagne",
        )
        relation = mad.RelationContractuelleMiseADisposition(
            identifiant_beneficiaire=beneficiaire.identifiant_stable,
            identifiant_payeur=payeur.identifiant_stable,
            saison="2026-2027",
            activite="Gymnastique",
            groupe="Loisirs",
            tarif_unitaire="44.00",
            unite_tarif=mad.UNITE_HEURE,
            regle_adhesion=mad.ADHESION_NON_REQUISE,
            mode_facturation=mad.FACTURATION_TRIMESTRIELLE,
        )
        return beneficiaire, payeur, relation

    def _programmation(self, relation):
        programmation = prog.ProgrammationAnnuelle(
            identifiant_relation=relation.identifiant_stable,
            saison="2026-2027",
            statut=prog.STATUT_PROGRAMMATION_VALIDEE,
        )
        creneau = prog.CreneauProgrammation(
            identifiant_relation=relation.identifiant_stable,
            jour_semaine=2,
            heure_debut="10:30",
            heure_fin="11:15",
            groupe="Groupe 1",
            lieu="Salle de sports",
        )
        programmation.AjouterCreneau(creneau)
        return programmation, creneau

    def test_regle_calendrier_produit_le_contrat_historique_exact(self):
        _, _, relation = self._relation()
        _, creneau = self._programmation(relation)
        regle = docs.RegleCalendrierMiseADisposition(
            appliquer_scolaire=True,
            appliquer_vacances=False,
            inclure_feries=False,
            frequence=docs.FREQUENCE_TOUTES_LES_SEMAINES,
        )
        donnees = regle.GetParametresRecurrence(
            creneau, "2026-09-01", "2027-06-30"
        )
        self.assertEqual(
            set(donnees),
            {
                "date_debut",
                "date_fin",
                "heure_debut",
                "heure_fin",
                "jours_vacances",
                "jours_scolaires",
                "semaines",
                "feries",
            },
        )
        self.assertEqual(donnees["jours_scolaires"], [2])
        self.assertEqual(donnees["jours_vacances"], [])
        self.assertEqual(donnees["heure_debut"], "10:30")
        self.assertEqual(donnees["heure_fin"], "11:15")
        self.assertFalse(donnees["feries"])

    def test_periode_du_creneau_restreint_la_generation(self):
        _, _, relation = self._relation()
        programmation = prog.ProgrammationAnnuelle(
            identifiant_relation=relation.identifiant_stable,
            saison="2026-2027",
        )
        creneau = prog.CreneauProgrammation(
            identifiant_relation=relation.identifiant_stable,
            jour_semaine=3,
            heure_debut="16:55",
            heure_fin="17:40",
            date_debut="2026-11-01",
            date_fin="2027-03-31",
        )
        programmation.AjouterCreneau(creneau)
        donnees = docs.RegleCalendrierMiseADisposition().GetParametresRecurrence(
            creneau, "2026-09-01", "2027-06-30"
        )
        self.assertEqual(donnees["date_debut"], datetime.date(2026, 11, 1))
        self.assertEqual(donnees["date_fin"], datetime.date(2027, 3, 31))

    def test_regle_vide_et_frequence_inconnue_sont_refusees(self):
        with self.assertRaises(ValueError):
            docs.RegleCalendrierMiseADisposition(
                appliquer_scolaire=False,
                appliquer_vacances=False,
            )
        with self.assertRaises(ValueError):
            docs.RegleCalendrierMiseADisposition(frequence=99)

    def test_annexe_appelle_le_calculateur_historique_sans_recalculer_le_calendrier(self):
        _, _, relation = self._relation()
        programmation, _ = self._programmation(relation)
        appels = []

        def calculateur(parametres):
            appels.append(dict(parametres))
            return [
                {
                    "date_debut": datetime.datetime(2026, 9, 2, 10, 30),
                    "date_fin": datetime.datetime(2026, 9, 2, 11, 15),
                },
                {
                    "date_debut": datetime.datetime(2026, 9, 9, 10, 30),
                    "date_fin": datetime.datetime(2026, 9, 9, 11, 15),
                },
            ]

        annexe = docs.GenererAnnexeDepuisProgrammation(
            programmation,
            "2026-09-01",
            "2026-09-30",
            calculateur_occurences=calculateur,
        )
        self.assertEqual(len(appels), 1)
        self.assertEqual(len(annexe.occurrences), 2)
        self.assertEqual(annexe.GetLignes()[0]["jour"], "mercredi")
        self.assertEqual(annexe.GetLignes()[0]["duree"], "0h45")

    def test_occurrences_et_annexe_ont_des_identifiants_deterministes(self):
        _, _, relation = self._relation()
        programmation, _ = self._programmation(relation)

        def calculateur(parametres):
            return [
                {
                    "date_debut": datetime.datetime(2026, 9, 2, 10, 30),
                    "date_fin": datetime.datetime(2026, 9, 2, 11, 15),
                }
            ]

        annexe1 = docs.GenererAnnexeDepuisProgrammation(
            programmation, "2026-09-01", "2026-09-30", calculateur
        )
        annexe2 = docs.GenererAnnexeDepuisProgrammation(
            programmation, "2026-09-01", "2026-09-30", calculateur
        )
        self.assertEqual(annexe1.identifiant_stable, annexe2.identifiant_stable)
        self.assertEqual(
            annexe1.occurrences[0].identifiant_stable,
            annexe2.occurrences[0].identifiant_stable,
        )

    def test_annexe_trie_les_dates_et_totalise_les_heures(self):
        _, _, relation = self._relation()
        programmation, _ = self._programmation(relation)

        def calculateur(parametres):
            return [
                {
                    "date_debut": datetime.datetime(2026, 9, 9, 10, 30),
                    "date_fin": datetime.datetime(2026, 9, 9, 11, 15),
                },
                {
                    "date_debut": datetime.datetime(2026, 9, 2, 10, 30),
                    "date_fin": datetime.datetime(2026, 9, 2, 11, 15),
                },
            ]

        annexe = docs.GenererAnnexeDepuisProgrammation(
            programmation, "2026-09-01", "2026-09-30", calculateur
        )
        lignes = annexe.GetLignes()
        self.assertEqual(lignes[0]["date"], "02/09/2026")
        self.assertEqual(lignes[1]["date"], "09/09/2026")
        self.assertEqual(annexe.DureeTotaleMinutes(), 90)
        self.assertEqual(
            annexe.GetChampsFusion()["{ANNEXE_DUREE_TOTALE}"], "1h30"
        )

    def test_occurrences_dupliquees_du_moteur_ne_doublent_pas_annexe(self):
        _, _, relation = self._relation()
        programmation, _ = self._programmation(relation)
        occurrence = {
            "date_debut": datetime.datetime(2026, 9, 2, 10, 30),
            "date_fin": datetime.datetime(2026, 9, 2, 11, 15),
        }
        annexe = docs.GenererAnnexeDepuisProgrammation(
            programmation,
            "2026-09-01",
            "2026-09-30",
            lambda parametres: [occurrence, dict(occurrence)],
        )
        self.assertEqual(len(annexe.occurrences), 1)

    def test_dossier_fusionne_convention_relation_tiers_contact_programmation_annexe(self):
        beneficiaire, payeur, relation = self._relation()
        programmation, _ = self._programmation(relation)
        convention = mad.ConventionMiseADisposition(
            "2026-09-01",
            "2027-06-30",
            reference="MAD-2026-001",
            statut=mad.STATUT_VALIDEE,
            mode_facturation=mad.FACTURATION_TRIMESTRIELLE,
            identifiant_relation=relation.identifiant_stable,
        )
        contact = mad.ContactStructure(
            identifiant_structure=beneficiaire.identifiant_stable,
            nom="Martin",
            prenom="Alice",
            roles=[mad.ROLE_CONTACT_CONVENTION],
            fonction="Présidente",
            mail="alice@example.test",
        )
        annexe = docs.GenererAnnexeDepuisProgrammation(
            programmation,
            "2026-09-01",
            "2026-09-30",
            lambda parametres: [],
        )
        dossier = docs.DossierDocumentaireMiseADisposition(
            convention,
            relation,
            beneficiaire,
            payeur,
            programmation,
            annexe,
            contact_convention=contact,
        )
        champs = dossier.GetChampsFusion()
        self.assertEqual(champs["{CONVENTION_REFERENCE}"], "MAD-2026-001")
        self.assertEqual(champs["{BENEFICIAIRE_NOM}"], "Club Test")
        self.assertEqual(champs["{PAYEUR_NOM}"], "Mairie Test")
        self.assertEqual(champs["{CONTACT_CONVENTION_NOM_COMPLET}"], "Alice Martin")
        self.assertEqual(champs["{DOCUMENT_TYPE}"], docs.DOCUMENT_CONVENTION)

    def test_absence_contact_produit_des_champs_vides_stables(self):
        beneficiaire, payeur, relation = self._relation()
        programmation, _ = self._programmation(relation)
        convention = mad.ConventionMiseADisposition(
            "2026-09-01",
            identifiant_relation=relation.identifiant_stable,
        )
        annexe = docs.GenererAnnexeDepuisProgrammation(
            programmation,
            "2026-09-01",
            "2026-09-30",
            lambda parametres: [],
        )
        dossier = docs.DossierDocumentaireMiseADisposition(
            convention,
            relation,
            beneficiaire,
            payeur,
            programmation,
            annexe,
        )
        champs = dossier.GetChampsFusion()
        self.assertIn("{CONTACT_CONVENTION_NOM}", champs)
        self.assertEqual(champs["{CONTACT_CONVENTION_NOM}"], "")

    def test_avenant_est_identifie_sans_ecraser_la_convention_parent(self):
        beneficiaire, payeur, relation = self._relation()
        programmation, _ = self._programmation(relation)
        parent = mad.ConventionMiseADisposition(
            "2026-09-01",
            identifiant_relation=relation.identifiant_stable,
        )
        avenant = mad.ConventionMiseADisposition(
            "2027-01-01",
            version=2,
            identifiant_parent=parent.identifiant_stable,
            identifiant_relation=relation.identifiant_stable,
        )
        annexe = docs.GenererAnnexeDepuisProgrammation(
            programmation,
            "2027-01-01",
            "2027-06-30",
            lambda parametres: [],
        )
        dossier = docs.DossierDocumentaireMiseADisposition(
            avenant,
            relation,
            beneficiaire,
            payeur,
            programmation,
            annexe,
        )
        self.assertEqual(dossier.GetTypeDocument(), docs.DOCUMENT_AVENANT)
        self.assertEqual(
            dossier.GetChampsFusion()["{CONVENTION_PARENT_ID_STABLE}"],
            parent.identifiant_stable,
        )

    def test_snapshot_officiel_est_hashable_et_detecte_une_mutation(self):
        beneficiaire, payeur, relation = self._relation()
        programmation, _ = self._programmation(relation)
        convention = mad.ConventionMiseADisposition(
            "2026-09-01",
            identifiant_relation=relation.identifiant_stable,
        )
        annexe = docs.GenererAnnexeDepuisProgrammation(
            programmation,
            "2026-09-01",
            "2026-09-30",
            lambda parametres: [],
        )
        dossier = docs.DossierDocumentaireMiseADisposition(
            convention,
            relation,
            beneficiaire,
            payeur,
            programmation,
            annexe,
        )
        snapshot = dossier.Figer(
            date_generation=datetime.datetime(2026, 8, 21, 0, 30)
        )
        self.assertTrue(snapshot.VerifierIntegrite())
        snapshot.paquet_modele["champs"]["{BENEFICIAIRE_NOM}"] = "Altéré"
        self.assertFalse(snapshot.VerifierIntegrite())

    def test_dossier_refuse_les_relations_incoherentes(self):
        beneficiaire, payeur, relation = self._relation()
        programmation, _ = self._programmation(relation)
        autre_relation = str(uuid.uuid4())
        convention = mad.ConventionMiseADisposition(
            "2026-09-01",
            identifiant_relation=autre_relation,
        )
        annexe = docs.GenererAnnexeDepuisProgrammation(
            programmation,
            "2026-09-01",
            "2026-09-30",
            lambda parametres: [],
        )
        with self.assertRaises(ValueError):
            docs.DossierDocumentaireMiseADisposition(
                convention,
                relation,
                beneficiaire,
                payeur,
                programmation,
                annexe,
            )


if __name__ == "__main__":
    unittest.main()
