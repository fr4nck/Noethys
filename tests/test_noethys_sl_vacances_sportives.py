#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "noethys" / "Utils" / "UTILS_VacancesSportives.py"
DLG_LOT = ROOT / "noethys" / "Dlg" / "DLG_Saisie_lot_ouvertures2.py"
DLG_OUVERTURES = ROOT / "noethys" / "Dlg" / "DLG_Ouvertures.py"


spec = importlib.util.spec_from_file_location("UTILS_VacancesSportives", str(MODULE_PATH))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TestVacancesSportives(unittest.TestCase):

    def setUp(self):
        self.vacances = [
            ("2026-10-17", "2026-11-01", "Toussaint", "2026"),
        ]

    def test_premier_samedi_reste_hors_vacances_sportives(self):
        self.assertFalse(
            module.EstEnVacancesSportives(datetime.date(2026, 10, 17), self.vacances)
        )

    def test_dimanche_debut_est_en_vacances_sportives(self):
        self.assertTrue(
            module.EstEnVacancesSportives(datetime.date(2026, 10, 18), self.vacances)
        )

    def test_samedi_du_milieu_est_en_vacances_sportives(self):
        self.assertTrue(
            module.EstEnVacancesSportives(datetime.date(2026, 10, 24), self.vacances)
        )

    def test_dernier_samedi_est_en_vacances_sportives(self):
        self.assertTrue(
            module.EstEnVacancesSportives(datetime.date(2026, 10, 31), self.vacances)
        )

    def test_dimanche_fin_est_en_vacances_sportives(self):
        self.assertTrue(
            module.EstEnVacancesSportives(datetime.date(2026, 11, 1), self.vacances)
        )

    def test_lundi_reprise_est_hors_vacances_sportives(self):
        self.assertFalse(
            module.EstEnVacancesSportives(datetime.date(2026, 11, 2), self.vacances)
        )

    def test_debut_deja_un_dimanche_reste_dimanche(self):
        self.assertEqual(
            module.GetDebutVacancesSportives(datetime.date(2026, 10, 18)),
            datetime.date(2026, 10, 18),
        )


    def test_option_est_explicite_dans_la_saisie_par_lot(self):
        source = DLG_LOT.read_text(encoding="utf-8")
        self.assertIn("self.ctrl_vacances_dimanche = wx.CheckBox(", source)
        self.assertIn("Vacances sportives : du dimanche au dimanche", source)
        self.assertIn('"vacances_dimanche_dimanche": vacances_dimanche_dimanche', source)
        self.assertIn("self.ctrl_vacances_dimanche.SetValue(False)", source)

    def test_traitement_par_lot_applique_la_regle_uniquement_si_cochee(self):
        source = DLG_OUVERTURES.read_text(encoding="utf-8")
        self.assertIn('dictDonnees.get("vacances_dimanche_dimanche", False)', source)
        self.assertIn("if vacances_dimanche_dimanche:", source)
        self.assertIn("UTILS_VacancesSportives.EstEnVacancesSportives(", source)
        self.assertIn("else:\n                est_en_vacances = self.EstEnVacances(date)", source)



if __name__ == "__main__":
    unittest.main()
