#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import types
import unittest
from pathlib import Path

from scripts import audit_branch_assignment_gaps


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "noethys"
SOURCE_PATH = SOURCE_ROOT / "Utils" / "UTILS_Images.py"


class FakeColour:
    def __init__(self, r, v, b, alpha=255):
        self.value = (r, v, b, alpha)

    def Get(self):
        return self.value


class FakeImage:
    def __init__(self, largeur, hauteur, clear=True):
        self.largeur = largeur
        self.hauteur = hauteur
        self.clear = clear
        self.rgb_calls = []

    def SetRGB(self, rect, r, v, b):
        self.rgb_calls.append((rect, r, v, b))

    def ConvertToBitmap(self):
        return self


def load_color_helpers():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    wanted = {"hex_to_rgb", "ConvertToRVB", "CreationCarreCouleur"}
    functions = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in wanted
    ]
    module = ast.Module(body=functions, type_ignores=[])
    ast.fix_missing_locations(module)
    fake_wx = types.SimpleNamespace(
        PlatformInfo=("phoenix",),
        Colour=FakeColour,
        Image=FakeImage,
    )
    namespace = {"wx": fake_wx}
    exec(compile(module, str(SOURCE_PATH), "exec"), namespace)
    return namespace


class UtilsImagesColorContractTests(unittest.TestCase):
    def test_historical_hex_and_tuple_inputs_are_preserved(self):
        convert = load_color_helpers()["ConvertToRVB"]
        self.assertEqual(convert("#123456"), (0x12, 0x34, 0x56))
        self.assertEqual(convert((1, 2, 3)), (1, 2, 3))
        self.assertEqual(convert((4, 5, 6, 7)), (4, 5, 6))

    def test_wx_colour_keeps_first_three_components(self):
        convert = load_color_helpers()["ConvertToRVB"]
        self.assertEqual(convert(FakeColour(8, 9, 10, 11)), (8, 9, 10))

    def test_default_colour_is_white_in_converter_and_square(self):
        helpers = load_color_helpers()
        self.assertEqual(helpers["ConvertToRVB"](), (255, 255, 255))
        image = helpers["CreationCarreCouleur"](5, 4)
        self.assertEqual(
            image.rgb_calls,
            [
                ((0, 0, 5, 4), 255, 255, 255),
                ((1, 1, 3, 2), 255, 255, 255),
            ],
        )

    def test_invalid_colour_is_rejected_explicitly(self):
        convert = load_color_helpers()["ConvertToRVB"]
        with self.assertRaisesRegex(ValueError, "au moins trois composantes"):
            convert((1, 2))
        with self.assertRaisesRegex(ValueError, "chaîne HEXA, un tuple RGB ou un wx.Colour"):
            convert([1, 2, 3])

    def test_convert_to_rvb_branch_assignment_gaps_are_gone(self):
        findings = audit_branch_assignment_gaps.scan_file(SOURCE_PATH, SOURCE_ROOT)
        targeted = [
            item for item in findings
            if item.get("function") == "ConvertToRVB"
            and item.get("name") in {"r", "v", "b"}
        ]
        self.assertEqual(targeted, [], targeted)


if __name__ == "__main__":
    unittest.main()
