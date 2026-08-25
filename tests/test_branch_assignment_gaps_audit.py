#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import tempfile
import textwrap
import unittest
from pathlib import Path

from scripts import audit_branch_assignment_gaps as audit


class BranchAssignmentGapTests(unittest.TestCase):
    def report_for(self, source):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sample.py").write_text(textwrap.dedent(source), encoding="utf-8")
            return audit.build_report(root)

    def test_one_sided_assignment_then_read_is_detected(self):
        report = self.report_for('''
            def f(flag):
                if flag:
                    value = 1
                else:
                    pass
                return value
        ''')
        self.assertEqual(report["count"], 1)
        self.assertEqual(report["findings"][0]["name"], "value")

    def test_previous_definition_makes_branch_safe(self):
        report = self.report_for('''
            def f(flag):
                value = None
                if flag:
                    value = 1
                return value
        ''')
        self.assertEqual(report["count"], 0)

    def test_terminating_unassigned_branch_is_safe(self):
        report = self.report_for('''
            def f(flag):
                if flag:
                    return None
                else:
                    value = 1
                return value
        ''')
        self.assertEqual(report["count"], 0)

    def test_repository_inventory_is_exported(self):
        report = audit.build_report()
        output = Path("tmp/branch-assignment-audit.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"BRANCH_ASSIGNMENT_GAPS={report['count']}")
        self.assertIn("findings", report)


if __name__ == "__main__":
    unittest.main()
