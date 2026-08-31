import ast
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
AUDIT = ROOT / "scripts" / "audit_branch_assignment_gaps.py"
spec = importlib.util.spec_from_file_location("audit_branch_assignment_gaps", AUDIT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

TARGETS = {
    "noethys/Ctrl/CTRL_Saisie_pays.py": {("SetValue", "pays")},
    "noethys/Ctrl/CTRL_Editeur_email.py": {("OnIndentLess", "r")},
    "noethys/Dlg/DLG_Saisie_texte_rappel.py": {("OnIndentLess", "r")},
    "noethys/Dlg/DLG_Planning_transports.py": {("OnChercherDate", "newDate")},
    "noethys/Dlg/DLG_Portail_renseignements.py": {("SetValeur", "resultat")},
}

class TestBatch11Contracts(unittest.TestCase):
    def test_targeted_findings_disappear(self):
        for relpath, targets in TARGETS.items():
            findings = audit.scan_file(ROOT / relpath, ROOT / "noethys")
            remaining = {(x.get("function"), x.get("name")) for x in findings}
            self.assertTrue(targets.isdisjoint(remaining), (relpath, targets & remaining))

    def test_cancelled_date_search_does_not_use_unassigned_date(self):
        text = (ROOT / "noethys/Dlg/DLG_Planning_transports.py").read_text(encoding="utf-8")
        self.assertIn("if dlg.ShowModal() == wx.ID_OK:", text)
        self.assertIn("self.parent.ctrl_planning.SetDate(newDate)", text)

    def test_unknown_address_field_is_explicit(self):
        text = (ROOT / "noethys/Dlg/DLG_Portail_renseignements.py").read_text(encoding="utf-8")
        self.assertIn('raise ValueError("Champ d\'adresse inconnu : %s" % champ)', text)

if __name__ == "__main__":
    unittest.main()
