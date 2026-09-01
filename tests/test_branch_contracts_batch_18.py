import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
AUDIT = ROOT / "scripts" / "audit_branch_assignment_gaps.py"
spec = importlib.util.spec_from_file_location("audit_branch_assignment_gaps", AUDIT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

TARGET = ("Utils/UTILS_Stats_modeles.py", "GetHTML", "html")


class TestBatch18StatsModeles(unittest.TestCase):
    def test_targeted_finding_disappears(self):
        path = NOETHYS / "Utils/UTILS_Stats_modeles.py"
        remaining = {
            (item["file"], item["function"], item["name"])
            for item in audit.scan_file(path, NOETHYS)
            if (item["file"], item["function"], item["name"]) == TARGET
        }
        self.assertEqual(remaining, set())

    def test_gethtml_rejects_unknown_mode_explicitly(self):
        source = (NOETHYS / "Utils/UTILS_Stats_modeles.py").read_text(encoding="utf-8")
        self.assertIn('def GetHTML(self, rubrique=None, page=None, mode="affichage", selectionsCodes=[]):', source)
        self.assertIn('if mode == "affichage" :', source)
        self.assertIn('elif mode == "impression" :', source)
        self.assertIn('else :\n            raise ValueError("Mode GetHTML inconnu : %s" % mode)', source)

    def test_gethtml_mode_contract_matches_actual_callers(self):
        # Tous les appelants réels de GetHTML n'utilisent que les modes
        # "affichage" (valeur par défaut) et "impression" : le contrat rendu
        # explicite ne casse donc aucun appel existant du dépôt.
        for relpath in ("Dlg/DLG_Stats.py",):
            source = (NOETHYS / relpath).read_text(encoding="utf-8")
            for line in source.splitlines():
                if ".GetHTML(" in line and "def GetHTML" not in line:
                    self.assertTrue(
                        'mode="impression"' in line or "mode=" not in line,
                        msg="Appel GetHTML avec un mode inattendu : %s" % line,
                    )


if __name__ == "__main__":
    unittest.main()
