#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import unittest

from scripts import qualify_branch_assignment_gaps


class FinalBranchGapTriageDiagnostic(unittest.TestCase):
    def test_print_remaining_review_queue(self):
        report = qualify_branch_assignment_gaps.build_report()
        reviews = [
            {
                "file": item["file"],
                "line": item["line"],
                "function": item["function"],
                "name": item["name"],
                "detail": item["detail"],
            }
            for item in report["findings"]
            if item["classification"] == "review"
        ]
        print("FINAL_BRANCH_GAP_TRIAGE=" + json.dumps(reviews, ensure_ascii=False, separators=(",", ":")))
        self.assertTrue(report["count"] >= len(reviews))


if __name__ == "__main__":
    unittest.main()
