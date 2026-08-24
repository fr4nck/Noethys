#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from scripts import audit_wx_lifecycle as audit


class WxLifecycleZeroDebtTests(unittest.TestCase):
    def test_no_use_after_destroy_remains_in_noethys_ui(self):
        risky = [
            item for item in audit.scan()
            if item["kind"] == "use_after_destroy"
        ]
        self.assertEqual(risky, [])


if __name__ == "__main__":
    unittest.main()
