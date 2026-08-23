# -*- coding: utf-8 -*-

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_legacy_list_tools.py"
SPEC = importlib.util.spec_from_file_location("audit_legacy_list_tools", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class LegacyListToolsAuditTests(unittest.TestCase):
    def test_detects_historical_toolbar_and_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "screen.py"
            path.write_text(
                "from Ctrl import CTRL_ObjectListView\n"
                "toolbar = CTRL_ObjectListView.CTRL_Outils(parent, listview=liste)\n"
                "image = 'Images/16x16/Filtre_3.png'\n",
                encoding="utf-8",
            )
            findings = MODULE.scan(root)
            codes = [item["code"] for item in findings]
            self.assertIn("ctrl_outils_historique", codes)
            self.assertIn("assets_filtre_16px", codes)

    def test_repens_toolbar_is_not_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "screen.py"
            path.write_text(
                "from Ctrl import CTRL_OutilsListeRepens\n"
                "toolbar = CTRL_OutilsListeRepens.CTRL(parent, listview=liste)\n",
                encoding="utf-8",
            )
            self.assertEqual(MODULE.scan(root), [])

    def test_summary_keeps_zero_categories_visible(self):
        summary = MODULE.summarize([])
        self.assertEqual(set(summary), set(MODULE.PATTERNS))
        self.assertTrue(all(value == 0 for value in summary.values()))


if __name__ == "__main__":
    unittest.main()
