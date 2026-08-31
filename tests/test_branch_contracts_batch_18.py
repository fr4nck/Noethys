import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
AUDIT = ROOT / "scripts" / "audit_branch_assignment_gaps.py"
spec = importlib.util.spec_from_file_location("audit_branch_assignment_gaps", AUDIT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

TARGET = ("Ctrl/CTRL_Questionnaire.py", "Remplissage", "ctrl")

class TestBatch18Questionnaire(unittest.TestCase):
    def test_targeted_finding_disappears(self):
        path = NOETHYS / "Ctrl/CTRL_Questionnaire.py"
        remaining = [
            (item["file"], item["function"], item["name"])
            for item in audit.scan_file(path, NOETHYS)
            if (item["file"], item["function"], item["name"]) == TARGET
        ]
        self.assertEqual(remaining, [])

    def test_unknown_non_null_control_is_rejected_before_tree_mutation(self):
        source = (NOETHYS / "Ctrl/CTRL_Questionnaire.py").read_text(encoding="utf-8")
        self.assertIn("controles_valides = {", source)
        self.assertIn("if track.controle not in controles_valides:", source)
        self.assertIn("Type de contrôle de questionnaire inconnu", source)
        self.assertLess(source.index("if track.controle not in controles_valides:"), source.index("self.dictBranches = {}", source.index("def Remplissage")))

    def test_control_less_question_does_not_load_widget_value(self):
        source = (NOETHYS / "Ctrl/CTRL_Questionnaire.py").read_text(encoding="utf-8")
        block = source[source.index("if track.controle != None :", source.index("def Remplissage")):source.index("indexQuestion += 1", source.index("def Remplissage"))]
        self.assertIn("track.SetValeurStr(valeur)", block)
        self.assertTrue(block.index("track.SetValeurStr(valeur)") > block.index("if track.controle != None :"))

    def test_maj_always_thaws_after_failure(self):
        source = (NOETHYS / "Ctrl/CTRL_Questionnaire.py").read_text(encoding="utf-8")
        maj = source[source.index("def MAJ("):source.index("def Importation(")]
        self.assertIn("try:", maj)
        self.assertIn("finally:", maj)
        self.assertIn("self.Thaw()", maj)

if __name__ == "__main__":
    unittest.main()
