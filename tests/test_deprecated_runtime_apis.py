#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tempfile
import textwrap
import unittest
from pathlib import Path

from scripts import audit_deprecated_runtime_apis as audit


class DeprecatedRuntimeApisTests(unittest.TestCase):
    def report_for(self, source):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sample.py").write_text(textwrap.dedent(source), encoding="utf-8")
            return audit.build_report(root)

    def test_thread_isalive_is_detected(self):
        report = self.report_for('''
            def stop(thread):
                if thread.isAlive():
                    thread.abort()
        ''')
        self.assertEqual(report["count"], 1)
        self.assertEqual(report["findings"][0]["kind"], "thread_isAlive")

    def test_modern_thread_api_is_clean(self):
        report = self.report_for('''
            def stop(thread):
                if thread.is_alive():
                    thread.abort()
        ''')
        self.assertEqual(report["count"], 0)

    def test_repository_has_no_removed_runtime_api(self):
        report = audit.build_report()
        self.assertEqual(report["findings"], [], msg=f"API supprimées restantes : {report['findings']}")


if __name__ == "__main__":
    unittest.main()
