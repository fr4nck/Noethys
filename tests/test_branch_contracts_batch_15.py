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
    ("Utils/UTILS_Gestion.py", "Verification", "date"),
    ("Utils/UTILS_Printer.py", "__init__", "controlBar"),
    ("Dlg/DLG_Anniversaires.py", "OnBoutonOk", "listeIndividus"),
}


class TestBatch15RealContracts(unittest.TestCase):
    def test_targeted_findings_disappear(self):
        remaining = set()
        for relpath, function, name in TARGETS:
            path = NOETHYS / relpath
            for item in audit.scan_file(path, NOETHYS):
                key = (item["file"], item["function"], item["name"])
                if key in TARGETS:
                    remaining.add(key)
        self.assertEqual(remaining, set())

    def test_gestion_rejects_unsupported_items_explicitly(self):
        source = (NOETHYS / "Utils/UTILS_Gestion.py").read_text(encoding="utf-8")
        self.assertIn('raise TypeError("Type de donnée de gestion non supporté', source)

    def test_printer_requires_preview_control_bar_explicitly(self):
        source = (NOETHYS / "Utils/UTILS_Printer.py").read_text(encoding="utf-8")
        self.assertIn("controlBar = None", source)
        self.assertIn("if controlBar is None:", source)
        self.assertIn("Barre de contrôle d'aperçu introuvable", source)

    def test_anniversaires_rejects_unknown_mode_explicitly(self):
        source = (NOETHYS / "Dlg/DLG_Anniversaires.py").read_text(encoding="utf-8")
        self.assertIn('elif dictParametres["mode"] == "inscrits":', source)
        self.assertIn('raise ValueError("Mode anniversaire inconnu', source)


if __name__ == "__main__":
    unittest.main()
