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

    def test_terminating_branch_propagates_continuing_definition(self):
        report = self.report_for('''
            def f(flag, other):
                if flag:
                    return None
                else:
                    value = 1
                if other:
                    value = 2
                return value
        ''')
        self.assertEqual(report["count"], 0)

    def test_loop_target_is_already_defined_inside_loop(self):
        report = self.report_for('''
            def f(rows):
                for value in rows:
                    if value is not None:
                        value = str(value)
                    print(value)
        ''')
        self.assertEqual(report["count"], 0)

    def test_assignment_in_both_branches_is_propagated_to_following_if(self):
        report = self.report_for('''
            def f(flag, other):
                if flag:
                    value = 1
                else:
                    value = 2
                if other:
                    value = 3
                return value
        ''')
        self.assertEqual(report["count"], 0)

    def test_exhaustive_if_elif_else_is_propagated(self):
        report = self.report_for('''
            def f(mode, other):
                if mode == "a":
                    value = 1
                elif mode == "b":
                    value = 2
                elif mode == "c":
                    value = 3
                else:
                    value = 4
                if other:
                    value = 5
                return value
        ''')
        self.assertEqual(report["count"], 0)

    def test_nested_conditional_assignment_is_not_treated_as_guaranteed(self):
        report = self.report_for('''
            def f(flag, nested, other):
                if flag:
                    if nested:
                        value = 1
                else:
                    value = 2
                if other:
                    value = 3
                return value
        ''')
        self.assertTrue(any(item["name"] == "value" for item in report["findings"]))

    def test_comprehension_target_does_not_bind_enclosing_function(self):
        report = self.report_for('''
            def f(flag, rows):
                if flag:
                    left = [tuple(value) for value in rows]
                return [tuple(value) for value in rows]
        ''')
        self.assertFalse(any(item["name"] == "value" for item in report["findings"]))

    def test_comprehension_outer_iterable_read_remains_visible(self):
        report = self.report_for('''
            def f(flag):
                if flag:
                    rows = [1]
                return [value for value in rows]
        ''')
        findings = [item for item in report["findings"] if item["name"] == "rows"]
        self.assertEqual(len(findings), 1)

    def test_previous_comprehension_target_is_local_in_next_generator(self):
        report = self.report_for('''
            def f(flag, rows):
                if flag:
                    marker = [(left, right) for left in rows for right in left]
                return [(left, right) for left in rows for right in left]
        ''')
        self.assertFalse(any(item["name"] in {"left", "right"} for item in report["findings"]))

    def test_try_assignment_with_terminating_handler_is_propagated(self):
        report = self.report_for('''
            def f(flag):
                try:
                    value = operation()
                except Exception:
                    return None
                if flag:
                    value = 2
                return value
        ''')
        self.assertEqual(report["count"], 0)

    def test_try_assignment_with_non_terminating_handler_is_not_guaranteed(self):
        report = self.report_for('''
            def f(flag):
                try:
                    value = operation()
                except Exception:
                    pass
                if flag:
                    value = 2
                return value
        ''')
        self.assertTrue(any(item["name"] == "value" for item in report["findings"]))

    def test_finally_assignment_is_guaranteed_on_continuing_paths(self):
        report = self.report_for('''
            def f(flag):
                try:
                    operation()
                finally:
                    value = 1
                if flag:
                    value = 2
                return value
        ''')
        self.assertEqual(report["count"], 0)

    def test_with_body_assignment_is_not_guaranteed_after_suppression(self):
        report = self.report_for('''
            def f(flag):
                with suppress(Exception):
                    value = operation()
                if flag:
                    value = 2
                return value
        ''')
        findings = [item for item in report["findings"] if item["name"] == "value"]
        self.assertEqual(len(findings), 1)

    def test_with_as_target_is_guaranteed_on_continuing_path(self):
        report = self.report_for('''
            def f(flag):
                with manager() as handle:
                    operation()
                if flag:
                    handle = replacement()
                return handle
        ''')
        self.assertFalse(any(item["name"] == "handle" for item in report["findings"]))

    def test_later_with_target_is_not_guaranteed_after_outer_suppression(self):
        report = self.report_for('''
            def f(flag):
                with outer() as first, inner() as value:
                    operation()
                if flag:
                    value = replacement()
                return value
        ''')
        findings = [item for item in report["findings"] if item["name"] == "value"]
        self.assertEqual(len(findings), 1)

    def test_first_with_target_remains_guaranteed_with_multiple_managers(self):
        report = self.report_for('''
            def f(flag):
                with outer() as first, inner() as value:
                    operation()
                if flag:
                    first = replacement()
                return first
        ''')
        self.assertFalse(any(item["name"] == "first" for item in report["findings"]))

    def test_delete_removes_definition_before_later_branch(self):
        report = self.report_for('''
            def f(flag, other):
                if flag:
                    value = 1
                    del value
                else:
                    value = 2
                if other:
                    value = 3
                return value
        ''')
        findings = [item for item in report["findings"] if item["name"] == "value"]
        self.assertEqual(len(findings), 1)

    def test_delete_on_unassigned_path_is_detected_as_first_event(self):
        report = self.report_for('''
            def f(flag):
                if flag:
                    value = 1
                del value
        ''')
        findings = [item for item in report["findings"] if item["name"] == "value"]
        self.assertEqual(len(findings), 1)

    def test_repository_inventory_is_exported(self):
        report = audit.build_report()
        output = Path("tmp/branch-assignment-audit.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"BRANCH_ASSIGNMENT_GAPS={report['count']}")
        self.assertIn("findings", report)


if __name__ == "__main__":
    unittest.main()