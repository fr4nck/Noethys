#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tempfile
import textwrap
import unittest
from pathlib import Path

from scripts import audit_branch_assignment_gaps as audit


class BranchAssignmentExceptionTargetFlowTests(unittest.TestCase):
    def report_for(self, source):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sample.py").write_text(textwrap.dedent(source), encoding="utf-8")
            return audit.build_report(root)

    def test_except_target_clears_preexisting_local_after_handler(self):
        report = self.report_for('''
            def f(flag):
                value = 0
                try:
                    operation()
                except Exception as value:
                    pass
                if flag:
                    value = 1
                return value
        ''')
        findings = [item for item in report["findings"] if item["name"] == "value"]
        self.assertEqual(len(findings), 1)

    def test_except_target_is_cleared_even_if_reassigned_in_handler(self):
        report = self.report_for('''
            def f(flag):
                value = 0
                try:
                    operation()
                except Exception as value:
                    value = replacement()
                if flag:
                    value = 1
                return value
        ''')
        findings = [item for item in report["findings"] if item["name"] == "value"]
        self.assertEqual(len(findings), 1)

    def test_unrelated_except_target_keeps_other_local_guaranteed(self):
        report = self.report_for('''
            def f(flag):
                value = 0
                try:
                    operation()
                except Exception as exc:
                    pass
                if flag:
                    value = 1
                return value
        ''')
        self.assertFalse(any(item["name"] == "value" for item in report["findings"]))


if __name__ == "__main__":
    unittest.main()
