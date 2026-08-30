import ast
import unittest
from pathlib import Path
from scripts import audit_branch_assignment_gaps

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "noethys"
SOURCE_PATH = SOURCE_ROOT / "Ctrl" / "CTRL_ObjectListView.py"

def extract_method(name):
    tree = ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))
    matches = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name]
    if len(matches) != 1:
        raise AssertionError("method ambiguous: %s" % name)
    module = ast.Module(body=[matches[0]], type_ignores=[])
    ast.fix_missing_locations(module)
    ns = {}
    exec(compile(module, str(SOURCE_PATH), "exec"), ns)
    return ns[name]

class FakeOwner:
    def GetInscrits(self, **kwargs): return [1, 2]
    def GetCotisations(self, **kwargs): return [3]

class ObjectListViewFilterContractTests(unittest.TestCase):
    def test_numeric_range_keeps_historical_expression(self):
        method = extract_method("formatageFiltres")
        result = method(FakeOwner(), [{"code":"montant", "choix":"COMPRIS", "criteres":"10;20", "typeDonnee":"montant"}])
        self.assertEqual(result, ["track.montant >= 10 and track.montant <= 20"])

    def test_supported_text_filter_is_unchanged(self):
        method = extract_method("formatageFiltres")
        result = method(FakeOwner(), [{"code":"nom", "choix":"CONTIENT", "criteres":"abc", "typeDonnee":"texte"}])
        self.assertEqual(result, ["track.nom != None and 'abc'.lower() in track.nom.lower()"])

    def test_unsupported_filter_fails_explicitly(self):
        method = extract_method("formatageFiltres")
        with self.assertRaises(ValueError):
            method(FakeOwner(), [{"code":"x", "choix":"INCONNU", "criteres":"", "typeDonnee":"texte"}])

    def test_unsupported_inscription_mode_fails_before_database_access(self):
        method = extract_method("GetInscrits")
        criteres = {"listeActivites":[], "listeGroupes":[]}
        with self.assertRaisesRegex(ValueError, "non supporté"):
            method(FakeOwner(), mode="autre", choix="", criteres=criteres)

    def test_targeted_gaps_are_gone(self):
        findings = audit_branch_assignment_gaps.scan_file(SOURCE_PATH, SOURCE_ROOT)
        targeted = [x for x in findings if x.get("function") in ("formatageFiltres", "GetInscrits") and x.get("name") in ("min", "max", "filtre", "key")]
        self.assertEqual(targeted, [], targeted)

if __name__ == "__main__": unittest.main()
