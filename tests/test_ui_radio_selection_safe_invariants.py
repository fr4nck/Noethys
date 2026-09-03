import unittest
from pathlib import Path

from scripts import audit_branch_assignment_gaps as audit
from scripts import qualify_branch_assignment_gaps as qualify

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"

SPECS = (
    ("Dlg/DLG_Liste_deductions.py", "GetActivites", "listeActivites", "body_only"),
    ("Dlg/DLG_Synthese_modes_reglements.py", "GetActivites", "listeActivites", "body_only"),
    ("Dlg/DLG_Badgeage_saisie_procedure.py", "Sauvegarde", "systeme", "body_only"),
    ("Dlg/DLG_Saisie_utilisateur.py", "Sauvegarde", "profil", "body_only"),
    ("Dlg/DLG_Saisie_utilisateur_reseau.py", "RechercheAutorisation", "hote", "body_only"),
    ("Dlg/DLG_Saisie_utilisateur_reseau.py", "Sauvegarde", "hote", "body_only"),
    ("Dlg/DLG_Releve_prestations_saisie.py", "GetOptions", "dictOptions", "body_only"),
    ("Dlg/DLG_Releve_prestations_saisie.py", "GetPeriode", "parametres", "body_only"),
)


class UiRadioSelectionSafeInvariantTests(unittest.TestCase):
    def test_candidates_are_exactly_qualified(self):
        for relative, function, name, detail in SPECS:
            findings = audit.scan_file(NOETHYS / relative, NOETHYS)
            matches = [item for item in findings if item["function"] == function and item["name"] == name and item["detail"] == detail]
            self.assertEqual(len(matches), 1, (relative, function, name))
            self.assertIn(qualify.qualification_key(matches[0], NOETHYS), qualify.EXPLICIT_SAFE)

    def test_radio_groups_remain_explicit(self):
        expected = {
            "Dlg/DLG_Liste_deductions.py": "self.radio_toutes = wx.RadioButton",
            "Dlg/DLG_Synthese_modes_reglements.py": "self.radio_toutes = wx.RadioButton",
            "Dlg/DLG_Badgeage_saisie_procedure.py": "self.radio_barre = wx.RadioButton",
            "Dlg/DLG_Saisie_utilisateur.py": "self.radio_droits_admin = wx.RadioButton",
            "Dlg/DLG_Saisie_utilisateur_reseau.py": "self.radio_1 = wx.RadioButton",
            "Dlg/DLG_Releve_prestations_saisie.py": "self.radio_type_prestations = wx.RadioButton",
        }
        for relative, first_radio in expected.items():
            text = (NOETHYS / relative).read_text(encoding="utf-8")
            line = next(line for line in text.splitlines() if first_radio in line)
            self.assertIn("style=wx.RB_GROUP", line, relative)
        releve = (NOETHYS / "Dlg/DLG_Releve_prestations_saisie.py").read_text(encoding="utf-8")
        period_line = next(line for line in releve.splitlines() if "self.radio_tout = wx.RadioButton" in line)
        self.assertIn("style=wx.RB_GROUP", period_line)


if __name__ == "__main__":
    unittest.main()
