#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import types
import unittest
from pathlib import Path


SOURCE = Path("noethys/Dlg/DLG_Noedoc.py")


class Vector:
    """Petit vecteur suffisant pour exercer DeplacerObjet sans dépendance numpy."""

    def __init__(self, values):
        self.values = list(values)

    def __add__(self, other):
        return Vector(a + b for a, b in zip(self.values, other.values))

    def __sub__(self, other):
        return Vector(a - b for a, b in zip(self.values, other.values))

    def __iter__(self):
        return iter(self.values)

    def __getitem__(self, index):
        return self.values[index]

    def all(self):
        """Expose le marqueur historique utilisé pour reconnaître un ndarray."""
        return all(self.values)


class FakeNumpy:
    @staticmethod
    def array(values):
        return Vector(values)


def load_deplacer_objet():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    fonction = next(
        node for classe in ast.walk(tree)
        if isinstance(classe, ast.ClassDef)
        for node in classe.body
        if isinstance(node, ast.FunctionDef) and node.name == "DeplacerObjet"
    )
    module = ast.Module(body=[fonction], type_ignores=[])
    ast.fix_missing_locations(module)

    namespace = {"numpy": FakeNumpy}
    exec(compile(module, str(SOURCE), "exec"), namespace)
    return namespace["DeplacerObjet"]


class FakeObjet:
    def __init__(self, xy):
        self._xy = xy
        self.verrouillageX = False
        self.verrouillageY = False
        self.categorie = "texte"

    def GetXY(self):
        return self._xy

    def Move(self, delta):
        self._xy = self._xy + delta

    def CalcBoundingBox(self):
        pass


class FakeCtrlPosition:
    def SetX(self, x):
        pass

    def SetY(self, y):
        pass


class FakeCtrlProprietes:
    def __init__(self):
        self.ctrl_position = FakeCtrlPosition()

    def SetObjet(self, objet):
        pass


class FakeCanvas:
    def Draw(self, refresh):
        pass


class FakeSelf:
    def __init__(self):
        self.dictSelection = None
        self.ctrl_proprietes = FakeCtrlProprietes()
        self.canvas = FakeCanvas()


class NoedocDeplacerObjetContractTests(unittest.TestCase):
    def setUp(self):
        self.fonction = load_deplacer_objet()

    def test_deplacement_avec_sens_reconnu(self):
        objet = FakeObjet(Vector([0, 0]))
        self.fonction(FakeSelf(), objet, sens="haut")
        self.assertEqual(list(objet.GetXY()), [0, 1])

    def test_deplacement_avec_nouvelle_position(self):
        objet = FakeObjet(Vector([0, 0]))
        self.fonction(FakeSelf(), objet, newPosition=Vector([5, 5]))
        self.assertEqual(list(objet.GetXY()), [5, 5])

    def test_contrat_ambigu_sans_sens_ni_position_leve_une_erreur_explicite(self):
        objet = FakeObjet(Vector([0, 0]))
        with self.assertRaises(ValueError):
            self.fonction(FakeSelf(), objet)

    def test_sens_non_reconnu_leve_une_erreur_explicite(self):
        objet = FakeObjet(Vector([0, 0]))
        with self.assertRaises(ValueError):
            self.fonction(FakeSelf(), objet, sens="diagonale")


if __name__ == "__main__":
    unittest.main()
