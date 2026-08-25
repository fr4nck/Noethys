#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from scripts import audit_wx_lifecycle as audit


class WxLifecycleZeroDebtTests(unittest.TestCase):
    def test_no_high_risk_wx_lifecycle_debt_returns(self):
        findings = audit.scan()
        strong_kinds = {
            "use_after_destroy",
            "constructor_parent_callback",
            "constructor_callback_before_dependency",
        }
        risky = [item for item in findings if item["kind"] in strong_kinds]
        self.assertEqual(risky, [], msg=f"Risque wx fort réintroduit : {risky}")


if __name__ == "__main__":
    unittest.main()
