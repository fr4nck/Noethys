#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnostic temporaire du lot 23 branch_assignment_gap.

Ce test est volontairement supprimé du diff final : il permet d'exécuter
l'inventaire exhaustif dans l'environnement GitHub Actions déjà utilisé par la
CI, puis d'en lire la sortie exacte dans les logs.
"""

import unittest

from scripts import audit_branch_assignment_gaps


class BranchAssignmentGapBatch23InventoryTest(unittest.TestCase):
    def test_inventory_current_master(self):
        self.assertEqual(audit_branch_assignment_gaps.main([]), 0)


if __name__ == "__main__":
    unittest.main()
