# -*- coding: utf-8 -*-
"""Régressions de l'audit runtime sans dépendance à Noethys ni wxPython."""

import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "scripts" / "audit_runtime_patterns.py"
SPEC = importlib.util.spec_from_file_location("audit_runtime_patterns", AUDIT_PATH)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class RuntimePy2AuditTests(unittest.TestCase):
    def _scan(self, content):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "sample.py"
            path.write_text(content, encoding="utf-8")
            return AUDIT.check_text_patterns(path, root)["PY2_BUILTINS"]

    def test_six_moves_range_as_xrange_is_not_a_py2_builtin(self):
        issues = self._scan(
            "from six.moves import range as xrange\n"
            "for index in xrange(3):\n"
            "    pass\n"
        )
        self.assertEqual([], issues)

    def test_six_moves_xrange_is_not_a_py2_builtin(self):
        issues = self._scan(
            "from six.moves import xrange\n"
            "values = list(xrange(3))\n"
        )
        self.assertEqual([], issues)

    def test_unguarded_xrange_still_fails(self):
        issues = self._scan("values = list(xrange(3))\n")
        self.assertEqual(1, len(issues))
        self.assertEqual("xrange", issues[0]["builtin"])

    def test_raw_input_inside_six_py2_branch_is_ignored(self):
        issues = self._scan(
            "import six\n"
            "if six.PY2:\n"
            "    value = raw_input('> ')\n"
        )
        self.assertEqual([], issues)

    def test_unguarded_raw_input_still_fails(self):
        issues = self._scan("value = raw_input('> ')\n")
        self.assertEqual(1, len(issues))
        self.assertEqual("raw_input", issues[0]["builtin"])

    def test_basestring_literal_is_not_a_builtin_use(self):
        self.assertEqual([], self._scan("kind = 'basestring'\n"))


if __name__ == "__main__":
    unittest.main()
