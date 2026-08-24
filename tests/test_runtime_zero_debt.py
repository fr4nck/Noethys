#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import unittest
from pathlib import Path

from scripts import audit_runtime_patterns as audit


class RuntimeZeroDebtTests(unittest.TestCase):
    ZERO_DEBT = (
        "DB_UNCLOSED",
        "PY2_BUILTINS",
        "UNSAFE_EXEC",
        "INVALID_ESCAPE",
        "ENCODING_MBCS",
    )

    def test_runtime_zero_debt_categories_stay_empty_and_snapshot_full_report(self):
        report = audit.run_audit()

        output = Path("tmp/runtime-audit.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        remaining = {
            key: report.get(key, [])
            for key in self.ZERO_DEBT
            if report.get(key)
        }
        self.assertEqual(remaining, {})


if __name__ == "__main__":
    unittest.main()
