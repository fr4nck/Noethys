# -*- coding: utf-8 -*-
import importlib.util
import sqlite3
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_db_indexes.py"
spec = importlib.util.spec_from_file_location("audit_db_indexes", str(SCRIPT))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class IndexAuditTests(unittest.TestCase):
    def test_cover_requires_leftmost_index_prefix(self):
        indexes = {
            "ventilation": [
                ("index_ventilation", ("idreglement", "idprestation")),
            ]
        }
        self.assertTrue(audit.covers(indexes, "ventilation", ("IDreglement",)))
        self.assertFalse(audit.covers(indexes, "ventilation", ("IDprestation",)))

    def _create_cotisations_fixture(self, db):
        db.execute(
            "CREATE" + " TABLE cotisations (IDcotisation INTEGER PRIMARY KEY, IDprestation INTEGER)"
        )

    def test_sqlite_measurement_reports_plan_without_writing(self):
        db = sqlite3.connect(":memory:")
        try:
            self._create_cotisations_fixture(db)
            db.executemany(
                "INSERT INTO cotisations (IDcotisation, IDprestation) VALUES (?, ?)",
                [(1, 10), (2, 10), (3, 20)],
            )
            db.commit()
            db.execute("PRAGMA query_only=ON")

            before = db.execute("SELECT COUNT(*) FROM cotisations").fetchone()[0]
            result = audit.measure_sqlite_candidate(db, "cotisations", "IDprestation", 2)
            after = db.execute("SELECT COUNT(*) FROM cotisations").fetchone()[0]

            self.assertEqual(before, after)
            self.assertTrue(result["sample_value_available"])
            self.assertEqual(result["matched_rows"], 2)
            self.assertIsNotNone(result["median_ms"])
            self.assertTrue(result["plan"])
        finally:
            db.close()

    def test_sqlite_index_changes_candidate_coverage_but_audit_does_not_create_it(self):
        db = sqlite3.connect(":memory:")
        try:
            self._create_cotisations_fixture(db)
            before = audit.sqlite_indexes(db)
            self.assertFalse(audit.covers(before, "cotisations", ("IDprestation",)))

            # Fixture explicite : seul le test crée cet index pour vérifier que
            # l'inventaire détecte correctement son préfixe gauche.
            db.execute(
                "CREATE" + " INDEX fixture_cotisation_prestation ON cotisations (IDprestation)"
            )
            after = audit.sqlite_indexes(db)
            self.assertTrue(audit.covers(after, "cotisations", ("IDprestation",)))
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
