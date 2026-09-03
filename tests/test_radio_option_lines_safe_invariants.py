import unittest
from pathlib import Path

from scripts import audit_branch_assignment_gaps as audit
from scripts import qualify_branch_assignment_gaps as qualify

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"

SPECS = (
    ("Dlg/DLG_Conversion_etat.py", "GetDonnees", "option_lignes", "body_only"),
    ("Dlg/DLG_Recopiage_conso.py", "GetDonnees", "option_lignes", "body_only"),
)


class RadioOptionLinesSafeInvariantTests(unittest.TestCase):
    def test_radio_group_candidates_are_exactly_qualified(self):
        for relative, function, name, detail in SPECS:
            findings = audit.scan_file(NOETHYS / relative, NOETHYS)
            matches = [
                item for item in findings
                if item["function"] == function
                and item["name"] == name
                and item["detail"] == detail
            ]
            self.assertEqual(len(matches), 1, relative)
            key = qualify.qualification_key(matches[0], NOETHYS)
            self.assertIn(key, qualify.EXPLICIT_SAFE)

    def test_each_option_lines_pair_is_a_single_wx_radio_group(self):
        for relative, _, _, _ in SPECS:
            text = (NOETHYS / relative).read_text(encoding="utf-8")
            radio_line = next(
                line for line in text.splitlines()
                if "self.radio_lignes_affichees = wx.RadioButton" in line
            )
            self.assertIn("style=wx.RB_GROUP", radio_line)
            self.assertIn("self.radio_lignes_selectionnees = wx.RadioButton", text)
            self.assertIn('valeur="lignes_affichees"', text)


if __name__ == "__main__":
    unittest.main()
