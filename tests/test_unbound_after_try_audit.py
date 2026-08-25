#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
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

    def test_repository_findings_are_only_the_safe_topwindow_guard_idiom(self):
        """Les signaux résiduels partagent tous le même garde corrélé historique.

        ``topWindow`` est lié avant ``nomWindow = topWindow.GetName()``. Si l'un
        de ces appels échoue, le handler force ``nomWindow = None`` ; la branche
        qui relit ``topWindow`` n'est donc atteignable que lorsque le ``try`` a
        réussi. On garde les occurrences visibles dans l'inventaire, mais toute
        autre forme d'UnboundLocalError potentiel doit faire échouer ce contrat.
        """
        findings = audit.scan()
        self.assertGreater(len(findings), 0)

        for item in findings:
            self.assertEqual(item["name"], "topWindow", msg=f"Signal non qualifié : {item}")
            path = audit.NOETHYS / item["file"]
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            window = "\n".join(lines[item["try_line"] - 1:item["read_line"]])
            self.assertRegex(window, r"topWindow\s*=\s*wx\.GetApp\(\)\.GetTopWindow\(\)")
            self.assertRegex(window, r"nomWindow\s*=\s*topWindow\.GetName\(\)")
            self.assertRegex(window, r"except\s+Exception\s*:\s*\n\s*nomWindow\s*=\s*None")
            self.assertRegex(window, r"if\s+nomWindow\s*==\s*[\"']general[\"']")


if __name__ == "__main__":
    unittest.main()
