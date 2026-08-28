#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import types
import unittest
from pathlib import Path

from scripts import audit_branch_assignment_gaps


ROOT = Path(__file__).resolve().parents[1]
TARGETS = (
    ROOT / "noethys" / "Dlg" / "DLG_Importation_fichier.py",
    ROOT / "noethys" / "Dlg" / "DLG_Ouvrir_fichier.py",
)


def load_get_nom_fichier(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    method = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "GetNomFichier":
                    method = item
                    break
        if method is not None:
            break
    if method is None:
        raise AssertionError(f"GetNomFichier absent de {path}")
    module = ast.Module(body=[method], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {
        "six": types.SimpleNamespace(PY2=False),
        "GestionDB": types.SimpleNamespace(EncodeMdpReseau=lambda value: "ENC:" + value),
    }
    exec(compile(module, str(path), "exec"), namespace)
    return namespace["GetNomFichier"]


class Radio:
    def __init__(self, value):
        self.value = value

    def GetValue(self):
        return self.value


class Files:
    def __init__(self, title):
        self.title = title

    def GetFirstSelected(self):
        return 0

    def GetItemPyData(self, index):
        return {"titre": self.title}


class FakeDialog:
    def __init__(self, mode_local, title="demo"):
        self.radio_local = Radio(mode_local)
        self.ctrl_fichiers = Files(title)

    def GetCodesReseau(self):
        return {
            "port": "3306",
            "hote": "db.example",
            "utilisateur": "user",
            "motdepasse": "secret",
        }


class FileModeBranchContractTests(unittest.TestCase):
    def test_local_mode_preserves_plain_filename(self):
        for path in TARGETS:
            with self.subTest(path=path.name):
                method = load_get_nom_fichier(path)
                self.assertEqual(method(FakeDialog(True, "base_test")), "base_test")

    def test_network_mode_preserves_connection_descriptor(self):
        expected = "3306;db.example;user;ENC:secret[RESEAU]base_test"
        for path in TARGETS:
            with self.subTest(path=path.name):
                method = load_get_nom_fichier(path)
                self.assertEqual(method(FakeDialog(False, "base_test")), expected)

    def test_mode_branch_is_exhaustive(self):
        for path in TARGETS:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            method = next(
                item
                for node in tree.body if isinstance(node, ast.ClassDef)
                for item in node.body
                if isinstance(item, ast.FunctionDef) and item.name == "GetNomFichier"
            )
            segment = ast.get_source_segment(source, method)
            self.assertIn("if modeLocal == True", segment)
            self.assertNotIn("if modeLocal == False", segment)

    def test_targeted_branch_assignment_gaps_are_gone(self):
        for path in TARGETS:
            rel = path.relative_to(ROOT / "noethys").as_posix()
            findings = audit_branch_assignment_gaps.scan_file(path, rel)
            targeted = [
                finding for finding in findings
                if finding.get("function") == "GetNomFichier" and finding.get("name") == "nomFichier"
            ]
            self.assertEqual(targeted, [], targeted)


if __name__ == "__main__":
    unittest.main()
