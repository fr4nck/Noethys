#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import tempfile
import textwrap
import unittest
from pathlib import Path

from scripts import audit_semantic_traps as audit


class SemanticTrapsAuditTests(unittest.TestCase):
    _repository_report = None

    def report_for(self, source):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sample.py").write_text(textwrap.dedent(source), encoding="utf-8")
            return audit.build_report(root)

    @classmethod
    def repository_report(cls):
        if cls._repository_report is None:
            cls._repository_report = audit.build_report()
        return cls._repository_report

    def test_mutated_mutable_default_is_high_priority(self):
        report = self.report_for('''
            def f(items=[]):
                items.append(1)
        ''')
        self.assertEqual(report["findings"][0]["kind"], "mutable_default_mutated")
        self.assertEqual(report["findings"][0]["priority"], "high")

    def test_empty_dict_item_assignment_is_high_priority(self):
        report = self.report_for('''
            def f(values={}):
                values["x"] = 1
        ''')
        self.assertEqual(report["findings"][0]["kind"], "mutable_default_mutated")
        self.assertEqual(report["findings"][0]["detail"], "item_mutation")

    def test_slice_assignment_can_mutate_empty_shared_default(self):
        report = self.report_for('''
            def f(items=[]):
                items[:] = [1]
        ''')
        finding = report["findings"][0]
        self.assertEqual(finding["kind"], "mutable_default_mutated")
        self.assertEqual(finding["priority"], "high")

    def test_slice_augassign_can_mutate_empty_shared_default(self):
        report = self.report_for('''
            def f(items=[]):
                items[:] += [1]
        ''')
        finding = report["findings"][0]
        self.assertEqual(finding["kind"], "mutable_default_mutated")
        self.assertEqual(finding["priority"], "high")
        self.assertEqual(finding["detail"], "slice_mutation")

    def test_rebind_before_append_does_not_mutate_shared_default(self):
        report = self.report_for('''
            def f(items=[]):
                items = []
                items.append(1)
                return len(items)
        ''')
        finding = report["findings"][0]
        self.assertEqual(finding["kind"], "mutable_default_qualified")
        self.assertEqual(finding["priority"], "low")
        self.assertEqual(finding["detail"], "rebound_before_mutation")

    def test_sorting_empty_default_is_qualified_not_high(self):
        report = self.report_for('''
            def f(items=[]):
                items.sort()
        ''')
        finding = report["findings"][0]
        self.assertEqual(finding["kind"], "mutable_default_qualified")
        self.assertEqual(finding["priority"], "low")
        self.assertEqual(finding["detail"], "empty_default_non_growing:sort")

    def test_sorting_nonempty_default_remains_high(self):
        report = self.report_for('''
            def f(items=[2, 1]):
                items.sort()
        ''')
        finding = report["findings"][0]
        self.assertEqual(finding["kind"], "mutable_default_mutated")
        self.assertEqual(finding["priority"], "high")

    def test_required_dict_read_before_item_mutation_is_qualified(self):
        report = self.report_for('''
            def f(values={}):
                category = values["category"]
                values["label"] = category.upper()
                return values
        ''')
        finding = report["findings"][0]
        self.assertEqual(finding["kind"], "mutable_default_qualified")
        self.assertEqual(finding["priority"], "low")
        self.assertEqual(finding["detail"], "empty_default_fails_before_mutation")

    def test_conditional_rebind_does_not_hide_shared_default_mutation(self):
        report = self.report_for('''
            def f(flag, items=[]):
                if flag:
                    items = []
                items.append(1)
        ''')
        finding = report["findings"][0]
        self.assertEqual(finding["kind"], "mutable_default_mutated")
        self.assertEqual(finding["priority"], "high")

    def test_directly_returned_mutable_default_is_visible(self):
        report = self.report_for('''
            def f(items=[]):
                return items
        ''')
        self.assertEqual(report["findings"][0]["kind"], "mutable_default_escape")

    def test_validation_only_dialog_is_not_a_save_asymmetry(self):
        report = self.report_for('''
            class Dialog:
                def OnBoutonOk(self):
                    if self.ctrl_date.Validation() is False:
                        return False
                    self.EndModal(1)

                def GetDate(self):
                    return self.ctrl_date.GetDate()
        ''')
        findings = [item for item in report["findings"] if item["kind"] == "validation_without_save"]
        self.assertEqual(findings, [])

    def test_unrelated_saved_component_does_not_create_false_asymmetry(self):
        report = self.report_for('''
            class Dialog:
                def OnBoutonOk(self):
                    if self.ctrl_date.Validation() is False:
                        return False
                    value = self.ctrl_date.GetDate()
                    self.ctrl_repas.Sauvegarde()
                    return value
        ''')
        findings = [item for item in report["findings"] if item["kind"] == "validation_save_mixed_api"]
        self.assertEqual(findings, [])

    def test_mixed_validation_save_contract_is_informational(self):
        report = self.report_for('''
            class Dialog:
                def OnBoutonOk(self):
                    self.ctrl_a.Validation()
                    self.ctrl_b.Validation()
                    self.ctrl_a.Sauvegarde()
        ''')
        findings = [item for item in report["findings"] if item["kind"] == "validation_save_mixed_api"]
        self.assertEqual([item["control"] for item in findings], ["ctrl_b"])
        self.assertEqual(findings[0]["priority"], "low")

    def test_modal_without_destroy_is_detected(self):
        report = self.report_for('''
            class Dialog:
                def OnBoutonOk(self):
                    dlg = MessageDialog(self)
                    dlg.ShowModal()
        ''')
        self.assertTrue(any(item["kind"] == "modal_without_destroy" for item in report["findings"]))

    def test_repository_has_no_high_priority_shared_mutable_default(self):
        report = self.repository_report()
        findings = [
            item
            for item in report["findings"]
            if item["kind"] == "mutable_default_mutated" and item["priority"] == "high"
        ]
        self.assertEqual(
            findings,
            [],
            "Valeurs mutables réellement partagées à qualifier:\n"
            + "\n".join(
                "{file}:{line} {function}({parameter}) — {detail}".format(**item)
                for item in findings
            ),
        )

    def test_repository_has_no_high_priority_semantic_trap(self):
        report = self.repository_report()
        findings = [item for item in report["findings"] if item["priority"] == "high"]
        self.assertEqual(
            findings,
            [],
            "Pièges sémantiques à priorité haute à qualifier:\n"
            + "\n".join(
                "{kind} {file}:{line} {function}".format(**item)
                for item in findings
            ),
        )

    def test_repository_inventory_is_exported(self):
        report = self.repository_report()
        output = Path("tmp/semantic-traps-audit.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"SEMANTIC_TRAPS={report['count']} {report['kinds']} {report['priorities']}")
        self.assertIn("findings", report)
        self.assertIn("kinds", report)
        self.assertIn("priorities", report)


if __name__ == "__main__":
    unittest.main()
