# -*- coding: utf-8 -*-
import ast
from pathlib import Path
from types import SimpleNamespace

from scripts import audit_branch_assignment_gaps


ROOT = Path(__file__).resolve().parents[1]
FICHIER = ROOT / "noethys" / "Ol" / "OL_Lots_pes.py"


def _charger_get_classe():
    source = FICHIER.read_text(encoding="utf-8")
    arbre = ast.parse(source)
    fonction = None
    for noeud in arbre.body:
        if isinstance(noeud, ast.ClassDef) and noeud.name == "ListView":
            for membre in noeud.body:
                if isinstance(membre, ast.FunctionDef) and membre.name == "Get_classe":
                    fonction = membre
                    break
    assert fonction is not None

    marqueurs = {
        "pes": object(),
        "magnus": object(),
        "jvs": object(),
        "corail": object(),
    }
    espace = {
        "DLG_Saisie_lot_tresor_public_pes": SimpleNamespace(Dialog=marqueurs["pes"]),
        "DLG_Saisie_lot_tresor_public_magnus": SimpleNamespace(Dialog=marqueurs["magnus"]),
        "DLG_Saisie_lot_tresor_public_jvs": SimpleNamespace(Dialog=marqueurs["jvs"]),
        "DLG_Saisie_lot_tresor_public_corail": SimpleNamespace(Dialog=marqueurs["corail"]),
    }
    module = ast.Module(body=[fonction], type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module, str(FICHIER), "exec"), espace)
    return espace["Get_classe"], marqueurs


def test_get_classe_conserve_les_quatre_formats_connus():
    get_classe, marqueurs = _charger_get_classe()
    for code, classe in marqueurs.items():
        assert get_classe(None, code) == (code, classe)


def test_get_classe_refuse_proprement_un_format_inconnu():
    get_classe, _ = _charger_get_classe()
    assert get_classe(None, "format-inconnu") == (False, False)


def test_get_classe_ne_presente_plus_de_variable_classe_non_initialisee():
    findings = audit_branch_assignment_gaps.scan_file(FICHIER)
    assert not any(
        item["function"] == "Get_classe" and item["name"] == "classe"
        for item in findings
    )
