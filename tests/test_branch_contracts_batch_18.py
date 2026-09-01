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
        self.assertIn('elif mode == "impression" :', source)
        self.assertIn(
            '''raise ValueError("Mode d'affichage des statistiques inconnu : %s" % mode)''',
            source,
        )

    def test_gethtml_still_supports_affichage_and_impression_modes(self):
        source = (NOETHYS / "Utils/UTILS_Stats_modeles.py").read_text(encoding="utf-8")
        self.assertIn('if mode == "affichage" :', source)
        # Both historically supported modes must still assign html before the
        # final "return html", preserving behaviour for supported entries.
        gethtml_start = source.index("def GetHTML(")
        gethtml_end = source.index("def GetFigure(", gethtml_start)
        body = source[gethtml_start:gethtml_end]
        self.assertIn('html = u"""<HTML><BODY><FONT SIZE=-1>"""', body)
        self.assertIn('html = u"""<HTML><BODY>"""', body)
        self.assertIn("return html", body)


if __name__ == "__main__":
    unittest.main()
