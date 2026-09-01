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

class TestBatch18StatsGetHTML(unittest.TestCase):
    def test_targeted_finding_disappears(self):
        path = NOETHYS / "Utils/UTILS_Stats_modeles.py"
        remaining = {
            (item["file"], item["function"], item["name"])
            for item in audit.scan_file(path, NOETHYS)
            if (item["file"], item["function"], item["name"]) == TARGET
        }
        self.assertEqual(remaining, set())

    def test_unsupported_mode_raises_explicit_error_instead_of_unbound_local(self):
        source = (NOETHYS / "Utils/UTILS_Stats_modeles.py").read_text(encoding="utf-8")
        self.assertIn(
            'def GetHTML(self, rubrique=None, page=None, mode="affichage", selectionsCodes=[]):',
            source,
        )
        self.assertIn('if mode not in ("affichage", "impression") :', source)
        self.assertIn("raise ValueError(", source)
        # Le contrôle du mode doit précéder tout autre traitement de la méthode.
        idx_def = source.index("def GetHTML(")
        idx_guard = source.index('if mode not in ("affichage", "impression") :')
        idx_affichage_branch = source.index('if mode == "affichage" :')
        self.assertLess(idx_def, idx_guard)
        self.assertLess(idx_guard, idx_affichage_branch)

    def test_historical_modes_are_preserved(self):
        source = (NOETHYS / "Utils/UTILS_Stats_modeles.py").read_text(encoding="utf-8")
        self.assertIn('if mode == "affichage" :', source)
        # Une fois le mode validé en amont, 'impression' est le seul mode
        # restant : le second 'if mode == "impression"' devient un 'else'
        # exhaustif qui rend l'affectation de 'html' garantie sur tous les
        # chemins atteignables.
        self.assertIn('# Mode \'impression\'\n        else :', source)

if __name__ == "__main__":
    unittest.main()
