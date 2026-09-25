#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UTILS = ROOT / "noethys" / "Utils" / "UTILS_PeriodesSaison.py"
CTRL = ROOT / "noethys" / "Ctrl" / "CTRL_Grille_periode.py"
DLG_ETAT_GLOBAL = ROOT / "noethys" / "Dlg" / "DLG_Etat_global.py"
DLG_ETAT_NOMIN = ROOT / "noethys" / "Dlg" / "DLG_Etat_nomin.py"
DLG_DEVIS = ROOT / "noethys" / "Dlg" / "DLG_Impression_devis.py"
DLG_SYNTHESE = ROOT / "noethys" / "Dlg" / "DLG_Synthese_conso.py"
DLG_LOT = ROOT / "noethys" / "Dlg" / "DLG_Saisie_lot_conso.py"

spec = importlib.util.spec_from_file_location("UTILS_PeriodesSaison", UTILS)
periodes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(periodes)


class PeriodesSaisonTests(unittest.TestCase):
    def test_saison_courante_bascule_en_septembre(self):
        self.assertEqual(
            periodes.GetAnneeDebutSaison(datetime.date(2026, 9, 24)),
            2026,
        )
        self.assertEqual(
            periodes.GetAnneeDebutSaison(datetime.date(2027, 8, 31)),
            2026,
        )

    def test_bornes_saison_et_trimestres(self):
        bornes = periodes.GetBornesPeriodesSaison(2026)
        self.assertEqual(
            bornes["saison"],
            (datetime.date(2026, 9, 1), datetime.date(2027, 8, 31)),
        )
        self.assertEqual(
            bornes["trimestre_1"],
            (datetime.date(2026, 9, 1), datetime.date(2026, 12, 31)),
        )
        self.assertEqual(
            bornes["trimestre_2"],
            (datetime.date(2027, 1, 1), datetime.date(2027, 3, 31)),
        )
        self.assertEqual(
            bornes["trimestre_3"],
            (datetime.date(2027, 4, 1), datetime.date(2027, 8, 31)),
        )

    def test_bornes_semestres_et_annee_bissextile(self):
        bornes = periodes.GetBornesPeriodesSaison(2027)
        self.assertEqual(
            bornes["semestre_1"],
            (datetime.date(2027, 9, 1), datetime.date(2028, 2, 29)),
        )
        self.assertEqual(
            bornes["semestre_2"],
            (datetime.date(2028, 3, 1), datetime.date(2028, 8, 31)),
        )

    def test_raccourcis_en_cours_utilisent_la_date_reelle(self):
        self.assertEqual(
            periodes.GetPeriodeSaison(
                "trimestre_courant",
                annee_debut=2020,
                date_reference=datetime.date(2026, 9, 24),
            ),
            (datetime.date(2026, 9, 1), datetime.date(2026, 12, 31)),
        )
        self.assertEqual(
            periodes.GetPeriodeSaison(
                "semestre_courant",
                annee_debut=2020,
                date_reference=datetime.date(2027, 3, 1),
            ),
            (datetime.date(2027, 3, 1), datetime.date(2027, 8, 31)),
        )

    def test_onglet_saison_est_ajoute_apres_les_quatre_onglets_historiques(self):
        source = CTRL.read_text(encoding="utf-8")
        marqueurs = [
            'self.notebook.AddPage(self.page_mois, _(u"Mois"))',
            'self.notebook.AddPage(self.page_vacances, _(u"Vacances"))',
            'self.notebook.AddPage(self.page_annee, _(u"Année"))',
            'self.notebook.AddPage(self.page_dates, _(u"Dates"))',
            'self.notebook.AddPage(self.page_saison, _(u"Saison"))',
        ]
        positions = [source.index(marqueur) for marqueur in marqueurs]
        self.assertEqual(positions, sorted(positions))

    def test_onglet_saison_reutilise_le_format_de_persistance_existant(self):
        source = CTRL.read_text(encoding="utf-8")
        self.assertIn("if numPage == 4 :", source)
        self.assertIn('dictDonnees["page"] = 4', source)
        self.assertIn('dictDonnees["annee"] = page.ctrl_annee.GetValue()', source)
        self.assertIn('dictDonnees["listePeriodes"] = self.GetDatesSelections()', source)

    def test_selecteur_commun_peut_imposer_une_selection_simple(self):
        source = CTRL.read_text(encoding="utf-8")
        self.assertIn("selection_multiple=True", source)
        self.assertIn("wx.LB_EXTENDED if selection_multiple else wx.LB_SINGLE", source)
        self.assertIn("callback_selection=None", source)

    def test_etat_global_reutilise_le_selecteur_commun(self):
        source = DLG_ETAT_GLOBAL.read_text(encoding="utf-8")
        self.assertIn("from Ctrl import CTRL_Grille_periode", source)
        self.assertIn("self.ctrl_periode = CTRL_Grille_periode.CTRL(", source)
        self.assertIn("selection_multiple=False", source)
        self.assertIn("callback_selection=self.OnChoixDate", source)
        self.assertNotIn("CTRL_Saisie_date.Date2", source)

    def test_etat_global_conserve_une_periode_continue(self):
        source = DLG_ETAT_GLOBAL.read_text(encoding="utf-8")
        self.assertIn("liste_periodes = self.ctrl_periode.GetDatesSelections()", source)
        self.assertIn("if len(liste_periodes) != 1:", source)
        self.assertIn("date_debut, date_fin = self.panel_parametres.GetPeriode()", source)


    def test_ecrans_metier_reutilisent_le_selecteur_commun(self):
        fichiers = [
            DLG_ETAT_GLOBAL,
            DLG_ETAT_NOMIN,
            DLG_DEVIS,
            DLG_SYNTHESE,
            DLG_LOT,
        ]
        for fichier in fichiers:
            source = fichier.read_text(encoding="utf-8")
            self.assertIn("CTRL_Grille_periode", source, fichier.name)
            self.assertIn("selection_multiple=False", source, fichier.name)

    def test_anciens_selecteurs_de_periode_sont_retires(self):
        for fichier in (DLG_ETAT_GLOBAL, DLG_DEVIS, DLG_SYNTHESE, DLG_LOT):
            source = fichier.read_text(encoding="utf-8")
            self.assertNotIn("ctrl_date_debut", source, fichier.name)
            self.assertNotIn("ctrl_date_fin", source, fichier.name)

        # Etat nominatif conserve volontairement les deux dates du filtre
        # de naissance ; sa période principale passe, elle, par CTRL_Periode.
        source = DLG_ETAT_NOMIN.read_text(encoding="utf-8")
        debut = source.index("class CTRL_Periode")
        fin = source.index("# -------------------------------------------------------------------------------------------------------------------------------------------------", debut)
        bloc_periode = source[debut:fin]
        self.assertIn("CTRL_Grille_periode.CTRL", bloc_periode)
        self.assertNotIn("CTRL_Saisie_date.Date", bloc_periode)

    def test_ecrans_continus_refusent_plusieurs_periodes(self):
        for fichier in (DLG_ETAT_GLOBAL, DLG_ETAT_NOMIN, DLG_DEVIS, DLG_SYNTHESE, DLG_LOT):
            source = fichier.read_text(encoding="utf-8")
            self.assertIn("GetDatesSelections()", source, fichier.name)
            self.assertTrue(
                "len(liste) != 1" in source or "len(liste_periodes) != 1" in source,
                fichier.name,
            )



    def test_etat_global_affiche_les_cinq_onglets_sans_navigation(self):
        source = DLG_ETAT_GLOBAL.read_text(encoding="utf-8")
        self.assertIn("self.ctrl_periode.SetMinSize((300, 205))", source)
        self.assertIn("self.SetMinSize((315, -1))", source)



    def test_saison_affiche_une_valeur_complete_sans_table_geante(self):
        source = CTRL.read_text(encoding="utf-8")
        self.assertIn("class CTRL_Saison(wx.ComboBox):", source)
        self.assertIn("NB_SAISONS_AUTOUR = 10", source)
        self.assertIn('u"%d - %d" % (annee, annee + 1)', source)
        self.assertIn("datetime.MAXYEAR - 1", source)
        self.assertIn("self.ctrl_annee = CTRL_Saison(self)", source)
        self.assertNotIn("range(1977, 6001)", source)
        self.assertNotIn("label_annee_fin", source)



if __name__ == "__main__":
    unittest.main()
