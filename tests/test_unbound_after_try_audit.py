#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import tempfile
import textwrap
import unittest
from pathlib import Path

from scripts import audit_unbound_after_try as audit


class UnboundAfterTryAuditTests(unittest.TestCase):
    def scan_source(self, source):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.py"
            path.write_text(textwrap.dedent(source), encoding="utf-8")
            return audit.scan(Path(tmp))

    def test_detects_value_defined_only_in_try_and_used_after_handler(self):
        findings = self.scan_source('''
            def f():
                try:
                    value = operation()
                except Exception:
                    pass
                return value
        ''')
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["name"], "value")

    def test_ignores_value_defined_before_try(self):
        findings = self.scan_source('''
            def f():
                value = None
                try:
                    value = operation()
                except Exception:
                    pass
                return value
        ''')
        self.assertEqual(findings, [])

    def test_ignores_handler_that_returns(self):
        findings = self.scan_source('''
            def f():
                try:
                    value = operation()
                except Exception:
                    return None
                return value
        ''')
        self.assertEqual(findings, [])

    def test_reassignment_in_following_try_precedes_its_reads(self):
        findings = self.scan_source('''
            def f():
                try:
                    value = first()
                except Exception:
                    pass
                try:
                    value = second()
                    if value:
                        return value
                except Exception:
                    pass
                return None
        ''')
        self.assertEqual(findings, [])

    def test_for_target_is_bound_before_reads_in_loop_body(self):
        findings = self.scan_source('''
            def f(items):
                try:
                    for item in items:
                        consume(item)
                except Exception:
                    pass
                for item in items:
                    consume(item)
        ''')
        self.assertEqual(findings, [])

    def test_repository_inventory_is_exported(self):
        findings = audit.scan()
        output = Path("tmp/unbound-after-try-audit.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps({"count": len(findings), "findings": findings}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        self.assertIsInstance(findings, list)


if __name__ == "__main__":
    unittest.main()
