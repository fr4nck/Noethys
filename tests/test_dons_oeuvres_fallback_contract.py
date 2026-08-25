# -*- coding: utf-8 -*-
import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FICHIER = ROOT / "noethys" / "Dlg" / "DLG_Impression_don_oeuvres.py"


def _source_et_arbre():
    source = FICHIER.read_text(encoding="utf-8")
    return source, ast.parse(source)


def _methode(arbre, classe, methode):
    for noeud in arbre.body:
        if isinstance(noeud, ast.ClassDef) and noeud.name == classe:
            for membre in noeud.body:
                if isinstance(membre, ast.FunctionDef) and membre.name == methode:
                    return membre
    raise AssertionError(f"{classe}.{methode} introuvable")


def _est_cible_date_edition(cible):
    return isinstance(cible, ast.Name) and cible.id == "date_edition"


def test_aucun_titulaire_ne_reutilise_pas_un_idindividu_inexistant():
    source, _ = _source_et_arbre()
    assert "self.dictDonnees[0] = IDindividu" not in source
    assert "if nbreTitulaires > 0:" in source
    assert "self.dictDonnees[0] = listeTitulaires[-1][0]" in source


def test_nom_collectif_conserve_tous_les_titulaires():
    source, _ = _source_et_arbre()
    assert "listeTitulaires[:-2]" not in source
    assert "listeTitulaires[:-1]" in source


def test_date_edition_est_definie_dans_les_deux_branches():
    _, arbre = _source_et_arbre()
    constructeur = _methode(arbre, "Impression", "__init__")

    candidat = None
    for noeud in ast.walk(constructeur):
        if not isinstance(noeud, ast.If):
            continue
        test = ast.unparse(noeud.test)
        if "dictDonnees['date_edition']" in test or 'dictDonnees["date_edition"]' in test:
            candidat = noeud
            break

    assert candidat is not None
    assert any(
        isinstance(stmt, ast.Assign)
        and any(_est_cible_date_edition(cible) for cible in stmt.targets)
        for stmt in candidat.body
    )
    assert any(
        isinstance(stmt, ast.Assign)
        and any(_est_cible_date_edition(cible) for cible in stmt.targets)
        for stmt in candidat.orelse
    )


def test_repli_date_edition_ne_modifie_pas_le_dictionnaire_appelant():
    source, _ = _source_et_arbre()
    assert 'dictDonnees["date_edition"] = u""' not in source
