# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_sql_strict.py"
spec = importlib.util.spec_from_file_location("audit_sql_strict", str(SCRIPT))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class StrictSQLAuditTests(unittest.TestCase):
    def candidate(self, sql):
        return audit.SQLCandidate(Path("fixture.py"), 1, sql)

    def test_simple_aggregate_key_is_safe(self):
        item = self.candidate(
            "SELECT IDgroupe, COUNT(IDinscription) FROM inscriptions GROUP BY IDgroupe"
        )
        self.assertEqual(item.classification, "SAFE")

    def test_aggregate_with_ungrouped_column_requires_review(self):
        item = self.candidate(
            "SELECT IDgroupe, nom, COUNT(IDinscription) FROM inscriptions GROUP BY IDgroupe"
        )
        self.assertEqual(item.classification, "REVIEW")
        self.assertIn("nom", item.ungrouped_items)

    def test_dedupe_is_only_classified_when_all_selected_columns_are_grouped(self):
        safe = self.candidate(
            "SELECT IDfamille, IDindividu FROM inscriptions GROUP BY IDfamille, IDindividu"
        )
        unsafe = self.candidate(
            "SELECT IDfamille, date_inscription FROM inscriptions GROUP BY IDfamille"
        )
        self.assertEqual(safe.classification, "DEDUPE")
        self.assertEqual(unsafe.classification, "REVIEW")

    def test_nested_safe_group_by_does_not_make_outer_query_a_false_positive(self):
        item = self.candidate(
            """
            SELECT reglements.IDreglement, ventilation_totaux.total_ventilation
            FROM reglements
            LEFT JOIN (
                SELECT IDreglement, SUM(montant) AS total_ventilation
                FROM ventilation
                GROUP BY IDreglement
            ) ventilation_totaux
              ON ventilation_totaux.IDreglement = reglements.IDreglement
            """
        )
        self.assertEqual(item.classification, "SAFE")

    def test_nested_risky_group_by_remains_review(self):
        item = self.candidate(
            """
            SELECT x.IDx
            FROM x
            LEFT JOIN (
                SELECT IDx, label, SUM(montant)
                FROM y
                GROUP BY IDx
            ) ytot ON ytot.IDx=x.IDx
            """
        )
        self.assertEqual(item.classification, "REVIEW")


if __name__ == "__main__":
    unittest.main()
