# -*- coding: utf-8 -*-
"""Contrats du texte de bandeau dans le bundle PyInstaller plat."""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BANDEAU = ROOT / "noethys" / "Ctrl" / "CTRL_Bandeau.py"
SPEC = ROOT / "packaging" / "noethys.spec"


class BandeauHtmlContractTests(unittest.TestCase):
    def test_bandeau_does_not_import_top_level_html(self):
        source = BANDEAU.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)

        self.assertNotIn("html", imports)
        self.assertIn("def _decoder_entites_html", source)
        self.assertIn("chr(int(code[2:], 16))", source)
        self.assertIn("chr(int(code[1:], 10))", source)

    def test_packaging_does_not_try_to_mask_html_name_collision(self):
        source = SPEC.read_text(encoding="utf-8")
        self.assertNotIn('"html",', source)
        self.assertNotIn('"html.entities"', source)
        self.assertNotIn('"html.parser"', source)


if __name__ == "__main__":
    unittest.main()
