#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import tempfile
import textwrap
import unittest
from pathlib import Path

from scripts import audit_branch_assignment_gaps as base
from scripts import qualify_branch_assignment_gaps as audit


class BranchAssignmentQualificationTests(unittest.TestCase):
    def report_for(self, source):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sample.py").write_text(textwrap.dedent(source), encoding="utf-8")
            return audit.build_report(root)

    def assert_all_review_high(self, report):
        self.assertGreater(report["count"], 0)
        self.assertEqual(report["priorities"], {"high": report["count"]})
        self.assertEqual(report["classifications"], {"review": report["count"]})
        self.assertTrue(all(item["priority"] == "high" for item in report["findings"]))
        self.assertTrue(all(item["classification"] == "review" for item in report["findings"]))

    def test_repeated_identity_guard_is_not_automatically_downgraded(self):
        report = self.report_for('''
            def f(flag):
                if flag is True:
                    value = 1
                if flag is True:
                    return value
        ''')
        self.assert_all_review_high(report)

    def test_dynamic_guard_is_not_automatically_downgraded(self):
        report = self.report_for('''
            def f(obj):
                if obj.ready:
                    value = 1
                if obj.ready:
                    return value
        ''')
        self.assert_all_review_high(report)

    def test_loop_back_edge_is_not_automatically_downgraded(self):
        report = self.report_for('''
            def f(flag, condition):
                if flag is True:
                    value = 1
                while condition:
                    if flag is True:
                        return value
                    flag = True
        ''')
        self.assert_all_review_high(report)

    def test_delete_after_branch_remains_visible(self):
        report = self.report_for('''
            def f(flag):
                if flag:
                    value = 1
                del value
        ''')
        self.assert_all_review_high(report)
        self.assertEqual(report["findings"][0]["name"], "value")

    def test_qualification_preserves_every_raw_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sample.py").write_text(textwrap.dedent('''
                def f(first, second):
                    if first:
                        left = 1
                    print(left)
                    if second:
                        right = 2
                    return right
            '''), encoding="utf-8")
            raw = base.build_report(root)
            report = audit.build_report(root)

        raw_keys = {
            (item["file"], item["function"], item["if_line"], item["line"], item["name"])
            for item in raw["findings"]
        }
        qualified_keys = {
            (item["file"], item["function"], item["if_line"], item["line"], item["name"])
            for item in report["findings"]
        }
        self.assertEqual(qualified_keys, raw_keys)
        self.assertEqual(report["count"], raw["count"])
        self.assert_all_review_high(report)

    def test_explicit_safe_registry_is_exact_and_unambiguous_on_repository(self):
        report = audit.build_report()
        registry = report["explicit_safe_registry"]
        self.assertEqual(registry["configured"], len(audit.EXPLICIT_SAFE))
        self.assertEqual(registry["matched"], len(audit.EXPLICIT_SAFE))
        self.assertEqual(registry["unmatched"], [])
        self.assertEqual(registry["ambiguous"], [])

        safe_keys = {
            audit.qualification_key(item)
            for item in report["findings"]
            if item["classification"] == "explicit_safe"
        }
        self.assertEqual(safe_keys, set(audit.EXPLICIT_SAFE))
        self.assertTrue(
            all(
                item["priority"] == "low"
                for item in report["findings"]
                if item["classification"] == "explicit_safe"
            )
        )

    def test_stale_explicit_safe_structure_is_not_downgraded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "Dlg" / "DLG_Saisie_portail_demande.py"
            target.parent.mkdir(parents=True)
            target.write_text(textwrap.dedent("""
                def MAJ_informations(flag):
                    if flag:
                        dict_periodes = {}
                    return dict_periodes
            """), encoding="utf-8")
            report = audit.build_report(root)

        candidate = next(
            item for item in report["findings"]
            if item["function"] == "MAJ_informations" and item["name"] == "dict_periodes"
        )
        self.assertEqual(candidate["classification"], "review")
        self.assertEqual(candidate["priority"], "high")

    def test_explicit_safe_fingerprint_covers_surrounding_control_flow(self):
        source = (base.NOETHYS / "Dlg" / "DLG_Saisie_portail_demande.py").read_text(encoding="utf-8")
        marker = "    def Traitement_recus(self):"
        prefix, suffix = source.split(marker, 1)
        original = 'if self.dict_parametres["methode_envoi"] != "email" :'
        changed = 'if self.dict_parametres["methode_envoi"] == "courrier" :'
        self.assertIn(original, suffix)
        suffix = suffix.replace(original, changed, 1)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "Dlg" / "DLG_Saisie_portail_demande.py"
            target.parent.mkdir(parents=True)
            target.write_text(prefix + marker + suffix, encoding="utf-8")
            report = audit.build_report(root)

        candidate = next(
            item for item in report["findings"]
            if item["function"] == "Traitement_recus" and item["name"] == "reponse"
        )
        self.assertEqual(candidate["classification"], "review")
        self.assertEqual(candidate["priority"], "high")
        self.assertGreater(len(report["explicit_safe_registry"]["unmatched"]), 0)

    def test_repository_qualification_is_exported_without_hidden_candidates(self):
        raw = base.build_report()
        report = audit.build_report()
        output = Path("tmp/branch-assignment-qualified-audit.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(
            f"BRANCH_ASSIGNMENT_QUALIFIED={report['count']} "
            f"{report['priorities']} {report['classifications']}"
        )
        self.assertEqual(report["count"], raw["count"])
        self.assertEqual(report["explicit_safe_registry"]["unmatched"], [])
        self.assertEqual(report["explicit_safe_registry"]["ambiguous"], [])
        self.assertEqual(report["priorities"].get("low", 0), len(audit.EXPLICIT_SAFE))
        self.assertEqual(
            report["priorities"].get("high", 0),
            report["count"] - len(audit.EXPLICIT_SAFE),
        )
        self.assertIn("findings", report)


if __name__ == "__main__":
    unittest.main()
