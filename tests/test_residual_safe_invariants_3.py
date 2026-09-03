from pathlib import Path

from scripts import qualify_branch_assignment_gaps as qualify

TARGETS = {
    ("Ctrl/CTRL_Grille.py", "SetModeIndividu", "attente", "body_only"),
    ("Ctrl/CTRL_Grille.py", "SetModeDate", "attente", "body_only"),
    ("Ctrl/CTRL_Grille.py", "Sauvegarde", "IDcategorie", "body_only"),
    ("Ctrl/CTRL_Locations_tableau.py", "Draw", "hauteurTrait", "partial_branches"),
    ("Ctrl/CTRL_Synthese_impayes.py", "MAJ", "niveau2", "body_only"),
    ("Ctrl/CTRL_Synthese_prestations.py", "MAJ", "niveau2", "body_only"),
    ("Ctrl/CTRL_Synthese_ventilation.py", "MAJ", "niveauPrestation", "body_only"),
}


def test_residual_safe_invariants_are_exactly_qualified():
    report = qualify.build_report()
    registry = report["explicit_safe_registry"]
    assert registry["unmatched"] == []
    assert registry["ambiguous"] == []
    for target in TARGETS:
        matches = [
            item for item in report["findings"]
            if (item["file"], item["function"], item["name"], item["detail"]) == target
        ]
        assert len(matches) == 1
        assert matches[0]["classification"] == "explicit_safe"


def test_source_contracts_support_the_qualifications():
    root = Path("noethys")
    grille = (root / "Ctrl/CTRL_Grille.py").read_text(encoding="utf-8")
    assert grille.count("if modeSilencieux == False :") >= 4
    assert 'for codeCategorie in ("suppr", "modif", "ajout") :' in grille
    assert 'if codeCategorie == "ajout" : IDcategorie = 9' in grille
    assert 'if codeCategorie == "modif" : IDcategorie = 29' in grille
    assert 'if codeCategorie == "suppr" : IDcategorie = 10' in grille

    locations = (root / "Ctrl/CTRL_Locations_tableau.py").read_text(encoding="utf-8")
    assert "byminute=(0, 15, 30, 45)" in locations
    assert "if dt.minute == 0:" in locations
    assert "elif dt.minute in (15, 45):" in locations
    assert "elif dt.minute == 30:" in locations

    impayes = (root / "Ctrl/CTRL_Synthese_impayes.py").read_text(encoding="utf-8")
    assert "if self.affichage_details == True :\n                    niveau2 = self.AppendItem" in impayes

    prestations = (root / "Ctrl/CTRL_Synthese_prestations.py").read_text(encoding="utf-8")
    assert 'if self.key_ligne2 != "" :\n                    niveau2 = self.AppendItem' in prestations

    ventilation = (root / "Ctrl/CTRL_Synthese_ventilation.py").read_text(encoding="utf-8")
    assert "if self.affichage_details == True :\n                    niveauPrestation = self.AppendItem" in ventilation
