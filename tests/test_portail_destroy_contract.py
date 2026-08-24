#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import unittest

from scripts import audit_wx_lifecycle as audit


class PortailDestroyContractTests(unittest.TestCase):
    def test_saisie_portail_demande_has_no_use_after_destroy(self):
        path = audit.NOETHYS / "Dlg" / "DLG_Saisie_portail_demande.py"
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)
        findings = audit._scan_use_after_destroy(path, tree, source.splitlines())
        risky = [item for item in findings if item["kind"] == "use_after_destroy"]
        self.assertEqual(risky, [])


if __name__ == "__main__":
    unittest.main()
