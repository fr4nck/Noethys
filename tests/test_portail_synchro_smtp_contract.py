import ast
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "noethys" / "Utils" / "UTILS_Portail_synchro.py"
AUDIT = ROOT / "scripts" / "audit_branch_assignment_gaps.py"


def load_audit():
    spec = importlib.util.spec_from_file_location("audit_branch_assignment_gaps", AUDIT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PortailSynchroSmtpContractTests(unittest.TestCase):
    def test_smtp_neutral_defaults_are_defined_before_selection(self):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        names = {"MAIL_SERVER", "MAIL_DEFAULT_SENDER", "MAIL_PORT", "MAIL_USE_TLS", "MAIL_USE_SSL", "MAIL_USERNAME", "MAIL_PASSWORD"}
        upload_config = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "Upload_config")
        defaults = {}
        email_if_line = None
        for node in upload_config.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id in names:
                defaults[node.targets[0].id] = node
            if isinstance(node, ast.If) and "email_type_adresse" in ast.unparse(node.test):
                email_if_line = node.lineno
                break
        self.assertEqual(set(defaults), names)
        self.assertTrue(all(isinstance(node.value, ast.Constant) and node.value.value is None for node in defaults.values()))
        self.assertTrue(all(node.lineno < email_if_line for node in defaults.values()))

    def test_targeted_smtp_gaps_disappear(self):
        audit = load_audit()
        findings = audit.scan_file(SOURCE, ROOT / "noethys")
        names = {"MAIL_SERVER", "MAIL_DEFAULT_SENDER", "MAIL_USE_TLS", "MAIL_USE_SSL", "MAIL_USERNAME", "MAIL_PASSWORD"}
        targeted = [item for item in findings if item.get("function") == "Upload_config" and item.get("name") in names]
        self.assertEqual(targeted, [], targeted)

    def test_module_still_parses(self):
        ast.parse(SOURCE.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
