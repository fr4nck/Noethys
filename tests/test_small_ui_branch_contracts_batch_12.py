
import unittest
from pathlib import Path
from scripts import audit_branch_assignment_gaps

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "noethys"

TARGETS = {
    ("Dlg/DLG_Gestionnaire_conso.py", "On_affichage_largeur_unite", "newLargeur"),
    ("Dlg/DLG_Parametres_nbre_inscrits.py", "OnBoutonOk", "parametre"),
    ("Dlg/DLG_Saisie_contrat.py", "MAJ", "label"),
    ("Ol/OL_Langues.py", "Ajouter", "nom"),
    ("Dlg/DLG_Individu_identite.py", "SetValeursDefaut", "IDcivilite"),
}

class TestBatch12Contracts(unittest.TestCase):
    def test_targeted_findings_disappear(self):
        remaining = set()
        for rel, func, name in TARGETS:
            findings = audit_branch_assignment_gaps.scan_file(SRC / rel, SRC)
            for item in findings:
                key = (item["file"], item["function"], item["name"])
                if key in TARGETS:
                    remaining.add(key)
        self.assertEqual(remaining, set(), remaining)

    def test_cancelled_width_dialog_returns_before_persist(self):
        text = (SRC / "Dlg/DLG_Gestionnaire_conso.py").read_text(encoding="utf-8")
        self.assertIn("if reponse != wx.ID_OK:", text)
        self.assertIn("UTILS_Config.SetParametre(\"largeur_colonne_unite\", newLargeur)", text)

    def test_contract_mode_is_exhaustive(self):
        text = (SRC / "Dlg/DLG_Parametres_nbre_inscrits.py").read_text(encoding="utf-8")
        self.assertIn("raise ValueError(\"Mode de sélection d'activités inconnu", text)

if __name__ == "__main__":
    unittest.main()
