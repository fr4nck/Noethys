import ast
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
AUDIT = ROOT / "scripts" / "audit_branch_assignment_gaps.py"
spec = importlib.util.spec_from_file_location("audit_branch_assignment_gaps", AUDIT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

TARGETS = {
    ("Ctrl/CTRL_Evenements.py", "Importation", "conditionPeriode"),
    ("Ctrl/CTRL_Grille_renderers.py", "DrawTexte", "x"),
    ("Ctrl/CTRL_Grille_renderers.py", "Draw", "largeur_bouton"),
    ("Ctrl/CTRL_Informations.py", "Branches_renseignements", "labelRenseignement"),
    ("Ctrl/CTRL_Remplissage.py", "__init__", "labelActivite"),
    ("Ctrl/CTRL_Remplissage.py", "Draw", "largeur_bouton"),
}

class TestBatch13Contracts(unittest.TestCase):
    def test_targeted_findings_disappear(self):
        remaining = set()
        for relpath, function, name in TARGETS:
            path = NOETHYS / relpath
            for item in audit.scan_file(path, NOETHYS):
                key = (item["file"], item["function"], item["name"])
                if key in TARGETS:
                    remaining.add(key)
        self.assertEqual(remaining, set())

    def test_event_period_contract_is_explicit(self):
        source = (NOETHYS / "Ctrl/CTRL_Evenements.py").read_text(encoding="utf-8")
        self.assertIn('if self.periode == None', source)
        self.assertIn('conditionPeriode = ""', source)
        self.assertIn('raise ValueError("Type de période inconnu', source)
        self.assertIn('WHERE evenements.IDactivite IN %s %s', source)

    def test_text_position_contract_is_explicit(self):
        source = (NOETHYS / "Ctrl/CTRL_Grille_renderers.py").read_text(encoding="utf-8")
        self.assertIn('if position == "gauche"', source)
        self.assertIn('elif position == "droite"', source)
        self.assertIn('raise ValueError("Position de texte inconnue', source)

    def test_render_defaults_are_neutral(self):
        source = (NOETHYS / "Ctrl/CTRL_Grille_renderers.py").read_text(encoding="utf-8")
        self.assertIn('largeur_bouton = 0', source)
        source2 = (NOETHYS / "Ctrl/CTRL_Remplissage.py").read_text(encoding="utf-8")
        self.assertIn('labelActivite = u""', source2)
        self.assertIn('largeur_bouton = 0', source2)

if __name__ == "__main__":
    unittest.main()
