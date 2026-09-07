import tempfile
import unittest
from pathlib import Path

from tools import audit_ui_commands as audit


class UICommandAuditScannerTests(unittest.TestCase):
    def _scan_source(self, source):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "noethys"
            package.mkdir()
            (package / "sample.py").write_text(source, encoding="utf-8")
            return audit.scan(root)

    def test_button_bind_and_empty_handler_are_correlated(self):
        result = self._scan_source(
            """
class Dialog:
    def __init__(self):
        self.button = wx.Button(self, wx.ID_ANY, label='Tester')
        self.Bind(wx.EVT_BUTTON, self.OnTester, self.button)

    def OnTester(self, event):
        pass
"""
        )
        self.assertEqual(len(result.commands), 1)
        command = result.commands[0]
        self.assertEqual(command.label, "Tester")
        self.assertEqual(command.handler, "self.OnTester")
        self.assertEqual(command.status, "FAIL")
        self.assertEqual(command.defect_type, "HANDLER_EMPTY")
        self.assertEqual(command.severity, "P2")

    def test_menu_bind_by_id_is_correlated_without_claiming_functional_pass(self):
        result = self._scan_source(
            """
class Dialog:
    def BuildMenu(self):
        menu.Append(1234, 'Exporter')
        self.Bind(wx.EVT_MENU, self.OnExporter, id=1234)

    def OnExporter(self, event):
        return exporter.run()
"""
        )
        self.assertEqual(len(result.commands), 1)
        command = result.commands[0]
        self.assertEqual(command.label, "Exporter")
        self.assertEqual(command.handler, "self.OnExporter")
        self.assertEqual(command.status, "BLOCKED")
        self.assertEqual(command.defect_type, "HUMAN_RECIPE_REQUIRED")

    def test_unbound_command_is_not_marked_pass(self):
        result = self._scan_source(
            """
class Dialog:
    def __init__(self):
        self.button = wx.BitmapButton(self, wx.ID_ANY)
"""
        )
        self.assertEqual(len(result.commands), 1)
        self.assertNotEqual(result.commands[0].status, "PASS")
        self.assertEqual(result.commands[0].defect_type, "STATIC_BIND_UNRESOLVED")

    def test_known_rows_use_only_allowed_statuses_and_severity_on_failures(self):
        rows = audit.known_rows()
        self.assertTrue(rows)
        for row in rows:
            self.assertIn(row["Statut"], audit.STATUSES)
            if row["Statut"] == "FAIL":
                self.assertIn(row["Gravité"], {"P0", "P1", "P2", "P3"})


class UICommandAuditRepositoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]
        cls.result = audit.scan(cls.root)

    def test_repository_sources_parse(self):
        self.assertEqual(self.result.parse_errors, [])

    def test_inventory_is_not_trivially_incomplete(self):
        self.assertGreater(self.result.python_files, 100)
        self.assertGreater(self.result.commands, [])
        self.assertGreater(len(self.result.commands), 100)
        self.assertGreater(self.result.binding_count, 100)

    def test_every_command_has_valid_status_and_trace(self):
        for command in self.result.commands:
            self.assertIn(command.status, audit.STATUSES)
            self.assertTrue(command.trace, msg=f"trace absente pour {command.path}:{command.line}")
            self.assertNotEqual(command.status, "PASS", msg="Le scan statique seul ne doit jamais produire PASS")

    def test_failures_have_a_severity(self):
        for command in self.result.commands:
            if command.status == "FAIL":
                self.assertIn(command.severity, {"P0", "P1", "P2", "P3"})


if __name__ == "__main__":
    unittest.main()
