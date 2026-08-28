from pathlib import Path
import importlib.util
import sys

qualifier = Path("scripts/qualify_branch_assignment_gaps.py")
q = qualifier.read_text(encoding="utf-8")
q = q.replace(
    "correspondre à exactement un candidat brut ; une entrée absente ou ambiguë est\nsignalée et couverte par les tests du dépôt.",
    "correspondre à exactement un candidat brut et à l’empreinte AST complète de\nla fonction qui porte son invariant ; une entrée absente, modifiée ou ambiguë est\nsignalée et couverte par les tests du dépôt.",
)
old = '''        payload = "|".join((\n            item["function"],\n            item["name"],\n            item["detail"],\n            ast.dump(if_node, include_attributes=False),\n            ast.dump(event_node, include_attributes=False),\n        ))\n'''
new = '''        # Une qualification humaine peut dépendre d'un garde ou d'une boucle\n        # située avant/après le ``if`` directement signalé. On empreinte donc la\n        # fonction entière plutôt qu'un voisinage local : toute évolution du flot\n        # qui établit l'invariant rend l'entrée explicite obsolète et la remet en\n        # ``high/review`` jusqu'à nouvelle validation humaine.\n        payload = "|".join((\n            item["function"],\n            item["name"],\n            item["detail"],\n            ast.dump(function, include_attributes=False),\n        ))\n'''
if old not in q:
    raise SystemExit("fingerprint payload block not found")
q = q.replace(old, new, 1)
q = q.replace(
    "Les numéros de ligne servent uniquement à retrouver les nœuds signalés par\n    le scanner. Ils ne participent pas à l'empreinte : un déplacement de code\n    reste donc stable, tandis qu'une modification du branchement ou de la\n    lecture rend automatiquement l'entrée de registre obsolète.",
    "Les numéros de ligne servent uniquement à retrouver la fonction signalée par\n    le scanner. Ils ne participent pas à l'empreinte. En revanche, toute évolution\n    AST de cette fonction invalide la qualification, y compris un garde ou une\n    boucle environnante dont dépend l'invariant humain.",
)
qualifier.write_text(q, encoding="utf-8")

# Charge le module modifié : l'ancien registre peut être momentanément obsolète,
# mais le calcul d'empreinte reste utilisable pour régénérer ses quatre clés.
spec = importlib.util.spec_from_file_location("qualifier_tmp", qualifier)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
base = module.base

base_keys = [
    ("Dlg/DLG_Saisie_portail_demande.py", "MAJ_informations", "dict_periodes", "body_only"),
    ("Dlg/DLG_Saisie_portail_demande.py", "MAJ_informations", "dict_factures", "body_only"),
    ("Dlg/DLG_Saisie_portail_demande.py", "Traitement_recus", "reponse", "body_only"),
    ("Dlg/DLG_Saisie_portail_demande.py", "Traitement_factures", "reponse", "body_only"),
]
reasons = {
    base_keys[0]: "la lecture n'est atteinte qu'en itérant des paiements de type période ; ce même ensemble non vide initialise dict_periodes juste avant",
    base_keys[1]: "la lecture n'est atteinte qu'en itérant des paiements de type facture ; ce même ensemble non vide initialise dict_factures juste avant",
    base_keys[2]: "les chemins continuants sont couverts par methode_envoi != 'email' ou methode_envoi == 'email' ; chacun définit reponse avant le retour",
    base_keys[3]: "les chemins continuants sont couverts par methode_envoi != 'email' ou methode_envoi == 'email' ; chacun définit reponse avant le retour",
}
raw = base.build_report(Path("noethys"))
by_key = {}
for item in raw["findings"]:
    key = (item["file"], item["function"], item["name"], item["detail"])
    by_key.setdefault(key, []).append(item)

fingerprints = {}
for key in base_keys:
    matches = by_key.get(key, [])
    if len(matches) != 1:
        raise SystemExit(f"expected exactly one raw candidate for {key}, got {len(matches)}")
    fp = module._candidate_fingerprint(Path("noethys"), matches[0])
    if not fp:
        raise SystemExit(f"could not fingerprint {key}")
    fingerprints[key] = fp

q = qualifier.read_text(encoding="utf-8")
start = q.index("EXPLICIT_SAFE = {")
end = q.index("\n}\n", start) + 2
lines = ["EXPLICIT_SAFE = {"]
for key in base_keys:
    full_key = key + (fingerprints[key],)
    lines.append(f"    {full_key!r}: (")
    lines.append(f"        {reasons[key]!r}")
    lines.append("    ),")
lines.append("}")
q = q[:start] + "\n".join(lines) + q[end:]
qualifier.write_text(q, encoding="utf-8")

# Régression ciblée sur le cas remonté par Codex : le même if signalé et le même
# return ne suffisent pas si le garde précédent qui couvre l'autre chemin change.
tests = Path("tests/test_branch_assignment_gap_qualification.py")
t = tests.read_text(encoding="utf-8")
anchor = "    def test_repository_qualification_is_exported_without_hidden_candidates(self):\n"
addition = '''    def test_explicit_safe_fingerprint_covers_surrounding_control_flow(self):\n        source = (base.NOETHYS / "Dlg" / "DLG_Saisie_portail_demande.py").read_text(encoding="utf-8")\n        marker = "    def Traitement_recus(self):"\n        prefix, suffix = source.split(marker, 1)\n        original = 'if self.dict_parametres["methode_envoi"] != "email" :'\n        changed = 'if self.dict_parametres["methode_envoi"] == "courrier" :'\n        self.assertIn(original, suffix)\n        suffix = suffix.replace(original, changed, 1)\n\n        with tempfile.TemporaryDirectory() as tmp:\n            root = Path(tmp)\n            target = root / "Dlg" / "DLG_Saisie_portail_demande.py"\n            target.parent.mkdir(parents=True)\n            target.write_text(prefix + marker + suffix, encoding="utf-8")\n            report = audit.build_report(root)\n\n        candidate = next(\n            item for item in report["findings"]\n            if item["function"] == "Traitement_recus" and item["name"] == "reponse"\n        )\n        self.assertEqual(candidate["classification"], "review")\n        self.assertEqual(candidate["priority"], "high")\n\n'''
if addition not in t:
    if anchor not in t:
        raise SystemExit("test anchor not found")
    tests.write_text(t.replace(anchor, addition + anchor, 1), encoding="utf-8")
