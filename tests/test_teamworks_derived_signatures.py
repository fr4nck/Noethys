# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import unittest
from pathlib import Path

from scripts import audit_teamworks_signatures


ROOT = Path(__file__).resolve().parents[1]


class TeamworksDerivedSignatureTests(unittest.TestCase):
    def scan(self, source):
        return audit_teamworks_signatures.scan_tree(ast.parse(source), "fixture.py")

    def test_class_comprehension_reading_class_local_is_detected(self):
        findings = self.scan(
            "class Dialog:\n"
            "    LABELS = {'dark': 'Sombre'}\n"
            "    MODES = ['dark']\n"
            "    APPEARANCES = [(key, LABELS[key]) for key in MODES]\n"
        )
        self.assertEqual(
            [(item["kind"], item.get("name")) for item in findings],
            [("class_comprehension_scope", "LABELS")],
        )

    def test_first_comprehension_iterable_may_read_class_local(self):
        findings = self.scan(
            "class Dialog:\n"
            "    MODES = ['dark']\n"
            "    APPEARANCES = [key.upper() for key in MODES]\n"
        )
        self.assertEqual(findings, [])

    def test_comprehension_target_shadows_same_named_class_attribute(self):
        findings = self.scan(
            "class Example:\n"
            "    value = 10\n"
            "    values = [value for value in range(3)]\n"
        )
        self.assertEqual(findings, [])

    def test_previous_generator_target_is_local_in_next_iterable(self):
        findings = self.scan(
            "class Example:\n"
            "    item = 'class value'\n"
            "    pairs = [(item, child) for item in range(3) for child in (item,)]\n"
        )
        self.assertEqual(findings, [])

    def test_accessors_compared_without_call_are_detected(self):
        findings = self.scan(
            "def check(ctrl):\n"
            "    if ctrl.GetValue == 'x':\n"
            "        return True\n"
            "    if not ctrl.GetSelection:\n"
            "        return False\n"
        )
        self.assertEqual(
            [item["kind"] for item in findings],
            ["accessor_not_called", "accessor_not_called"],
        )

    def test_called_accessors_are_not_reported(self):
        findings = self.scan(
            "def check(ctrl):\n"
            "    if ctrl.GetValue() == 'x':\n"
            "        return ctrl.GetSelection() >= 0\n"
        )
        self.assertEqual(findings, [])

    def test_thread_is_alive_legacy_spelling_is_detected(self):
        findings = self.scan(
            "def stop(thread):\n"
            "    if thread.isAlive():\n"
            "        return False\n"
        )
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["kind"], "thread_isAlive")

    def test_current_noethys_tree_has_no_high_confidence_teamworks_signature(self):
        report = audit_teamworks_signatures.build_report(ROOT / "noethys")
        self.assertTrue(report["coverage"]["complete"], report["coverage"])
        self.assertEqual(
            report["priorities"].get("high", 0),
            0,
            "Signatures Teamworks à qualifier dans Noethys:\n"
            + "\n".join(
                "{kind} {file}:{line} — {detail}".format(**item)
                for item in report["findings"]
                if item["priority"] == "high"
            ),
        )


if __name__ == "__main__":
    unittest.main()
