#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import unittest
from pathlib import Path

from scripts import audit_branch_assignment_gaps


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "noethys"
SOURCE_PATH = SOURCE_ROOT / "Dlg" / "DLG_Nbre_inscrits.py"

COULEUR_GAUGE_FOND = "fond"
COULEUR_DISPONIBLE = "disponible"
COULEUR_ALERTE = "alerte"
COULEUR_COMPLET = "complet"
COULEUR_TRAIT = "trait"


class FakeWx:
    TRANSPARENT_PEN = "transparent"
    BITMAP_TYPE_ANY = "any"

    @staticmethod
    def Brush(value):
        return ("brush", value)

    @staticmethod
    def Pen(value, width):
        return ("pen", value, width)

    @staticmethod
    def Bitmap(path, bitmap_type):
        return ("bitmap", path, bitmap_type)


class FakeChemins:
    @staticmethod
    def GetStaticPath(path):
        return path


class FakeDC:
    def __init__(self):
        self.brushes = []
        self.pens = []
        self.rectangles = []
        self.bitmaps = []

    def SetBrush(self, brush):
        self.brushes.append(brush)

    def SetPen(self, pen):
        self.pens.append(pen)

    def DrawRectangle(self, *args):
        self.rectangles.append(args)

    def DrawBitmap(self, *args):
        self.bitmaps.append(args)


class FakeGauge:
    hauteurGauge = 10
    seuil_alerte = 3

    def __init__(self, nbre_inscrits, nbre_inscrits_max):
        self.nbre_inscrits = nbre_inscrits
        self.nbre_inscrits_max = nbre_inscrits_max


def load_draw_gauge():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    methods = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "DrawGauge"
    ]
    if len(methods) != 1:
        raise AssertionError(methods)
    module = ast.Module(body=[methods[0]], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {
        "wx": FakeWx,
        "Chemins": FakeChemins,
        "COULEUR_GAUGE_FOND": COULEUR_GAUGE_FOND,
        "COULEUR_DISPONIBLE": COULEUR_DISPONIBLE,
        "COULEUR_ALERTE": COULEUR_ALERTE,
        "COULEUR_COMPLET": COULEUR_COMPLET,
        "COULEUR_TRAIT": COULEUR_TRAIT,
    }
    exec(compile(module, str(SOURCE_PATH), "exec"), namespace)
    return namespace["DrawGauge"]


def rendered_color(nbre_inscrits, nbre_inscrits_max):
    draw_gauge = load_draw_gauge()
    dc = FakeDC()
    draw_gauge(FakeGauge(nbre_inscrits, nbre_inscrits_max), dc, 0, 0, 100, 20)
    return dc.brushes[-1][1], dc


class NbreInscritsGaugeColorContractTests(unittest.TestCase):
    def test_no_capacity_uses_available_color(self):
        color, dc = rendered_color(4, 0)
        self.assertEqual(color, COULEUR_DISPONIBLE)
        self.assertEqual(dc.bitmaps, [])

    def test_available_state_above_alert_threshold(self):
        color, dc = rendered_color(5, 10)
        self.assertEqual(color, COULEUR_DISPONIBLE)
        self.assertEqual(dc.bitmaps, [])

    def test_alert_state_at_threshold(self):
        color, dc = rendered_color(7, 10)
        self.assertEqual(color, COULEUR_ALERTE)
        self.assertEqual(len(dc.bitmaps), 1)

    def test_alert_state_with_one_place_left(self):
        color, dc = rendered_color(9, 10)
        self.assertEqual(color, COULEUR_ALERTE)
        self.assertEqual(len(dc.bitmaps), 1)

    def test_full_state_at_capcity(self):
        color, dc = rendered_color(10, 10)
        self.assertEqual(color, COULEUR_COMPLET)
        self.assertEqual(dc.bitmaps, [])

    def test_full_state_over_capacity(self):
        color, dc = rendered_color(12, 10)
        self.assertEqual(color, COULEUR_COMPLET)
        self.assertEqual(dc.bitmaps, [])

    def test_draw_gauge_color_branch_gap_is_gone(self):
        findings = audit_branch_assignment_gaps.scan_file(SOURCE_PATH, SOURCE_ROOT)
        targeted = [
            item for item in findings
            if item.get("function") == "DrawGauge"
            and item.get("name") == "couleur"
        ]
        self.assertEqual(targeted, [], targeted)


if __name__ == "__main__":
    unittest.main()
