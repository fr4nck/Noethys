from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
CHAMPS = ROOT / 'noethys' / 'Ol' / 'OL_Etat_nomin_champs.py'
RESULTATS = ROOT / 'noethys' / 'Ol' / 'OL_Etat_nomin_resultats.py'

def test_etat_nominatif_ignore_questionnaire_types_not_supported():
    source = CHAMPS.read_text(encoding='utf-8')
    assert 'elif type == "famille"' in source
    assert 'continue' in source[source.index('for IDquestion, label, type, controle in listeQuestions'):source.index('# Quantité UNITES')]

def test_etat_nominatif_uses_localized_question_categories_and_guard():
    source = RESULTATS.read_text(encoding='utf-8')
    block = source[source.index('# Questionnaires'):source.index('# Regroupement des conso')]
    assert 'champ.categorie == _(u"Individu")' in block
    assert 'champ.categorie == _(u"Famille")' in block
    assert 'else :' in block and 'continue' in block

def test_targeted_branch_gap_findings_disappear():
    spec = importlib.util.spec_from_file_location('audit_branch_assignment_gaps', ROOT / 'scripts' / 'audit_branch_assignment_gaps.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    findings = []
    for path in (CHAMPS, RESULTATS):
        findings.extend(mod.scan_file(path, ROOT / 'noethys'))
    targeted = [f for f in findings if f.get('name') in {'categorie', 'IDtemp'}]
    assert targeted == [], targeted
