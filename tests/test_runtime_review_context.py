#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import unittest
from pathlib import Path

from scripts import export_runtime_review_context as review


class RuntimeReviewContextTests(unittest.TestCase):
    def test_priority_runtime_context_is_exported_even_when_review_queue_is_empty(self):
        report = review.build_report()
        output = Path("tmp/runtime-review-audit.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

        self.assertIn("count", report)
        self.assertIn("reviews", report)
        self.assertEqual(report["count"], len(report["reviews"]))
        self.assertGreaterEqual(report["count"], 0)


if __name__ == "__main__":
    unittest.main()
