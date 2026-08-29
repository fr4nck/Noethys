#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import types
import unittest
from pathlib import Path

from scripts import audit_branch_assignment_gaps


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "noethys"
SOURCE_PATH = SOURCE_ROOT / "Dlg" / "DLG_Dates_forfait_date.py"


class FakeImage:
    def __init__(self, largeur, hauteur, clear):
        self.largeur = largeur
        self.hauteur = hauteur
        self.clear = clear
        self.rgb = None

    def SetRGB(self, rect, r, v, b):
        self.rgb = (rect, r, v, b)

    def ConvertToBitmap(self):
        return self


def load_creation_image():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    wanted = {"hex_to_rgb", "CreationImage"}
    functions = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in wanted
    ]
    module = ast.Module(body=functions, type_ignores=[])
    ast.fix_missing_locations(module)
    fake_wx = types.SimpleNamespace(
        PlatformInfo=("phoenix",),
        Image=FakeImage,
    )
    namespace = {"wx": fake_wx}
    exec(compile(module, str(SOURCE_PATH), "exec"), namespace)
    return namespace["CreationImage"]


class DatesForfaitColorContractTests(unittest.TestCase):
    def test_historical_hex_and_rgb_inputs_are_preserved(self):
        creation_image = load_creation_image()
        self.assertEqual(
            creation_image(8, 6, "#123456").rgb,
            ((0, 0, 8, 6), 0x12, 0x34, 0x56),
        )
        self.assertEqual(
            creation_image(5, 4, (1, 2, 3)).rgb,
            ((0, 0, 5, 4), 1, 2, 3),
        )

    def test_default_colour_is_white(self):
        image = load_creation_image()(3, 2)
        self.assertEqual(image.rgb, ((0, 0, 3, 2), 255, 255, 255))

    def test_unsupported_colour_is_rejected_explicitly(self):
        with self.assertRaisesRegex(ValueError, "chaîne HEXA ou un tuple RGB"):
            load_creation_image()(3, 2, [1, 2, 3])
        with self.assertRaisesRegex(ValueError, "chaîne HEXA ou un tuple RGB"):
            load_creation_image()(3, 2, (1, 2))

    def test_creation_image_branch_assignment_gaps_are_gone(self):
        findings = audit_branch_assignment_gaps.scan_file(SOURCE_PATH, SOURCE_ROOT)
        targeted = [
            item for item in findings
            if item.get("function") == "CreationImage"
            and item.get("name") in {"r", "v", "b"}
        ]
        self.assertEqual(targeted, [], targeted)


if __name__ == "__main__":
    unittest.main()
