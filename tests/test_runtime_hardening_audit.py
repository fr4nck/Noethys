#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import unittest
from pathlib import Path

from scripts import audit_runtime_hardening as hardening


class RuntimeHardeningAuditTests(unittest.TestCase):
    def test_full_runtime_triage_is_exported_for_the_hardening_pass(self):
        report = hardening.build_report()

        output = Path("tmp/runtime-hardening-audit.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        self.assertIn("RESULT_UNGUARDED", report["summary"])
        self.assertIn("RESULT_ASSIGN", report["summary"])
        self.assertIn("BARE_EXCEPT", report["summary"])
        self.assertTrue(all(value == 0 for value in report["zero_debt"].values()))


if __name__ == "__main__":
    unittest.main()
