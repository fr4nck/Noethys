import unittest

from scripts import qualify_branch_assignment_gaps as qualification

TARGETS = {
    ("Dlg/DLG_Compte_internet.py", "Importation", "req"),
    ("Dlg/DLG_Saisie_lot_deductions.py", "OnBoutonOk", "montant"),
    ("Dlg/DLG_Saisie_lot_deductions.py", "OnBoutonOk", "pourcent"),
    ("Dlg/DLG_Saisie_lot_deductions.py", "OnBoutonOk", "montantDeduction"),
    ("Dlg/DLG_Saisie_produit.py", "OnBoutonOk", "prochainIDligne"),
    ("Utils/UTILS_Icalendar.py", "__init__", "fichier"),
    ("Utils/UTILS_Impression_inscription.py", "__init__", "paraStyleIntro"),
    ("Utils/UTILS_Html2text.py", "handle_tag", "tag_style"),
    ("Utils/UTILS_Html2text.py", "handle_tag", "parent_style"),
    ("Utils/UTILS_Titulaires.py", "GetTitulaires", "nomsTitulaires"),
    ("Utils/UTILS_Cotisations_manquantes.py", "GetListeCotisationsManquantes", "date_fin"),
    ("Utils/UTILS_Cryptage_fichier.py", "DecrypterFichier", "dec"),
    ("Utils/UTILS_Export_nomade.py", "Run", "dlgAttente"),
    ("Utils/UTILS_Sauvegarde.py", "Sauvegarde", "fichierDest"),
    ("Utils/UTILS_Sauvegarde.py", "Sauvegarde", "dictAdresse"),
}


class BranchAssignmentSafeInvariantTests(unittest.TestCase):
    def test_proven_control_flow_invariants_are_explicitly_safe(self):
        report = qualification.build_report(qualification.ROOT)
        findings = {
            (item["file"], item["function"], item["name"]): item
            for item in report["findings"]
            if (item["file"], item["function"], item["name"]) in TARGETS
        }
        self.assertEqual(set(findings), TARGETS)
        for target in TARGETS:
            self.assertEqual(findings[target]["classification"], "explicit_safe")
            self.assertEqual(findings[target]["priority"], "low")


if __name__ == "__main__":
    unittest.main()
