#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import unittest
from pathlib import Path


SOURCE = Path(__file__).resolve().parents[1] / "noethys" / "Utils" / "UTILS_Fichiers.py"


class FileMigrationHardeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SOURCE.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.text)
        cls.function = next(
            node for node in cls.tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "DeplaceFichiers"
        )
        cls.source = ast.get_source_segment(cls.text, cls.function) or ""

    def test_legacy_database_archive_failure_is_not_silenced(self):
        self.assertIn("os.replace(source, archive)", self.source)
        self.assertNotIn("os.rename(Chemins.GetMainPath", self.source)

    def test_xlang_move_uses_resolved_main_path(self):
        self.assertIn('source = Chemins.GetMainPath(u"Lang/%s" % nomFichier)', self.source)
        self.assertIn("shutil.move(source, GetRepLang(nomFichier))", self.source)


if __name__ == "__main__":
    unittest.main()
