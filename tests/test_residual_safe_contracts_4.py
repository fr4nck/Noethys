from pathlib import Path

from scripts import qualify_branch_assignment_gaps as qualify

TARGETS = {
    ("Ctrl/CTRL_Informations.py", "GetRenseignements", "dictDonneesFamille"),
    ("Ctrl/CTRL_Tarification_calcul.py", "Sauvegarde", "DB"),
    ("Ctrl/CTRL_Tarification_forfait.py", "Sauvegarde", "options"),
    ("Dlg/DLG_Appliquer_forfait.py", "Applique_forfait", "IDgroupe"),
    ("Dlg/DLG_Appliquer_forfait.py", "Applique_forfait", "IDinscription"),
    ("Dlg/DLG_Nbre_inscrits_2.py", "MAJ", "dictGroupeParActivite"),
    ("Ol/OL_PES_pieces.py", "GetTracks", "criteres"),
    ("Utils/UTILS_Portail_synchro.py", "Upload_data", "IDfamille"),
    ("Utils/UTILS_Portail_synchro.py", "Upload_data", "IDutilisateur"),
    ("Utils/UTILS_Portail_synchro.py", "Upload_data", "nomDossier"),
    ("Utils/UTILS_Portail_synchro.py", "Download_data", "listeRefExistantes"),
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


def test_source_contracts_remain_visible():
    root = Path("noethys")
    infos = (root / "Ctrl/CTRL_Informations.py").read_text(encoding="utf-8")
    assert "if self.IDfamille != None :\n            req =" in infos
    assert "IDtype_renseignement == 7 and self.IDfamille != None" in infos

    calcul = (root / "Ctrl/CTRL_Tarification_calcul.py").read_text(encoding="utf-8")
    assert "if self.track_tarif == None :\n            DB = GestionDB.DB()" in calcul
    assert "if self.track_tarif == None :\n                    DB.ReqDEL" in calcul
    assert "if self.track_tarif == None :\n            DB.Close()" in calcul

    forfait = (root / "Ctrl/CTRL_Tarification_forfait.py").read_text(encoding="utf-8")
    assert "style=wx.RB_GROUP" in forfait
    assert "if self.radio_conso_sans.GetValue() == True :\n            options = None" in forfait
    assert "if self.radio_conso_ouvertures.GetValue() == True :\n            options = None" in forfait
    assert "if self.radio_conso_perso.GetValue() == True :\n            options = None" in forfait

    applique = (root / "Dlg/DLG_Appliquer_forfait.py").read_text(encoding="utf-8")
    assert 'IDinscription = dictInscription["IDinscription"]' in applique
    assert 'IDgroupe = dictInscription["IDgroupe"]' in applique
    assert "if IDcategorie_tarif_temp != None :" in applique

    inscrits = (root / "Dlg/DLG_Nbre_inscrits_2.py").read_text(encoding="utf-8")
    assert "if self.regroupement_groupe_activites == 1 :" in inscrits
    assert "self.regroupement_groupe_activites == 1 and IDactivite in dictGroupeParActivite" in inscrits

    pes = (root / "Ol/OL_PES_pieces.py").read_text(encoding="utf-8")
    assert "if IDlot == None and IDmandat == None :\n        return []" in pes

    portail = (root / "Utils/UTILS_Portail_synchro.py").read_text(encoding="utf-8")
    assert 'for profil, listeDonnees in [("famille", listeFamilles), ("utilisateur", listeUtilisateurs)]:' in portail
    assert "if full_synchro == True :\n            # Demande à récupérer toutes les actions du portail" in portail
    assert 'if full_synchro == True:\n                    if action["ref_unique"] in listeRefExistantes' in portail
