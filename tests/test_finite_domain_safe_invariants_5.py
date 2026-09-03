from pathlib import Path

from scripts import qualify_branch_assignment_gaps as qualify

TARGETS = {
    ("Ctrl/CTRL_Synthese_conso.py", "Importation", "regroupement"),
    ("Ctrl/CTRL_Synthese_conso.py", "Importation", "valeur"),
    ("Ctrl/CTRL_Synthese_deductions.py", "Importation", "regroupement"),
    ("Ctrl/CTRL_Synthese_locations.py", "Importation", "regroupement"),
    ("Ctrl/CTRL_Synthese_modes_reglements.py", "Importation", "condition"),
    ("Ol/OL_Liste_factures_detail.py", "__init__", "label_key"),
    ("Ol/OL_Liste_factures_detail.py", "InitObjectListView", "label_colonne"),
    ("Dlg/DLG_Saisie_tarification.py", "Sauvegarde", "DB"),
}


def test_targets_are_exactly_explicit_safe():
    report = qualify.build_report()
    registry = report["explicit_safe_registry"]
    assert registry["unmatched"] == []
    assert registry["ambiguous"] == []
    for target in TARGETS:
        matches = [item for item in report["findings"] if (item["file"], item["function"], item["name"]) == target]
        assert len(matches) == 1, (target, matches)
        assert matches[0]["classification"] == "explicit_safe"


def test_synthese_ui_domains_remain_explicit():
    root = Path("noethys")
    dlg_conso = (root / "Dlg/DLG_Synthese_conso.py").read_text(encoding="utf-8")
    for code in ("jour", "mois", "annee", "activite", "groupe", "evenement", "evenement_date", "etiquette", "categorie_tarif", "ville_residence", "secteur", "genre", "age", "ville_naissance", "nom_ecole", "nom_classe", "nom_niveau_scolaire", "famille", "individu", "regime", "caisse", "qf", "categorie_travail", "categorie_travail_pere", "categorie_travail_mere"):
        assert f'"code" : "{code}"' in dlg_conso or f'"code": "{code}"' in dlg_conso
    assert 'return "quantite"' in dlg_conso
    assert 'return "temps_presence"' in dlg_conso
    assert 'return "temps_facture"' in dlg_conso
    assert 'code = "question_%s_%d" % (public, dictTemp["IDquestion"])' in dlg_conso

    dlg_deductions = (root / "Dlg/DLG_Synthese_deductions.py").read_text(encoding="utf-8")
    for code in ("jour", "mois", "annee", "ville_residence", "secteur", "famille", "individu", "regime", "caisse", "qf", "montant_deduction", "nom_deduction", "nom_aide"):
        assert f'"code" : "{code}"' in dlg_deductions or f'"code": "{code}"' in dlg_deductions
    assert 'for public in ("famille",)' in dlg_deductions

    dlg_locations = (root / "Dlg/DLG_Synthese_locations.py").read_text(encoding="utf-8")
    for code in ("jour", "mois", "annee", "categorie", "ville_residence", "secteur", "famille", "regime", "caisse", "qf"):
        assert f'"code" : "{code}"' in dlg_locations or f'"code": "{code}"' in dlg_locations
    assert 'for public in ("famille",)' in dlg_locations


def test_radio_and_invoice_detail_domains_remain_bounded():
    root = Path("noethys")
    modes = (root / "Dlg/DLG_Synthese_modes_reglements.py").read_text(encoding="utf-8")
    assert 'self.radio_saisis = wx.RadioButton' in modes and 'wx.RB_GROUP' in modes
    assert 'return "saisis"' in modes
    assert 'return "deposes"' in modes
    assert 'return "nondeposes"' in modes

    factures = (root / "Dlg/DLG_Liste_factures_detail.py").read_text(encoding="utf-8")
    assert 'self.choix_regroupements = [("label",' in factures
    assert '("IDactivite",' in factures
    assert 'self.ctrl_factures.detail = self.choix_regroupements[self.ctrl_regroupement.GetSelection()][0]' in factures


def test_tarification_track_mode_guards_every_database_lifecycle_edge():
    source = Path("noethys/Dlg/DLG_Saisie_tarification.py").read_text(encoding="utf-8")
    assert 'if self.track_tarif == None :\n            DB = GestionDB.DB()' in source
    assert 'if self.track_tarif == None and self.toolbook.GetPage("conditions") != None :' in source
    assert 'if self.track_tarif == None :\n            DB.Close()' in source
