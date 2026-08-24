#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from scripts import audit_pre_rc


class AuditPreRcTests(unittest.TestCase):
    def test_collect_and_write_reports_keep_inventories_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "noethys"
            root.mkdir()
            output = Path(tmp) / "reports"

            sql_items = [
                SimpleNamespace(
                    classification="REVIEW",
                    risk="HIGH",
                    path=root / "Ol" / "OL_Test.py",
                    line=12,
                    reason="revue",
                    ungrouped_items=["libelle"],
                    summary=lambda: "SELECT libelle FROM test GROUP BY id",
                ),
                SimpleNamespace(
                    classification="SAFE",
                    risk="SAFE",
                    path=root / "Ol" / "OL_Safe.py",
                    line=8,
                    reason="ok",
                    ungrouped_items=[],
                    summary=lambda: "SELECT id, COUNT(*) FROM test GROUP BY id",
                ),
            ]
            wx_items = [
                {
                    "kind": "constructor_callback_before_dependency",
                    "file": "noethys/Ctrl/CTRL_Test.py",
                    "line": 10,
                },
                {
                    "kind": "visual_parent_business_coupling",
                    "file": "noethys/Ctrl/CTRL_Test.py",
                    "line": 20,
                },
            ]
            legacy_items = [
                {
                    "code": "ctrl_outils_historique",
                    "path": "noethys/Ol/OL_Test.py",
                    "line": 3,
                    "text": "CTRL_ObjectListView.CTRL_Outils",
                }
            ]

            with mock.patch.object(audit_pre_rc.audit_sql_strict, "scan", return_value=sql_items), \
                    mock.patch.object(audit_pre_rc.audit_wx_lifecycle, "scan", return_value=wx_items), \
                    mock.patch.object(audit_pre_rc.audit_legacy_list_tools, "scan", return_value=legacy_items):
                data = audit_pre_rc.run(root, output)

            self.assertEqual(data["summary"]["sql"]["REVIEW"], 1)
            self.assertEqual(data["summary"]["sql"]["SAFE"], 1)
            self.assertEqual(
                data["summary"]["wx_lifecycle"]["high_risk"][
                    "constructor_callback_before_dependency"
                ],
                1,
            )
            self.assertEqual(data["summary"]["legacy_list_tools"]["screens"], 1)

            summary = json.loads((output / "pre-rc-summary.json").read_text(encoding="utf-8"))
            sql_report = json.loads((output / "sql-strict-review.json").read_text(encoding="utf-8"))
            wx_report = json.loads((output / "wx-lifecycle-audit.json").read_text(encoding="utf-8"))
            legacy_report = json.loads((output / "legacy-list-tools-audit.json").read_text(encoding="utf-8"))

            self.assertEqual(summary["sql"]["REVIEW"], 1)
            self.assertEqual(len(sql_report["findings"]), 1)
            self.assertEqual(len(wx_report["findings"]), 2)
            self.assertEqual(legacy_report["screens"], ["noethys/Ol/OL_Test.py"])

    def test_high_risk_wx_categories_are_explicit_even_when_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "noethys"
            root.mkdir()

            with mock.patch.object(audit_pre_rc.audit_sql_strict, "scan", return_value=[]), \
                    mock.patch.object(audit_pre_rc.audit_wx_lifecycle, "scan", return_value=[]), \
                    mock.patch.object(audit_pre_rc.audit_legacy_list_tools, "scan", return_value=[]):
                data = audit_pre_rc.collect(root)

            self.assertEqual(
                data["summary"]["wx_lifecycle"]["high_risk"],
                {
                    "constructor_parent_callback": 0,
                    "constructor_callback_before_dependency": 0,
                },
            )


if __name__ == "__main__":
    unittest.main()
