# -*- coding: utf-8 -*-
import ast
import unittest
from pathlib import Path

from scripts import audit_semantic_traps


ROOT = Path(__file__).resolve().parents[1]
CAS = (
    ("Ctrl/CTRL_Editeur_email.py", "OnFileViewHTML", "dlg"),
    ("Ctrl/CTRL_Timeline.py", "_display_error_message", "dial"),
    ("Dlg/DLG_Mailer.py", "VerifieFusion", "dlgErreur"),
    ("Dlg/DLG_Nbre_inscrits.py", "OnBoutonParametres", "dlg"),
    ("Dlg/DLG_Nbre_inscrits_2.py", "OnBoutonParametres", "dlg"),
    ("Noethys.py", "On_propos_licence", "dlg"),
    ("Utils/UTILS_Procedures.py", "A9062", "dlg"),
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


def _lignes_appel(fonction, variable, methode):
    return sorted(
        noeud.lineno
        for noeud in ast.walk(fonction)
        if isinstance(noeud, ast.Call)
        and isinstance(noeud.func, ast.Attribute)
        and noeud.func.attr == methode
        and isinstance(noeud.func.value, ast.Name)
        and noeud.func.value.id == variable
    )


class SemanticModalDestroyTests(unittest.TestCase):
    def test_chaque_dialogue_modal_est_detruit_apres_affichage(self):
        for chemin, nom_fonction, variable in CAS:
            path = ROOT / "noethys" / chemin
            with self.subTest(path=chemin, fonction=nom_fonction):
                fonction = _fonction(path, nom_fonction)
                affichages = _lignes_appel(fonction, variable, "ShowModal")
                destructions = _lignes_appel(fonction, variable, "Destroy")

                self.assertTrue(affichages)
                self.assertTrue(destructions)
                self.assertLess(affichages[-1], destructions[0])

    def test_l_audit_semantique_ne_signale_plus_ces_dialogues(self):
        for chemin, nom_fonction, variable in CAS:
            path = ROOT / "noethys" / chemin
            with self.subTest(path=chemin, fonction=nom_fonction):
                signaux = [
                    signal
                    for signal in audit_semantic_traps.scan_file(path)
                    if signal["kind"] == "modal_without_destroy"
                    and signal["function"] == nom_fonction
                    and signal["dialog"] == variable
                ]

                self.assertEqual(signaux, [])

    def test_les_valeurs_utiles_sont_lues_avant_destruction(self):
        cas = (
            ("Dlg/DLG_Mailer.py", "VerifieFusion", "dlgErreur", "ShowModal"),
            ("Utils/UTILS_Procedures.py", "A9062", "dlg", "GetValue"),
        )
        for chemin, nom_fonction, variable, methode_lecture in cas:
            path = ROOT / "noethys" / chemin
            with self.subTest(path=chemin, fonction=nom_fonction):
                fonction = _fonction(path, nom_fonction)
                lectures = _lignes_appel(fonction, variable, methode_lecture)
                destructions = _lignes_appel(fonction, variable, "Destroy")

                self.assertTrue(lectures)
                self.assertTrue(destructions)
                self.assertLess(lectures[-1], destructions[0])


if __name__ == "__main__":
    unittest.main()
