#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import tempfile
import textwrap
import unittest
from pathlib import Path

from scripts import audit_silent_exception_handlers as audit


class SilentExceptionHandlersAuditTests(unittest.TestCase):
    def report_for(self, source):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.py"
            path.write_text(textwrap.dedent(source), encoding="utf-8")
            return audit.build_report(Path(tmp))

    def test_optional_import_is_low_priority(self):
        report = self.report_for('''
            try:
                import optional_module
            except Exception:
                pass
        ''')
        self.assertEqual(report["findings"][0]["classification"], "optional_import")
        self.assertEqual(report["findings"][0]["priority"], "low")

    def test_silent_db_write_is_high_priority(self):
        report = self.report_for('''
            def f(DB):
                try:
                    DB.ExecuterReq("DELETE FROM t")
                except Exception:
                    pass
        ''')
        self.assertEqual(report["findings"][0]["classification"], "silent_business_mutation")
        self.assertEqual(report["findings"][0]["priority"], "high")

    def test_silent_select_with_local_assignment_is_not_high_priority(self):
        report = self.report_for('''
            def f(DB):
                try:
                    DB.ExecuterReq("SELECT value FROM t")
                    value = DB.ResultatReq()[0]
                except Exception:
                    pass
        ''')
        self.assertEqual(report["findings"][0]["classification"], "silent_state_fallback")
        self.assertEqual(report["findings"][0]["priority"], "medium")

    def test_business_save_hidden_by_pass_is_high_priority(self):
        report = self.report_for('''
            def f(ctrl):
                try:
                    ctrl.Sauvegarde()
                except Exception:
                    pass
        ''')
        self.assertEqual(report["findings"][0]["priority"], "high")

    def test_repository_inventory_is_exported(self):
        report = audit.build_report()
        output = Path("tmp/silent-exception-audit.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        self.assertIn("findings", report)


if __name__ == "__main__":
    unittest.main()
