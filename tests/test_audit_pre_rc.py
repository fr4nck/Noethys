#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from scripts import audit_pre_rc


def _teamworks_report(findings=None, *, complete=True):
    findings = list(findings or [])
    kinds = {}
    priorities = {}
    for item in findings:
        kinds[item["kind"]] = kinds.get(item["kind"], 0) + 1
        priorities[item["priority"]] = priorities.get(item["priority"], 0) + 1
    return {
        "coverage": {
            "found": 2,
            "read": 2 if complete else 1,
            "parsed": 2 if complete else 1,
            "complete": complete,
            "failures": [] if complete else ["fixture.py: lecture: UnicodeDecodeError: test"],
        },
        "count": len(findings),
        "kinds": kinds,
        "priorities": priorities,
        "findings": findings,
    }


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
                    "kind": "use_after_destroy",
                    "file": "noethys/Dlg/DLG_Test.py",
                    "line": 15,
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
            teamworks_items = [
                {
                    "kind": "accessor_not_called",
                    "priority": "high",
                    "file": "Dlg/DLG_Test.py",
                    "line": 42,
                    "detail": "accesseur comparé sans appel",
                }
            ]

            with mock.patch.object(audit_pre_rc.audit_sql_strict, "scan", return_value=sql_items), \
                    mock.patch.object(audit_pre_rc.audit_wx_lifecycle, "scan", return_value=wx_items), \
                    mock.patch.object(audit_pre_rc.audit_legacy_list_tools, "scan", return_value=legacy_items), \
                    mock.patch.object(
                        audit_pre_rc.audit_teamworks_signatures,
                        "build_report",
                        return_value=_teamworks_report(teamworks_items),
                    ):
                data = audit_pre_rc.run(root, output)

            self.assertEqual(data["summary"]["sql"]["REVIEW"], 1)
            self.assertEqual(data["summary"]["sql"]["SAFE"], 1)
            self.assertEqual(
                data["summary"]["wx_lifecycle"]["high_risk"][
                    "constructor_callback_before_dependency"
                ],
                1,
            )
            self.assertEqual(
                data["summary"]["wx_lifecycle"]["high_risk"]["use_after_destroy"],
                1,
            )
            self.assertEqual(data["summary"]["legacy_list_tools"]["screens"], 1)
            self.assertEqual(data["summary"]["teamworks_signatures"]["total"], 1)
            self.assertTrue(data["summary"]["teamworks_signatures"]["coverage"]["complete"])

            summary = json.loads((output / "pre-rc-summary.json").read_text(encoding="utf-8"))
            sql_report = json.loads((output / "sql-strict-review.json").read_text(encoding="utf-8"))
            wx_report = json.loads((output / "wx-lifecycle-audit.json").read_text(encoding="utf-8"))
            legacy_report = json.loads((output / "legacy-list-tools-audit.json").read_text(encoding="utf-8"))
            teamworks_report = json.loads((output / "teamworks-signatures-audit.json").read_text(encoding="utf-8"))

            self.assertEqual(summary["sql"]["REVIEW"], 1)
            self.assertEqual(summary["teamworks_signatures"]["total"], 1)
            self.assertEqual(len(sql_report["findings"]), 1)
            self.assertEqual(len(wx_report["findings"]), 3)
            self.assertEqual(legacy_report["screens"], ["noethys/Ol/OL_Test.py"])
            self.assertEqual(teamworks_report["findings"], teamworks_items)

    def test_high_risk_wx_categories_are_explicit_even_when_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "noethys"
            root.mkdir()

            with mock.patch.object(audit_pre_rc.audit_sql_strict, "scan", return_value=[]), \
                    mock.patch.object(audit_pre_rc.audit_wx_lifecycle, "scan", return_value=[]), \
                    mock.patch.object(audit_pre_rc.audit_legacy_list_tools, "scan", return_value=[]), \
                    mock.patch.object(
                        audit_pre_rc.audit_teamworks_signatures,
                        "build_report",
                        return_value=_teamworks_report([]),
                    ):
                data = audit_pre_rc.collect(root)

            self.assertEqual(
                data["summary"]["wx_lifecycle"]["high_risk"],
                {
                    "constructor_parent_callback": 0,
                    "constructor_callback_before_dependency": 0,
                    "use_after_destroy": 0,
                },
            )
            self.assertEqual(data["summary"]["teamworks_signatures"]["total"], 0)
            self.assertTrue(data["summary"]["teamworks_signatures"]["coverage"]["complete"])

    def test_teamworks_signature_coverage_failure_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "noethys"
            root.mkdir()

            with mock.patch.object(audit_pre_rc.audit_sql_strict, "scan", return_value=[]), \
                    mock.patch.object(audit_pre_rc.audit_wx_lifecycle, "scan", return_value=[]), \
                    mock.patch.object(audit_pre_rc.audit_legacy_list_tools, "scan", return_value=[]), \
                    mock.patch.object(
                        audit_pre_rc.audit_teamworks_signatures,
                        "build_report",
                        return_value=_teamworks_report([], complete=False),
                    ):
                data = audit_pre_rc.collect(root)

            coverage = data["summary"]["teamworks_signatures"]["coverage"]
            self.assertFalse(coverage["complete"])
            self.assertEqual(coverage["found"], 2)
            self.assertEqual(coverage["parsed"], 1)


if __name__ == "__main__":
    unittest.main()
