# -*- coding: utf-8 -*-
import datetime
import importlib.util
import unittest
import uuid
from pathlib import Path


MODULE = (
    Path(__file__).resolve().parents[1]
    / "noethys"
    / "Utils"
    / "UTILS_Mises_a_disposition.py"
)
spec = importlib.util.spec_from_file_location("UTILS_Mises_a_disposition", str(MODULE))
mad = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mad)


class ConventionMiseADispositionTests(unittest.TestCase):
    def test_creation_genere_un_identifiant_stable_uuid(self):
        convention = mad.ConventionMiseADisposition("2026-09-01", "2027-06-30")
        self.assertEqual(str(uuid.UUID(convention.identifiant_stable)), convention.identifiant_stable)
        self.assertFalse(convention.EstAvenant())

    def test_dates_acceptent_date_datetime_et_iso(self):
        convention = mad.ConventionMiseADisposition(
            datetime.datetime(2026, 9, 1, 10, 30),
            datetime.date(2027, 6, 30),
        )
        self.assertEqual(convention.date_debut, datetime.date(2026, 9, 1))
        self.assertEqual(convention.date_fin, datetime.date(2027, 6, 30))

    def test_periode_inversee_est_refusee(self):
        with self.assertRaises(ValueError):
            mad.ConventionMiseADisposition("2027-06-30", "2026-09-01")

    def test_statut_et_facturation_sont_controles(self):
        with self.assertRaises(ValueError):
            mad.ConventionMiseADisposition("2026-09-01", statut="inconnu")
        with self.assertRaises(ValueError):
            mad.ConventionMiseADisposition(
                "2026-09-01", mode_facturation="au_pif"
            )

    def test_avenant_garde_un_parent_stable_et_exige_une_version(self):
        parent = mad.ConventionMiseADisposition("2026-09-01")
        avenant = mad.ConventionMiseADisposition(
            "2027-01-01",
            version=2,
            identifiant_parent=parent.identifiant_stable,
        )
        self.assertTrue(avenant.EstAvenant())
        self.assertEqual(avenant.identifiant_parent, parent.identifiant_stable)

        with self.assertRaises(ValueError):
            mad.ConventionMiseADisposition(
                "2027-01-01",
                version=1,
                identifiant_parent=parent.identifiant_stable,
            )

    def test_activation_est_fondee_sur_la_periode_pas_sur_le_statut(self):
        convention = mad.ConventionMiseADisposition(
            "2026-09-01",
            "2027-06-30",
            statut=mad.STATUT_BROUILLON,
        )
        self.assertFalse(convention.EstActiveA("2026-08-31"))
        self.assertTrue(convention.EstActiveA("2026-09-01"))
        self.assertTrue(convention.EstActiveA("2027-06-30"))
        self.assertFalse(convention.EstActiveA("2027-07-01"))

    def test_champs_fusion_sont_stables_et_documentaires(self):
        parent = str(uuid.uuid4())
        relation = str(uuid.uuid4())
        convention = mad.ConventionMiseADisposition(
            "2026-09-01",
            "2027-06-30",
            reference="MAD-2026-001",
            statut=mad.STATUT_VALIDEE,
            mode_facturation=mad.FACTURATION_TRIMESTRIELLE,
            version=2,
            identifiant_parent=parent,
            identifiant_relation=relation,
        )
        champs = convention.GetChampsFusion()
        self.assertEqual(champs["{CONVENTION_REFERENCE}"], "MAD-2026-001")
        self.assertEqual(champs["{CONVENTION_VERSION}"], "2")
        self.assertEqual(champs["{CONVENTION_DATE_DEBUT}"], "01/09/2026")
        self.assertEqual(champs["{CONVENTION_DATE_FIN}"], "30/06/2027")
        self.assertEqual(champs["{CONVENTION_MODE_FACTURATION}"], "trimestrielle")
        self.assertEqual(champs["{CONVENTION_PARENT_ID_STABLE}"], parent)
        self.assertEqual(champs["{CONVENTION_RELATION_ID_STABLE}"], relation)
        self.assertEqual(champs["{CONVENTION_EST_AVENANT}"], "1")

    def test_donnees_sont_serialisables_sans_objets_date(self):
        convention = mad.ConventionMiseADisposition("2026-09-01", "2027-06-30")
        donnees = convention.GetDonnees()
        self.assertEqual(donnees["date_debut"], "2026-09-01")
        self.assertEqual(donnees["date_fin"], "2027-06-30")


