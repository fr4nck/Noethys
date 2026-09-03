import unittest
from pathlib import Path

from scripts import audit_branch_assignment_gaps as audit
from scripts import qualify_branch_assignment_gaps as qualify

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"

SPECS = (('Dlg/DLG_Saisie_portail_periode.py', 'OnBoutonOk', 'affichage', 'body_only'), ('Dlg/DLG_Activite_portail.py', 'Sauvegarde', 'portail_inscriptions_affichage', 'body_only'), ('Dlg/DLG_Activite_portail.py', 'Sauvegarde', 'portail_reservations_affichage', 'body_only'))

class PortalRadioAffichageSafeInvariantTests(unittest.TestCase):
    def test_candidates_are_exactly_qualified(self):
        for relative, function, name, detail in SPECS:
            findings = audit.scan_file(NOETHYS / relative, NOETHYS)
            matches = [item for item in findings if item["function"] == function and item["name"] == name and item["detail"] == detail]
            self.assertEqual(len(matches), 1, (relative, function, name))
            self.assertIn(qualify.qualification_key(matches[0], NOETHYS), qualify.EXPLICIT_SAFE)

    def test_portal_controls_keep_their_radio_group_contracts(self):
        periode = (NOETHYS / "Dlg/DLG_Saisie_portail_periode.py").read_text(encoding="utf-8")
        activite = (NOETHYS / "Dlg/DLG_Activite_portail.py").read_text(encoding="utf-8")
        self.assertIn("self.radio_oui = wx.RadioButton", periode)
        self.assertIn("style=wx.RB_GROUP", next(line for line in periode.splitlines() if "self.radio_oui = wx.RadioButton" in line))
        self.assertIn("style=wx.RB_GROUP", next(line for line in activite.splitlines() if "self.radio_inscriptions_non = wx.RadioButton" in line))
        self.assertIn("style=wx.RB_GROUP", next(line for line in activite.splitlines() if "self.radio_reservations_non = wx.RadioButton" in line))

if __name__ == "__main__":
    unittest.main()
