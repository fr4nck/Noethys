# -*- coding: utf-8 -*-
import ast
import unittest
from pathlib import Path

from scripts import audit_semantic_traps


ROOT = Path(__file__).resolve().parents[1]
CAS = (
    ("Ctrl/CTRL_Portail_serveur.py", "OnClose"),
    ("Dlg/DLG_Transfert_tables.py", "OnBoutonOk"),
    ("Noethys.py", "On_outils_updater"),
)


def _fonction(path, nom):
    arbre = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    fonctions = [
        noeud
        for noeud in ast.walk(arbre)
        if isinstance(noeud, ast.FunctionDef) and noeud.name == nom
    ]
    if len(fonctions) != 1:
        raise AssertionError("Fonction %s introuvable ou ambiguë dans %s" % (nom, path))
    return fonctions[0]


class NonBlockingUiCallbacksTests(unittest.TestCase):
    def test_l_audit_ne_signale_plus_de_pause_dans_les_callbacks(self):
        for chemin, nom_fonction in CAS:
            path = ROOT / "noethys" / chemin
            with self.subTest(path=chemin, fonction=nom_fonction):
                signaux = [
                    signal
                    for signal in audit_semantic_traps.scan_file(path)
                    if signal["kind"] == "blocking_sleep_ui_callback"
                    and signal["function"] == nom_fonction
                ]

                self.assertEqual(signaux, [])

    def test_la_fermeture_du_serveur_conserve_son_delai_sans_bloquer_wx(self):
        path = ROOT / "noethys" / "Ctrl" / "CTRL_Portail_serveur.py"
        fonction = _fonction(path, "OnClose")
        appels = [
            noeud
            for noeud in ast.walk(fonction)
            if isinstance(noeud, ast.Call)
            and isinstance(noeud.func, ast.Attribute)
            and isinstance(noeud.func.value, ast.Name)
            and noeud.func.value.id == "wx"
            and noeud.func.attr == "CallLater"
        ]

        self.assertEqual(len(appels), 1)
        self.assertIsInstance(appels[0].args[0], ast.Constant)
        self.assertEqual(appels[0].args[0].value, 100)
        rappel = appels[0].args[1]
        self.assertIsInstance(rappel, ast.Attribute)
        self.assertIsInstance(rappel.value, ast.Name)
        self.assertEqual(rappel.value.id, "self")
        self.assertEqual(rappel.attr, "Destroy")

    def test_le_transfert_reste_synchrone_sans_pause_artificielle(self):
        path = ROOT / "noethys" / "Dlg" / "DLG_Transfert_tables.py"
        fonction = _fonction(path, "OnBoutonOk")
        exports = [
            noeud
            for noeud in ast.walk(fonction)
            if isinstance(noeud, ast.Call)
            and isinstance(noeud.func, ast.Attribute)
            and noeud.func.attr == "Exportation_vers_base_defaut"
        ]

        self.assertEqual(len(exports), 1)


if __name__ == "__main__":
    unittest.main()