class StructureMiseADispositionTests(unittest.TestCase):
    def test_identifiants_administratifs_sont_facultatifs(self):
        structure = mad.StructureMiseADisposition(
            "Les Jongleurs Gym",
            type_structure=mad.TYPE_ASSOCIATION,
        )
        self.assertEqual(structure.siret, "")
        self.assertEqual(structure.rna, "")
        self.assertEqual(structure.nom, "Les Jongleurs Gym")

    def test_type_inconnu_et_nom_vide_sont_refuses(self):
        with self.assertRaises(ValueError):
            mad.StructureMiseADisposition("", mad.TYPE_ASSOCIATION)
        with self.assertRaises(ValueError):
            mad.StructureMiseADisposition("Test", "cabane")

    def test_structure_operationnelle_et_payeur_restent_distincts(self):
        ecole = mad.StructureMiseADisposition("École Saint-Test", mad.TYPE_ECOLE)
        mairie = mad.StructureMiseADisposition("Mairie de Test", mad.TYPE_COLLECTIVITE)
        relation = mad.RelationContractuelleMiseADisposition(
            ecole.identifiant_stable,
            "2026-2027",
            "EPS",
            identifiant_payeur=mairie.identifiant_stable,
            tarif_unitaire="23.00",
        )
        self.assertTrue(relation.EstPayeurDistinct())
        self.assertEqual(relation.identifiant_beneficiaire, ecole.identifiant_stable)
        self.assertEqual(relation.identifiant_payeur, mairie.identifiant_stable)


class ContactStructureTests(unittest.TestCase):
    def test_contact_peut_cumuler_plusieurs_roles_sans_doublon(self):
        structure = mad.StructureMiseADisposition("Dynamic Gym")
        contact = mad.ContactStructure(
            structure.identifiant_stable,
            "Martin",
            "Camille",
            roles=[
                mad.ROLE_CONTACT_PLANNING,
                mad.ROLE_CONTACT_CONVENTION,
                mad.ROLE_CONTACT_PLANNING,
            ],
        )
        self.assertEqual(
            contact.roles,
            (mad.ROLE_CONTACT_PLANNING, mad.ROLE_CONTACT_CONVENTION),
        )
        self.assertTrue(contact.ALeRole(mad.ROLE_CONTACT_PLANNING))

    def test_role_inconnu_est_refuse(self):
        structure = mad.StructureMiseADisposition("Dynamic Gym")
        with self.assertRaises(ValueError):
            mad.ContactStructure(
                structure.identifiant_stable,
                "Martin",
                roles=["roi_du_planning"],
            )


class RelationContractuelleTests(unittest.TestCase):
    def test_adhesion_est_portee_par_relation_pas_par_type_structure(self):
        mairie = mad.StructureMiseADisposition(
            "Mairie partenaire ALSH",
            mad.TYPE_COLLECTIVITE,
        )
        financement = mad.RelationContractuelleMiseADisposition(
            mairie.identifiant_stable,
            "2026-2027",
            "Partenariat ALSH",
            regle_adhesion=mad.ADHESION_NON_APPLICABLE,
        )
        mise_a_disposition = mad.RelationContractuelleMiseADisposition(
            mairie.identifiant_stable,
            "2026-2027",
            "Intervention sportive",
            regle_adhesion=mad.ADHESION_REQUISE,
            tarif_unitaire="44",
        )
        self.assertEqual(financement.regle_adhesion, mad.ADHESION_NON_APPLICABLE)
        self.assertEqual(mise_a_disposition.regle_adhesion, mad.ADHESION_REQUISE)

    def test_tarif_decimal_est_serialise_sans_float(self):
        structure = mad.StructureMiseADisposition("Atout Sport")
        relation = mad.RelationContractuelleMiseADisposition(
            structure.identifiant_stable,
            "2026-2027",
            "Fitness",
            tarif_unitaire="33.50",
            unite_tarif=mad.UNITE_HEURE,
            mode_facturation=mad.FACTURATION_TRIMESTRIELLE,
        )
        self.assertEqual(relation.GetDonnees()["tarif_unitaire"], "33.50")
        self.assertEqual(
            relation.GetChampsFusion()["{RELATION_TARIF_UNITAIRE}"],
            "33.50",
        )

    def test_tarif_negatif_et_regles_inconnues_sont_refuses(self):
        structure = mad.StructureMiseADisposition("Atout Sport")
        with self.assertRaises(ValueError):
            mad.RelationContractuelleMiseADisposition(
                structure.identifiant_stable,
                "2026-2027",
                "Fitness",
                tarif_unitaire="-1",
            )
        with self.assertRaises(ValueError):
            mad.RelationContractuelleMiseADisposition(
                structure.identifiant_stable,
                "2026-2027",
                "Fitness",
                regle_adhesion="toujours",
            )

    def test_payeur_par_defaut_est_le_beneficiaire(self):
        structure = mad.StructureMiseADisposition("Cap Loisirs")
        relation = mad.RelationContractuelleMiseADisposition(
            structure.identifiant_stable,
            "2026-2027",
            "Gym",
        )
        self.assertFalse(relation.EstPayeurDistinct())
        self.assertEqual(
            relation.identifiant_payeur,
            structure.identifiant_stable,
        )


if __name__ == "__main__":
    unittest.main()
