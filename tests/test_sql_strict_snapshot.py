#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import unittest
from pathlib import Path

from scripts import audit_sql_strict as audit


ROOT = Path(__file__).resolve().parents[1]


class SqlStrictSnapshotTests(unittest.TestCase):
    def test_sql_strict_inventory_is_exported(self):
        candidates = audit.scan(ROOT / "noethys")
        findings = []
        for item in candidates:
            findings.append({
                "classification": item.classification,
                "risk": item.risk,
                "file": str(item.path.relative_to(ROOT)).replace("\\", "/"),
                "line": item.line,
                "reason": item.reason,
                "ungrouped_items": list(item.ungrouped_items),
                "sql": item.sql,
            })

        counts = {
            name: sum(1 for item in findings if item["classification"] == name)
            for name in ("REVIEW", "DEDUPE", "SAFE")
        }
        report = {"counts": counts, "findings": findings}

        output = ROOT / "tmp" / "sql-strict-audit.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

        self.assertEqual(sum(counts.values()), len(findings))


if __name__ == "__main__":
    unittest.main()
