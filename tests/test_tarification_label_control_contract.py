# -*- coding: utf-8 -*-
import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FICHIER = ROOT / "noethys" / "Ctrl" / "CTRL_Tarification_generalites.py"


def _source_et_constructeur():
    source = FICHIER.read_text(encoding="utf-8")
    arbre = ast.parse(source)
    for noeud in arbre.body:
        if isinstance(noeud, ast.ClassDef) and noeud.name == "CTRL_Label_prestation":
            for membre in noeud.body:
                if isinstance(membre, (ast.FunctionDef, ast.AsyncFunctionDef)) and membre.name == "__init__":
                    return source, membre
    raise AssertionError("CTRL_Label_prestation.__init__ introuvable")


def test_label_prestation_ne_partage_pas_la_liste_de_choix_par_defaut():
    source, constructeur = _source_et_constructeur()
    assert constructeur.args.defaults
    valeur_defaut = constructeur.args.defaults[-1]
    assert isinstance(valeur_defaut, ast.Constant)
    assert valeur_defaut.value is None
    assert "self.listeChoix = list(listeChoix) if listeChoix is not None else []" in source


def test_label_prestation_ne_mutile_pas_la_liste_fournie_par_l_appelant():
    source, _ = _source_et_constructeur()
    assert "self.listeChoix = listeChoix\n" not in source
    assert "self.listeChoix.append((\"autre:\"" in source


def test_label_prestation_ne_combine_pas_expand_et_alignement():
    source, _ = _source_et_constructeur()
    lignes = [
        ligne
        for ligne in source.splitlines()
        if "grid_sizer_base.Add(self.ctrl_choix" in ligne
        or "grid_sizer_base.Add(self.ctrl_autre" in ligne
    ]
    assert len(lignes) == 2
    for ligne in lignes:
        assert "wx.EXPAND" in ligne
        assert "wx.ALIGN_" not in ligne
