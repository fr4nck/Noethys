#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tempfile
import textwrap
import unittest
from pathlib import Path

from scripts import audit_branch_assignment_gaps as audit


class BranchAssignmentDeletionFlowTests(unittest.TestCase):
    def report_for(self, source):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sample.py").write_text(textwrap.dedent(source), encoding="utf-8")
            return audit.build_report(root)

    def test_conditional_delete_of_predefined_name_remains_a_candidate(self):
        report = self.report_for('''
            def f(flag):
                value = 1
                if flag:
                    del value
                return value
        ''')
        findings = [item for item in report["findings"] if item["name"] == "value"]
        self.assertEqual(len(findings), 1)

    def test_with_target_deleted_in_body_is_not_guaranteed_after_with(self):
        report = self.report_for('''
            def f(flag):
                with manager() as value:
                    del value
                if flag:
                    value = replacement()
                return value
        ''')
        findings = [item for item in report["findings"] if item["name"] == "value"]
        self.assertEqual(len(findings), 1)


if __name__ == "__main__":
    unittest.main()
