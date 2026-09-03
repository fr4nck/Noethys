import unittest
from pathlib import Path
from scripts import audit_branch_assignment_gaps as audit
from scripts import qualify_branch_assignment_gaps as qualify

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
SPECS = (
    ("Dlg/DLG_Impression_don_oeuvres.py", "SetListeDonnees", "nomTitulaires", "body_only"),
    ("Dlg/DLG_Saisie_cotisation.py", "SetListeDonnees", "nomTitulaires", "body_only"),
    ("Dlg/DLG_Saisie_cotisation.py", "MAJ", "nomTitulaires", "body_only"),
    ("Dlg/DLG_Saisie_cotisation.py", "MAJ", "IDcompte_payeur", "body_only"),
    ("Ol/OL_Etat_nomin_resultats.py", "__init__", "valeur", "partial_branches"),
    ("Utils/UTILS_Sauvegarde.py", "Sauvegarde", "err", "body_only"),
    ("Dlg/DLG_Releve_prestations_saisie.py", "GetOptions", "regroupement", "partial_branches"),
    ("Dlg/DLG_Saisie_texte_html.py", "Importation", "condition", "body_only"),
    ("Dlg/DLG_Stats.py", "Imprimer", "html", "body_only"),
    ("Utils/UTILS_Stats_modeles.py", "GetHTML", "html", "body_only"),
)

class FiniteDomainSafeInvariantTests(unittest.TestCase):
    def test_candidates_are_exactly_qualified(self):
        for relative, function, name, detail in SPECS:
            matches = [x for x in audit.scan_file(NOETHYS / relative, NOETHYS)
                       if x["function"] == function and x["name"] == name and x["detail"] == detail]
            self.assertEqual(len(matches), 1, (relative, function, name, detail))
            self.assertIn(qualify.qualification_key(matches[0], NOETHYS), qualify.EXPLICIT_SAFE)

    def test_domain_contracts_are_still_present(self):
        holders = ((NOETHYS / "Dlg/DLG_Impression_don_oeuvres.py").read_text(encoding="utf-8") +
                   (NOETHYS / "Dlg/DLG_Saisie_cotisation.py").read_text(encoding="utf-8"))
        for condition in ("nbreTitulaires == 0", "nbreTitulaires == 1", "nbreTitulaires == 2", "nbreTitulaires > 2"):
            self.assertIn(condition, holders)
        releve = (NOETHYS / "Dlg/DLG_Releve_prestations_saisie.py").read_text(encoding="utf-8")
        self.assertIn('choices=["Date", _(u"Mois"), _(u"Année")]', releve)
        self.assertIn("self.ctrl_regroupement_date.SetSelection(0)", releve)
        modeles = (NOETHYS / "Utils/UTILS_Stats_modeles.py").read_text(encoding="utf-8")
        self.assertIn('if mode not in ("affichage", "impression")', modeles)

if __name__ == "__main__":
    unittest.main()
