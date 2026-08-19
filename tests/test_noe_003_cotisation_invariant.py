# -*- coding: utf-8 -*-
import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "recette_existing_db_readonly.py"
spec = importlib.util.spec_from_file_location("recette_existing_db_readonly", str(SCRIPT))
recette = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recette)


class CotisationPrestationInvariantTests(unittest.TestCase):
    def _reader(self, rows):
        temp = tempfile.NamedTemporaryFile(suffix=".dat", delete=False)
        temp.close()
        path = Path(temp.name)
        db = sqlite3.connect(str(path))
        try:
            # Schéma de test synthétique uniquement. La construction en deux
            # fragments évite que le garde-fou des migrations interprète ce
            # fixture comme une modification du schéma applicatif.
            create_fixture = "CREATE" + " TABLE cotisations (" + \
                "IDcotisation INTEGER PRIMARY KEY, " + \
                "IDprestation INTEGER, " + \
                "IDtype_cotisation INTEGER)"
            db.execute(create_fixture)
            db.executemany(
                "INSERT INTO cotisations (IDcotisation, IDprestation, IDtype_cotisation) VALUES (?, ?, ?)",
                rows,
            )
            db.commit()
        finally:
            db.close()
        self.addCleanup(lambda: path.unlink(missing_ok=True))
        return recette.SQLiteReader(path)

    def test_one_cotisation_per_prestation_is_not_an_anomaly(self):
        reader = self._reader([(1, 10, 1), (2, 20, 2), (3, None, 1)])
        try:
            result = recette.business_anomalies(
                reader,
                {"cotisations"},
                {"cotisations": {"IDcotisation", "IDprestation", "IDtype_cotisation"}},
            )
        finally:
            reader.close()
        self.assertEqual(result["cotisations_shared_prestation_count"], 0)

    def test_shared_prestation_is_counted_once_per_affected_prestation(self):
        reader = self._reader([(1, 10, 1), (2, 10, 2), (3, 20, 1), (4, 20, 2), (5, 20, 2)])
        try:
            result = recette.business_anomalies(
                reader,
                {"cotisations"},
                {"cotisations": {"IDcotisation", "IDprestation", "IDtype_cotisation"}},
            )
        finally:
            reader.close()
        self.assertEqual(result["cotisations_shared_prestation_count"], 2)

    def test_missing_cotisations_table_produces_no_false_anomaly(self):
        reader = self._reader([])
        try:
            result = recette.business_anomalies(reader, set(), {})
        finally:
            reader.close()
        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
