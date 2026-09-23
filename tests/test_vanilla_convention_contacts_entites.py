# -*- coding: utf-8 -*-
"""Intégration des fonctions d'entité dans la Convention.

Couvre le chemin complet sans données réelles :
rattachement -> fonction/usages -> champs Convention -> menus du
générateur. Une base sans métadonnées de fonction garde le repli
historique couvert par les tests Convention existants.
"""
from __future__ import annotations

import datetime
import sys
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
NOETHYS_DIR = TESTS_DIR.parent / "noethys"
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))
if str(NOETHYS_DIR) not in sys.path:
    sys.path.insert(0, str(NOETHYS_DIR))

from _fixtures_noethys_db import RedirectionGestionDB, creer_base_association_simple  # noqa: E402
from Utils import UTILS_Convention_champs as CC  # noqa: E402
from Utils import UTILS_Fonctions_entites as FE  # noqa: E402


class FauxInformations:
    def __init__(self, valeurs=None):
        self.valeurs = valeurs or {"{NBRE_REPRESENTANTS_RATTACHES}": 0}

    def GetDictValeurs(self, mode, ID, formatChamp):
        return dict(self.valeurs)


class ConventionContactsEntitesTests(unittest.TestCase):

    def _ajoute_roles(self, base):
        # Relation 4 : représentant/signataire.
        base.db.ReqMAJ(
            "individus",
            [("travail_mail", "president@example.org"), ("travail_tel", "0102030405")],
            "IDindividu", 4,
        )
        FE.EnregistrerFonctionRattachement(
            4, fonction="Président", representant=True, signataire=True,
            defaut=True, DB=base.db,
        )

        # Deuxième personne, uniquement pour la facturation.
        base.inserer(
            "individus",
            ["IDindividu", "nom", "prenom", "IDcivilite", "travail_mail", "travail_tel"],
            [(5, "MARTIN", "Claire", 3, "facturation@example.org", "0504030201")],
        )
        base.inserer(
            "rattachements",
            ["IDrattachement", "IDfamille", "IDindividu", "IDcategorie", "titulaire"],
            [(5, 1, 5, 3, 0)],
        )
        FE.EnregistrerFonctionRattachement(
            5, fonction="Trésorière", facturation=True, defaut=True, DB=base.db,
        )

    def test_champs_convention_utilisent_signataire_et_referent_facturation(self):
        with creer_base_association_simple() as base:
            self._ajoute_roles(base)
            champs, _ = CC.GetChampsConvention(
                IDfamille=1,
                date_debut="2026-09-01",
                date_fin="2026-09-30",
                listeIDindividus=[2, 3],
                DB=base.db,
                informations=FauxInformations(),
            )

        self.assertEqual(champs["{CONVENTION_REPRESENTANT_NOM_COMPLET}"], "M. DUPUIS Jean")
        self.assertEqual(champs["{CONVENTION_REPRESENTANT_FONCTION}"], "Président")
        self.assertEqual(champs["{CONVENTION_REFERENT_FACTURATION_NOM_COMPLET}"], "Mme MARTIN Claire")
        self.assertEqual(champs["{CONVENTION_REFERENT_FACTURATION_FONCTION}"], "Trésorière")
        self.assertEqual(champs["{CONVENTION_REFERENT_FACTURATION_EMAIL}"], "facturation@example.org")
        self.assertEqual(champs["{CONVENTION_REFERENT_FACTURATION_TELEPHONE}"], "0504030201")

    def test_listes_de_choix_ne_contiennent_que_les_usages_pertinents(self):
        with creer_base_association_simple() as base:
            self._ajoute_roles(base)
            representants = CC.GetRepresentantsDisponibles(1, DB=base.db)
            facturation = CC.GetReferentsFacturationDisponibles(1, DB=base.db)

        self.assertEqual([x["IDindividu"] for x in representants], [4])
        self.assertEqual([x["IDindividu"] for x in facturation], [5])

    def test_dialogue_propose_les_deux_menus_et_applique_un_choix(self):
        import wx
        from Dlg import DLG_Generation_convention

        app = wx.GetApp() or wx.App(False)
        with creer_base_association_simple() as base:
            self._ajoute_roles(base)
            with RedirectionGestionDB(base.chemin):
                dlg = DLG_Generation_convention.Dialog(
                    None, IDfamille=1,
                    date_debut=datetime.date(2026, 9, 1),
                    date_fin=datetime.date(2026, 9, 30),
                )

                self.assertGreaterEqual(dlg.ctrl_representant_choix.GetCount(), 2)
                self.assertGreaterEqual(dlg.ctrl_facturation_choix.GetCount(), 2)

                dlg.ctrl_representant_choix.SetSelection(1)
                dlg.OnChoixRepresentant()
                self.assertEqual(dlg.ctrl_representant_nom_complet.GetValue(), "M. DUPUIS Jean")
                self.assertEqual(dlg.ctrl_representant_fonction.GetValue(), "Président")

                dlg.ctrl_facturation_choix.SetSelection(1)
                dlg.OnChoixReferentFacturation()
                overrides = dlg.GetOverrides()
                self.assertEqual(
                    overrides["{CONVENTION_REFERENT_FACTURATION_NOM_COMPLET}"],
                    "Mme MARTIN Claire",
                )
                self.assertEqual(
                    overrides["{CONVENTION_REFERENT_FACTURATION_FONCTION}"],
                    "Trésorière",
                )
                dlg.Destroy()

        # Ne détruit pas l'application globale créée par d'autres tests.
        self.assertIsNotNone(app)


if __name__ == "__main__":
    unittest.main()
