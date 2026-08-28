#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tempfile
import textwrap
import unittest
from pathlib import Path

from scripts import audit_branch_assignment_gaps as audit


class BranchAssignmentComprehensionScopeTests(unittest.TestCase):
    def test_comprehension_local_store_does_not_hide_later_outer_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sample.py").write_text(textwrap.dedent('''
                def f(flag, rows):
                    if flag:
                        value = 1
                    [value for value in rows]
                    return value
            '''), encoding="utf-8")
            report = audit.build_report(root)

        findings = [item for item in report["findings"] if item["name"] == "value"]
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["detail"], "body_only")


if __name__ == "__main__":
    unittest.main()
