import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
SOURCE_PATH = NOETHYS / "Ctrl/CTRL_Questionnaire.py"
AUDIT = ROOT / "scripts" / "audit_branch_assignment_gaps.py"
spec = importlib.util.spec_from_file_location("audit_branch_assignment_gaps", AUDIT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

TARGET = ("Ctrl/CTRL_Questionnaire.py", "Remplissage", "ctrl")


class TestBatch18Questionnaire(unittest.TestCase):
    def test_targeted_finding_disappears(self):
        remaining = [
            (item["file"], item["function"], item["name"])
            for item in audit.scan_file(SOURCE_PATH, NOETHYS)
            if (item["file"], item["function"], item["name"]) == TARGET
        ]
        self.assertEqual(remaining, [])

    def test_unknown_non_null_control_is_rejected_before_tree_mutation(self):
        source = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("controles_valides = {", source)
        self.assertIn("if track.controle not in controles_valides:", source)
        self.assertIn("Type de contrôle de questionnaire inconnu", source)
        self.assertLess(
            source.index("if track.controle not in controles_valides:"),
            source.index("self.dictBranches = {}", source.index("def Remplissage")),
        )

    def test_control_less_question_does_not_load_widget_value(self):
        source = SOURCE_PATH.read_text(encoding="utf-8")
        start = source.index("if track.controle != None :", source.index("def Remplissage"))
        block = source[start:source.index("indexQuestion += 1", start)]
        self.assertIn("track.SetValeurStr(valeur)", block)
        self.assertGreater(
            block.index("track.SetValeurStr(valeur)"),
            block.index("if track.controle != None :"),
        )

    def test_maj_always_thaws_after_failure(self):
        source = SOURCE_PATH.read_text(encoding="utf-8")
        maj = source[source.index("    def MAJ("):source.index("    def Importation(")]
        self.assertIn("try:", maj)
        self.assertIn("finally:", maj)
        self.assertIn("self.Thaw()", maj)

    def test_maj_validates_import_before_clearing_tree_and_restores_model_on_failure(self):
        source = SOURCE_PATH.read_text(encoding="utf-8")
        maj = source[source.index("    def MAJ("):source.index("    def Importation(")]
        self.assertLess(maj.index("self.Importation()"), maj.index("self.DeleteAllItems()"))
        self.assertIn("ancien_modele", maj)
        self.assertIn("= ancien_modele", maj)
        self.assertLess(
            maj.index("Type de contrôle de questionnaire inconnu"),
            maj.index("self.DeleteAllItems()"),
        )

    def test_settype_is_transactional_when_target_model_is_invalid(self):
        source = SOURCE_PATH.read_text(encoding="utf-8")
        block = source[source.index("    def SetType("):source.index("    def RAZ(")]
        self.assertIn("ancien_type = self.type", block)
        self.assertIn("self.MAJ()", block)
        self.assertNotIn("self.Importation()", block)
        self.assertIn("self.type = ancien_type", block)
        self.assertIn("except Exception:", block)

    def test_maj_rolls_back_model_and_tree_on_render_failure(self):
        source = SOURCE_PATH.read_text(encoding="utf-8")
        maj = source[source.index("    def MAJ("):source.index("    def Importation(")]
        self.assertLess(maj.index("ancien_modele ="), maj.index("self.Importation()"))
        self.assertIn("except Exception:", maj)
        rollback = maj[maj.index("except Exception:"):]
        self.assertIn("= ancien_modele", rollback)
        self.assertIn("self.DeleteAllItems()", rollback)
        self.assertIn("self.Remplissage(selection=selection)", rollback)

    def test_dialog_type_choice_rolls_back_when_settype_fails(self):
        dlg_path = ROOT / "noethys" / "Dlg" / "DLG_Questionnaires.py"
        source = dlg_path.read_text(encoding="utf-8")
        block = source[source.index("    def OnChoixType("):source.index("    def OnBoutonAjouter(")]
        self.assertIn("ancien_type = self.type", block)
        self.assertIn("nouveau_type = self.ctrl_type.GetID()", block)
        self.assertIn("self.ctrl_questionnaire.SetType(nouveau_type)", block)
        self.assertIn("self.ctrl_type.SetID(ancien_type)", block)
        self.assertLess(block.index("self.ctrl_questionnaire.SetType(nouveau_type)"), block.rindex("self.type = nouveau_type"))


if __name__ == "__main__":
    unittest.main()
