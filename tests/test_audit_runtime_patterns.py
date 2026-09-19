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


class InvalidEscapeAuditTests(unittest.TestCase):
    """INVALID_ESCAPE doit refléter la sémantique réelle du compilateur
    Python (ast.parse), pas une regex ligne par ligne aveugle aux chaînes
    triple-guillemets multi-lignes — voir le faux négatif historique sur
    noethys/Utils/UTILS_TL_drawing_default.py."""

    def _scan_escape(self, content):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "sample.py"
            path.write_text(content, encoding="utf-8")
            return AUDIT.check_invalid_escape(path, root)

    def test_multiline_triple_quote_docstring_with_real_invalid_escape_is_detected(self):
        # Le backslash fautif est sur une ligne de CORPS du docstring, sans
        # guillemet adjacent sur cette même ligne : une regex par ligne ne
        # peut pas le voir. C'est exactement le cas manqué en production.
        content = (
            "def f():\n"
            '    """\n'
            "    chemin windows \\d exemple\n"
            '    """\n'
            "    return 1\n"
        )
        issues = self._scan_escape(content)
        self.assertEqual(1, len(issues))
        self.assertIn("invalid escape sequence", issues[0]["snippet"])

    def test_same_content_as_raw_string_is_never_flagged(self):
        content = (
            "def f():\n"
            '    x = r"""\n'
            "    chemin windows \\d exemple\n"
            '    """\n'
            "    return x\n"
        )
        self.assertEqual([], self._scan_escape(content))

    def test_correctly_escaped_backslash_is_not_flagged(self):
        # "\\\\" dans la source du test = un seul backslash écrit dans le
        # fichier généré = échappement \\ valide (backslash littéral).
        content = 'value = "C:\\\\Users\\\\demo"\n'
        self.assertEqual([], self._scan_escape(content))

    def test_plain_string_without_escape_is_not_flagged(self):
        self.assertEqual([], self._scan_escape('value = "hello world"\n'))

    def test_single_line_string_invalid_escape_is_still_detected(self):
        # Non-régression : le cas simple, déjà couvert par l'ancienne regex,
        # doit continuer à fonctionner avec le détecteur basé sur ast.parse.
        issues = self._scan_escape('value = "chemin \\d"\n')
        self.assertEqual(1, len(issues))

    def test_third_party_directories_stay_excluded_via_run_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            third_party = root / "Outils"
            third_party.mkdir()
            (third_party / "legacy.py").write_text(
                "def f():\n"
                '    """\n'
                "    bad \\d escape\n"
                '    """\n',
                encoding="utf-8",
            )
            package = root / "Pkg"
            package.mkdir()
            (package / "clean.py").write_text("value = 1\n", encoding="utf-8")

            report = AUDIT.run_audit(root=root)
            self.assertEqual([], report["INVALID_ESCAPE"])

    def test_run_audit_still_exposes_invalid_escape_as_a_flat_list(self):
        # Contrat conservé pour les consommateurs en aval
        # (audit_runtime_hardening.py, tests/test_runtime_zero_debt.py).
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "clean.py").write_text("value = 1\n", encoding="utf-8")
            (root / "broken.py").write_text(
                'value = "chemin \\d"\n', encoding="utf-8"
            )
            report = AUDIT.run_audit(root=root)
            self.assertIn("INVALID_ESCAPE", report)
            self.assertEqual(1, len(report["INVALID_ESCAPE"]))
            self.assertEqual("broken.py", report["INVALID_ESCAPE"][0]["file"])


if __name__ == "__main__":
    unittest.main()
