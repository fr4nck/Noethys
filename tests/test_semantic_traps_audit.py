#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import tempfile
import textwrap
import unittest
from pathlib import Path

from scripts import audit_semantic_traps as audit


class SemanticTrapsAuditTests(unittest.TestCase):
    def report_for(self, source):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sample.py").write_text(textwrap.dedent(source), encoding="utf-8")
            return audit.build_report(root)

    def test_mutated_mutable_default_is_high_priority(self):
        report = self.report_for('''
            def f(items=[]):
                items.append(1)
        ''')
        self.assertEqual(report["findings"][0]["kind"], "mutable_default_mutated")
        self.assertEqual(report["findings"][0]["priority"], "high")

    def test_directly_returned_mutable_default_is_visible(self):
        report = self.report_for('''
            def f(items=[]):
                return items
        ''')
        self.assertEqual(report["findings"][0]["kind"], "mutable_default_escape")

    def test_validation_save_asymmetry_is_detected(self):
        report = self.report_for('''
            class Dialog:
                def OnBoutonOk(self):
                    self.ctrl_a.Validation()
                    self.ctrl_b.Validation()
                    self.ctrl_a.Sauvegarde()
        ''')
        findings = [item for item in report["findings"] if item["kind"] == "validation_without_save"]
        self.assertEqual([item["control"] for item in findings], ["ctrl_b"])

    def test_modal_without_destroy_is_detected(self):
        report = self.report_for('''
            class Dialog:
                def OnBoutonOk(self):
                    dlg = MessageDialog(self)
                    dlg.ShowModal()
        ''')
        self.assertTrue(any(item["kind"] == "modal_without_destroy" for item in report["findings"]))

    def test_repository_inventory_is_exported(self):
        report = audit.build_report()
        output = Path("tmp/semantic-traps-audit.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"SEMANTIC_TRAPS={report['count']} {report['kinds']} {report['priorities']}")
        self.assertIn("findings", report)
        self.assertIn("kinds", report)
        self.assertIn("priorities", report)


if __name__ == "__main__":
    unittest.main()
