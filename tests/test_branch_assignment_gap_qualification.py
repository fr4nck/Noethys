#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import tempfile
import textwrap
import unittest
from pathlib import Path

from scripts import qualify_branch_assignment_gaps as audit


class BranchAssignmentQualificationTests(unittest.TestCase):
    def report_for(self, source):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sample.py").write_text(textwrap.dedent(source), encoding="utf-8")
            return audit.build_report(root)

    def test_same_guard_qualifies_first_read(self):
        report = self.report_for('''
            def f(flag):
                if flag:
                    value = 1
                if flag:
                    return value
        ''')
        finding = report["findings"][0]
        self.assertEqual(finding["classification"], "correlated_guard")
        self.assertEqual(finding["priority"], "low")

    def test_stronger_conjunctive_guard_qualifies_first_read(self):
        report = self.report_for('''
            def f(flag, ready):
                if flag:
                    value = 1
                if flag and ready:
                    return value
        ''')
        finding = report["findings"][0]
        self.assertEqual(finding["classification"], "correlated_guard")
        self.assertEqual(finding["priority"], "low")

    def test_different_guard_stays_high_priority(self):
        report = self.report_for('''
            def f(flag, other):
                if flag:
                    value = 1
                if other:
                    return value
        ''')
        finding = report["findings"][0]
        self.assertEqual(finding["classification"], "review")
        self.assertEqual(finding["priority"], "high")

    def test_read_in_later_condition_is_not_considered_protected(self):
        report = self.report_for('''
            def f(flag):
                if flag:
                    value = 1
                if value:
                    return value
        ''')
        finding = report["findings"][0]
        self.assertEqual(finding["classification"], "review")
        self.assertEqual(finding["priority"], "high")

    def test_same_false_branch_qualifies_else_assignment(self):
        report = self.report_for('''
            def f(flag):
                if flag:
                    pass
                else:
                    value = 1
                if flag:
                    return None
                else:
                    return value
        ''')
        finding = report["findings"][0]
        self.assertEqual(finding["classification"], "correlated_guard")
        self.assertEqual(finding["priority"], "low")

    def test_negated_guard_qualifies_false_branch(self):
        report = self.report_for('''
            def f(flag):
                if flag:
                    pass
                else:
                    value = 1
                if not flag:
                    return value
        ''')
        finding = report["findings"][0]
        self.assertEqual(finding["classification"], "correlated_guard")
        self.assertEqual(finding["priority"], "low")

    def test_exact_negated_guard_else_qualifies_body_assignment(self):
        report = self.report_for('''
            def f(flag):
                if flag:
                    value = 1
                if not flag:
                    return None
                else:
                    return value
        ''')
        finding = next(item for item in report["findings"] if item["name"] == "value")
        self.assertEqual(finding["classification"], "correlated_guard")
        self.assertEqual(finding["priority"], "low")

    def test_conjunctive_negated_guard_else_stays_high_priority(self):
        report = self.report_for('''
            def f(flag, ready):
                if flag:
                    value = 1
                if not flag and ready:
                    return None
                else:
                    return value
        ''')
        finding = next(item for item in report["findings"] if item["name"] == "value")
        self.assertEqual(finding["classification"], "review")
        self.assertEqual(finding["priority"], "high")

    def test_repeated_call_guard_stays_high_priority(self):
        report = self.report_for('''
            def f():
                if check():
                    value = 1
                if check():
                    return value
        ''')
        finding = next(item for item in report["findings"] if item["name"] == "value")
        self.assertEqual(finding["classification"], "review")
        self.assertEqual(finding["priority"], "high")

    def test_same_outer_guard_does_not_hide_nested_one_sided_assignment(self):
        report = self.report_for('''
            def f(outer, inner):
                if outer:
                    if inner:
                        value = 1
                if outer:
                    return value
        ''')
        finding = next(item for item in report["findings"] if item["name"] == "value")
        self.assertEqual(finding["classification"], "review")
        self.assertEqual(finding["priority"], "high")

    def test_same_outer_guard_qualifies_nested_exhaustive_assignment(self):
        report = self.report_for('''
            def f(outer, inner):
                if outer:
                    if inner:
                        value = 1
                    else:
                        value = 2
                if outer:
                    return value
        ''')
        finding = next(item for item in report["findings"] if item["name"] == "value")
        self.assertEqual(finding["classification"], "correlated_guard")
        self.assertEqual(finding["priority"], "low")

    def test_reassigned_name_guard_stays_high_priority(self):
        report = self.report_for('''
            def f(flag):
                if flag:
                    value = 1
                flag = True
                if flag:
                    return value
        ''')
        finding = next(item for item in report["findings"] if item["name"] == "value")
        self.assertEqual(finding["classification"], "review")
        self.assertEqual(finding["priority"], "high")

    def test_reassigned_subscript_guard_stays_high_priority(self):
        report = self.report_for('''
            def f(state):
                if state["ready"]:
                    value = 1
                state["ready"] = True
                if state["ready"]:
                    return value
        ''')
        finding = next(item for item in report["findings"] if item["name"] == "value")
        self.assertEqual(finding["classification"], "review")
        self.assertEqual(finding["priority"], "high")

    def test_direct_container_mutation_stays_high_priority(self):
        report = self.report_for('''
            def f(state):
                if state["ready"]:
                    value = 1
                state.clear()
                if state["ready"]:
                    return value
        ''')
        finding = next(item for item in report["findings"] if item["name"] == "value")
        self.assertEqual(finding["classification"], "review")
        self.assertEqual(finding["priority"], "high")

    def test_unassigned_else_may_not_flip_body_guard(self):
        report = self.report_for('''
            def f(flag):
                if flag:
                    value = 1
                else:
                    flag = True
                if flag:
                    return value
        ''')
        finding = next(item for item in report["findings"] if item["name"] == "value")
        self.assertEqual(finding["classification"], "review")
        self.assertEqual(finding["priority"], "high")

    def test_unassigned_body_may_not_flip_else_guard(self):
        report = self.report_for('''
            def f(flag):
                if flag:
                    flag = False
                else:
                    value = 1
                if flag:
                    return None
                else:
                    return value
        ''')
        finding = next(item for item in report["findings"] if item["name"] == "value")
        self.assertEqual(finding["classification"], "review")
        self.assertEqual(finding["priority"], "high")

    def test_repository_qualification_is_exported(self):
        report = audit.build_report()
        output = Path("tmp/branch-assignment-qualified-audit.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(
            f"BRANCH_ASSIGNMENT_QUALIFIED={report['count']} "
            f"{report['priorities']} {report['classifications']}"
        )
        self.assertEqual(sum(report["priorities"].values()), report["count"])
        self.assertIn("findings", report)


if __name__ == "__main__":
    unittest.main()
