import ast
import importlib.util
import pathlib
import types
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
TARGET = ROOT / "noethys/Dlg/DLG_Saisie_prelevement_lot.py"
AUDIT = ROOT / "scripts/audit_branch_assignment_gaps.py"

spec = importlib.util.spec_from_file_location("audit_branch_assignment_gaps", AUDIT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def load_function():
    tree = ast.parse(TARGET.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "GetLabelParametres":
            module = ast.Module(body=[node], type_ignores=[])
            ast.fix_missing_locations(module)
            namespace = {
                "_": lambda value: value,
                "UTILS_Dates": types.SimpleNamespace(DateEngFr=lambda value: "FORMATTED:%s" % value),
            }
            exec(compile(module, str(TARGET), "exec"), namespace)
            return namespace["GetLabelParametres"]
    raise AssertionError("GetLabelParametres introuvable")


class _Control:
    def __init__(self, value):
        self.value = value

    def GetValue(self):
        return self.value

    def GetDate(self):
        return self.value


class _Dialog:
    def __init__(self, date):
        self.ctrl_nom = _Control("Septembre")
        self.ctrl_date = _Control(date)


class TestPrelevementLotLabelContract(unittest.TestCase):
    def test_branch_assignment_finding_disappears(self):
        findings = audit.scan_file(TARGET, ROOT / "noethys")
        remaining = {(item.get("function"), item.get("name")) for item in findings}
        self.assertNotIn(("GetLabelParametres", "date"), remaining)

    def test_missing_date_produces_a_safe_print_label(self):
        get_label = load_function()
        self.assertEqual(get_label(_Dialog(None)), "Prélèvement : 'Septembre' ()")

    def test_present_date_is_formatted_once(self):
        get_label = load_function()
        self.assertEqual(get_label(_Dialog("2026-09-01")), "Prélèvement : 'Septembre' (FORMATTED:2026-09-01)")


if __name__ == "__main__":
    unittest.main()
