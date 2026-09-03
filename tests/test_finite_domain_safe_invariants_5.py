from pathlib import Path
import unittest

from scripts import qualify_branch_assignment_gaps as qualify

TARGETS = {
    ("Ctrl/CTRL_Synthese_conso.py", "Importation", "regroupement"),
    ("Ctrl/CTRL_Synthese_conso.py", "Importation", "valeur"),
    ("Ctrl/CTRL_Synthese_deductions.py", "Importation", "regroupement"),
    ("Ctrl/CTRL_Synthese_locations.py", "Importation", "regroupement"),
    ("Ctrl/CTRL_Synthese_modes_reglements.py", "Importation", "condition"),
    ("Ol/OL_Liste_factures_detail.py", "__init__", "label_key"),
    ("Ol/OL_Liste_factures_detail.py", "InitObjectListView", "label_colonne"),
    ("Dlg/DLG_Saisie_tarification.py", "Sauvegarde", "DB"),
}


class FiniteDomainSafeInvariantsTest(unittest.TestCase):
    def test_targets_are_exactly_explicit_safe(self):
        report = qualify.build_report()
        registry = report["explicit_safe_registry"]
        self.assertEqual(registry["unmatched"], [])
        self.assertEqual(registry["ambiguous"], [])
        for target in TARGETS:
            matches = [item for item in report["findings"] if (item["file"], item["function"], item["name"]) == target]
            self.assertEqual(len(matches), 1, (target, matches))
            self.assertEqual(matches[0]["classification"], "explicit_safe")

    def test_synthese_ui_domains_remain_explicit(self):
        root = Path("noethys")
        dlg_conso = (root / "Dlg/DLG_Synthese_conso.py").read_text(encoding="utf-8")
        for code in ("jour", "mois", "annee", "activite", "groupe", "evenement", "evenement_date", "etiquette", "categorie_tarif", "ville_residence", "secteur", "genre", "age", "ville_naissance", "nom_ecole", "nom_classe", "nom_niveau_scolaire", "famille", "individu", "regime", "caisse", "qf", "categorie_travail", "categorie_travail_pere", "categorie_travail_mere"):
            self.assertTrue(f'"code" : "{code}"' in dlg_conso or f'"code": "{code}"' in dlg_conso, code)
        self.assertIn('return "quantite"', dlg_conso)
        self.assertIn('return "temps_presence"', dlg_conso)
        self.assertIn('return "temps_facture"', dlg_conso)
        self.assertIn('code = "question_%s_%d" % (public, dictTemp["IDquestion"])', dlg_conso)

        dlg_deductions = (root / "Dlg/DLG_Synthese_deductions.py").read_text(encoding="utf-8")
        for code in ("jour", "mois", "annee", "ville_residence", "secteur", "famille", "individu", "regime", "caisse", "qf", "montant_deduction", "nom_deduction", "nom_aide"):
            self.assertTrue(f'"code" : "{code}"' in dlg_deductions or f'"code": "{code}"' in dlg_deductions, code)
        self.assertIn('for public in ("famille",)', dlg_deductions)

        dlg_locations = (root / "Dlg/DLG_Synthese_locations.py").read_text(encoding="utf-8")
        for code in ("jour", "mois", "annee", "categorie", "ville_residence", "secteur", "famille", "regime", "caisse", "qf"):
            self.assertTrue(f'"code" : "{code}"' in dlg_locations or f'"code": "{code}"' in dlg_locations, code)
        self.assertIn('for public in ("famille",)', dlg_locations)

    def test_radio_and_invoice_detail_domains_remain_bounded(self):
        root = Path("noethys")
        modes = (root / "Dlg/DLG_Synthese_modes_reglements.py").read_text(encoding="utf-8")
        self.assertIn('self.radio_saisis = wx.RadioButton', modes)
        self.assertIn('wx.RB_GROUP', modes)
        self.assertIn('return "saisis"', modes)
        self.assertIn('return "deposes"', modes)
        self.assertIn('return "nondeposes"', modes)

        factures = (root / "Dlg/DLG_Liste_factures_detail.py").read_text(encoding="utf-8")
        self.assertIn('self.choix_regroupements = [("label",', factures)
        self.assertIn('("IDactivite",', factures)
        self.assertIn('self.ctrl_factures.detail = self.choix_regroupements[self.ctrl_regroupement.GetSelection()][0]', factures)

    def test_tarification_track_mode_guards_every_database_lifecycle_edge(self):
        source = Path("noethys/Dlg/DLG_Saisie_tarification.py").read_text(encoding="utf-8")
        self.assertIn('if self.track_tarif == None :\n            DB = GestionDB.DB()', source)
        self.assertIn('if self.track_tarif == None and self.toolbook.GetPage("conditions") != None :', source)
        self.assertIn('if self.track_tarif == None :\n            DB.Close()', source)


if __name__ == "__main__":
    unittest.main()
