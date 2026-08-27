# -*- coding: utf-8 -*-
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts import audit_fragile_date_parsing
from scripts.audit_source_coverage import SourceAuditSession


ROOT = Path(__file__).resolve().parents[1]
HARDENED_AUDITS = (
    "audit_fragile_date_parsing.py",
    "audit_wx_numeric_arguments.py",
    "audit_bytes_text_boundaries.py",
    "audit_csv_boundaries.py",
    "audit_utf8_boundaries.py",
    "audit_dependency_usage.py",
)


class SourceCoverageTests(unittest.TestCase):
    def test_declared_historical_encoding_is_read_and_parsed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "historique_latin1.py"
            path.write_bytes(
                b"# -*- coding: latin-1 -*-\n"
                b"libelle = 'caf\xe9'\n"
                b"date_naissance = '01022020'\n"
                b"jour = int(date_naissance[0:2])\n"
            )

            session = SourceAuditSession([path])
            loaded = session.parse(path)

            self.assertIsNotNone(loaded)
            self.assertTrue(session.coverage.complete)
            self.assertEqual(session.coverage.found, 1)
            self.assertEqual(session.coverage.read, 1)
            self.assertEqual(session.coverage.parsed, 1)
            _source, tree = loaded
            self.assertEqual(len(audit_fragile_date_parsing.scan_tree(tree)), 1)

    def test_syntax_error_is_not_silently_counted_as_zero_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.py"
            path.write_text("def broken(:\n    pass\n", encoding="utf-8")

            session = SourceAuditSession([path])
            loaded = session.parse(path)

            self.assertIsNone(loaded)
            self.assertFalse(session.coverage.complete)
            self.assertEqual(session.coverage.found, 1)
            self.assertEqual(session.coverage.read, 1)
            self.assertEqual(session.coverage.parsed, 0)
            self.assertEqual(session.coverage.failures[0].stage, "parsing")

    def test_undeclared_non_utf8_source_is_an_explicit_read_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad_encoding.py"
            path.write_bytes(b"libelle = 'caf\xe9'\n")

            session = SourceAuditSession([path])
            loaded = session.parse(path)

            self.assertIsNone(loaded)
            self.assertFalse(session.coverage.complete)
            self.assertEqual(session.coverage.found, 1)
            self.assertEqual(session.coverage.read, 0)
            self.assertEqual(session.coverage.parsed, 0)
            self.assertEqual(session.coverage.failures[0].stage, "lecture")

    def test_compatibility_inventory_audits_use_the_shared_coverage_contract(self):
        scripts = ROOT / "scripts"
        for filename in HARDENED_AUDITS:
            with self.subTest(filename=filename):
                source = (scripts / filename).read_text(encoding="utf-8")
                self.assertIn("SourceAuditSession", source)
                self.assertNotIn('errors="replace"', source)
                self.assertNotIn('errors="ignore"', source)
                self.assertNotIn("except (OSError, SyntaxError):\n        return []", source)


if __name__ == "__main__":
    unittest.main()
