from pathlib import Path
import re

p = Path('noethys/Utils/UTILS_Migration_base.py')
s = p.read_text(encoding='utf-8')

new_dependances = '''DEPENDANCES_COEUR = {
    "familles": [],
    "individus": [],
    "activites": [],
    "categories_tarifs": ["activites"],
    "noms_tarifs": ["activites", "categories_tarifs"],
    "tarifs": ["activites", "categories_tarifs", "noms_tarifs"],
    "groupes": ["activites"],
    "unites": ["activites"],
    "evenements": ["activites", "unites", "groupes"],
    "comptes_payeurs": ["familles", "individus"],
    "rattachements": ["familles", "individus"],
    "inscriptions": ["familles", "individus", "activites", "groupes", "categories_tarifs", "comptes_payeurs"],
    "factures": ["comptes_payeurs"],
    "contrats": ["individus", "inscriptions", "tarifs", "activites"],
    "contrats_tarifs": ["contrats"],
    "prestations": ["comptes_payeurs", "activites", "tarifs", "factures", "familles", "individus", "categories_tarifs", "contrats"],
    "reglements": ["comptes_payeurs"],
    "consommations": ["individus", "inscriptions", "activites", "unites", "groupes", "categories_tarifs", "comptes_payeurs", "evenements"],
    "ventilation": ["reglements", "prestations", "comptes_payeurs"],
    "cotisations": ["familles", "individus"],
    "questionnaire_reponses": ["familles", "individus"],
}
'''
s, n = re.subn(r'DEPENDANCES_COEUR = \{.*?\n\}\n\nCLES_PRIMAIRES_COEUR =', new_dependances + '\nCLES_PRIMAIRES_COEUR =', s, count=1, flags=re.S)
if n != 1:
    raise SystemExit('bloc DEPENDANCES_COEUR introuvable')

# Ajoute les clés primaires des nouvelles tables cœur.
s = s.replace('''    "groupes": "IDgroupe",\n''', '''    "groupes": "IDgroupe",\n    "unites": "IDunite",\n    "evenements": "IDevenement",\n''', 1)

# Étend le périmètre dossier avec ses référentiels directs.
s = s.replace('''        "familles", "individus", "comptes_payeurs", "rattachements",\n        "activites", "groupes", "inscriptions", "consommations",\n        "contrats", "contrats_tarifs", "questionnaire_reponses", "cotisations",\n''', '''        "familles", "individus", "comptes_payeurs", "rattachements",\n        "activites", "groupes", "unites", "evenements",\n        "categories_tarifs", "noms_tarifs", "tarifs",\n        "inscriptions", "consommations", "contrats", "contrats_tarifs",\n        "questionnaire_reponses", "cotisations",\n''', 1)

new_refs = '''REFERENCES_COEUR = {
    "comptes_payeurs": {"IDfamille": "familles", "IDindividu": "individus"},
    "rattachements": {"IDfamille": "familles", "IDindividu": "individus"},
    "groupes": {"IDactivite": "activites"},
    "unites": {"IDactivite": "activites", "IDrestaurateur": "restaurateurs"},
    "evenements": {"IDactivite": "activites", "IDunite": "unites", "IDgroupe": "groupes"},
    "categories_tarifs": {"IDactivite": "activites"},
    "noms_tarifs": {"IDactivite": "activites", "IDcategorie_tarif": "categories_tarifs"},
    "tarifs": {"IDactivite": "activites", "IDcategorie_tarif": "categories_tarifs", "IDnom_tarif": "noms_tarifs"},
    "tarifs_lignes": {"IDtarif": "tarifs"},
    "inscriptions": {
        "IDfamille": "familles", "IDindividu": "individus",
        "IDactivite": "activites", "IDgroupe": "groupes",
        "IDcategorie_tarif": "categories_tarifs", "IDcompte_payeur": "comptes_payeurs",
    },
    "consommations": {
        "IDfamille": "familles", "IDindividu": "individus", "IDinscription": "inscriptions",
        "IDactivite": "activites", "IDunite": "unites", "IDgroupe": "groupes",
        "IDutilisateur": "utilisateurs", "IDcategorie_tarif": "categories_tarifs",
        "IDcompte_payeur": "comptes_payeurs", "IDprestation": "prestations",
        "IDevenement": "evenements",
    },
    "prestations": {
        "IDcompte_payeur": "comptes_payeurs", "IDactivite": "activites", "IDtarif": "tarifs",
        "IDfacture": "factures", "IDfamille": "familles", "IDindividu": "individus",
        "IDcategorie_tarif": "categories_tarifs", "reglement_frais": "reglements",
        "IDcontrat": "contrats",
    },
    "factures": {"IDcompte_payeur": "comptes_payeurs"},
    "reglements": {"IDcompte_payeur": "comptes_payeurs"},
    "ventilation": {
        "IDreglement": "reglements", "IDprestation": "prestations",
        "IDcompte_payeur": "comptes_payeurs",
    },
    "cotisations": {"IDfamille": "familles", "IDindividu": "individus"},
    "questionnaire_reponses": {"IDfamille": "familles", "IDindividu": "individus"},
    "contrats": {
        "IDindividu": "individus", "IDinscription": "inscriptions",
        "IDtarif": "tarifs", "IDactivite": "activites",
    },
    "contrats_tarifs": {"IDcontrat": "contrats"},
}

# Références qui peuvent pointer vers une table migrée plus tard. Elles sont
# insérées à NULL puis réparées dans la même transaction avant le commit final.
REFERENCES_DIFFEREES = {
    "consommations": {"IDprestation": "prestations"},
    "prestations": {"reglement_frais": "reglements"},
}
'''
s, n = re.subn(r'REFERENCES_COEUR = \{.*?\n\}\n\n\nclass MappingIDs', new_refs + '\n\nclass MappingIDs', s, count=1, flags=re.S)
if n != 1:
    raise SystemExit('bloc REFERENCES_COEUR introuvable')

# Refuse silencieusement de recopier des colonnes ID non documentées.
old = '''            details = schema["champs"].get(table, {})\n            if details.get("source_uniquement", []):\n                revue.append({"table": table, "raison": "champs_source_sans_cible",\n                              "champs": details["source_uniquement"], "nbre": item["nbre"]}); continue\n            migrables.append(table)\n'''
new = '''            details = schema["champs"].get(table, {})\n            if details.get("source_uniquement", []):\n                revue.append({"table": table, "raison": "champs_source_sans_cible",\n                              "champs": details["source_uniquement"], "nbre": item["nbre"]}); continue\n            pk = self.cles_primaires[table]\n            refs_connues = set(self.references.get(table, {}))\n            ids_non_decrits = [champ for champ in details.get("communs", [])\n                               if champ != pk and champ.startswith("ID") and champ not in refs_connues]\n            if ids_non_decrits:\n                revue.append({"table": table, "raison": "references_non_decrites",\n                              "champs": ids_non_decrits, "nbre": item["nbre"]}); continue\n            migrables.append(table)\n'''
if old not in s:
    raise SystemExit('validation schema introuvable')
s = s.replace(old, new, 1)

# Étend le moteur aux références différées.
s = s.replace('''    def __init__(self, DBsource, DBcible, plan=None, mapping=None, references=None, tables=None):\n''', '''    def __init__(self, DBsource, DBcible, plan=None, mapping=None, references=None, tables=None, references_differees=None):\n''', 1)
s = s.replace('''        self.references = references or REFERENCES_COEUR\n        self.rapport = []\n''', '''        self.references = references or REFERENCES_COEUR\n        self.references_differees = references_differees or REFERENCES_DIFFEREES\n        self.rapport = []\n''', 1)

old = '''    def _remapper_ligne(self, table, champs, valeurs, cle_primaire):\n        donnees = dict(zip(champs, valeurs))\n        ancien_id = donnees.pop(cle_primaire, None)\n        for champ, table_ref in self.references.get(table, {}).items():\n            if champ not in donnees or donnees[champ] is None:\n                continue\n            ancien_ref = donnees[champ]\n            if not self.mapping.Existe(table_ref, ancien_ref):\n                raise ValueError("Référence non migrée %s.%s=%r vers %s" % (table, champ, ancien_ref, table_ref))\n            donnees[champ] = self.mapping.Get(table_ref, ancien_ref)\n        return ancien_id, donnees\n'''
new = '''    def _remapper_ligne(self, table, champs, valeurs, cle_primaire):\n        donnees = dict(zip(champs, valeurs))\n        ancien_id = donnees.pop(cle_primaire, None)\n        differes = []\n        for champ, table_ref in self.references.get(table, {}).items():\n            if champ not in donnees or donnees[champ] is None:\n                continue\n            ancien_ref = donnees[champ]\n            if self.mapping.Existe(table_ref, ancien_ref):\n                donnees[champ] = self.mapping.Get(table_ref, ancien_ref)\n                continue\n            if self.references_differees.get(table, {}).get(champ) == table_ref:\n                donnees[champ] = None\n                differes.append((champ, table_ref, ancien_ref))\n                continue\n            raise ValueError("Référence non migrée %s.%s=%r vers %s" % (table, champ, ancien_ref, table_ref))\n        return ancien_id, donnees, differes\n'''
if old not in s:
    raise SystemExit('_remapper_ligne introuvable')
s = s.replace(old, new, 1)

old = '''            lignes = self._lire_table(table, champs)\n            if lignes is None:\n                erreurs.append({"table": table, "erreur": "lecture_source"}); continue\n            compte += len(lignes)\n'''
new = '''            lignes = self._lire_table(table, champs)\n            if lignes is None:\n                erreurs.append({"table": table, "erreur": "lecture_source"}); continue\n            tables_plan = set(simulation["plan"]["ordre"])\n            refs = self.references.get(table, {})\n            indexes = {champ: index for index, champ in enumerate(champs)}\n            for champ, table_ref in refs.items():\n                if champ not in indexes or table_ref in tables_plan:\n                    continue\n                index = indexes[champ]\n                for valeurs in lignes:\n                    ancien_ref = valeurs[index]\n                    if ancien_ref is not None and not self.mapping.Existe(table_ref, ancien_ref):\n                        erreurs.append({"table": table, "champ": champ, "erreur": "reference_hors_perimetre",\n                                        "cible": table_ref, "valeur": ancien_ref})\n                        break\n            compte += len(lignes)\n'''
if old not in s:
    raise SystemExit('bloc simulation lecture introuvable')
s = s.replace(old, new, 1)

old = '''        schema = self.analyse.ComparerSchemas()\n        self.rapport = []\n        try:\n            for item in simulation["plan"]["tables_migrables"]:\n'''
new = '''        schema = self.analyse.ComparerSchemas()\n        self.rapport = []\n        references_a_reparer = []\n        try:\n            for item in simulation["plan"]["tables_migrables"]:\n'''
if old not in s:
    raise SystemExit('préambule Executer introuvable')
s = s.replace(old, new, 1)

old = '''                for valeurs in lignes:\n                    ancien_id, donnees = self._remapper_ligne(table, champs, valeurs, pk)\n                    liste_donnees = [(champ, donnees[champ]) for champ in champs if champ != pk and champ in donnees]\n                    nouvel_id = self.DBcible.ReqInsert(table, liste_donnees, commit=False)\n                    if nouvel_id is None:\n                        raise RuntimeError("Insertion impossible dans %s (ID source %r)" % (table, ancien_id))\n                    if ancien_id is not None:\n                        self.mapping.Ajouter(table, ancien_id, nouvel_id)\n                    nb += 1\n                self.rapport.append({"table": table, "lignes": nb, "statut": "preparee"})\n            self.DBcible.Commit()\n'''
new = '''                for valeurs in lignes:\n                    ancien_id, donnees, differes = self._remapper_ligne(table, champs, valeurs, pk)\n                    liste_donnees = [(champ, donnees[champ]) for champ in champs if champ != pk and champ in donnees]\n                    nouvel_id = self.DBcible.ReqInsert(table, liste_donnees, commit=False)\n                    if nouvel_id is None:\n                        raise RuntimeError("Insertion impossible dans %s (ID source %r)" % (table, ancien_id))\n                    if ancien_id is not None:\n                        self.mapping.Ajouter(table, ancien_id, nouvel_id)\n                    for champ, table_ref, ancien_ref in differes:\n                        references_a_reparer.append((table, pk, nouvel_id, champ, table_ref, ancien_ref))\n                    nb += 1\n                self.rapport.append({"table": table, "lignes": nb, "statut": "preparee"})\n\n            # Répare les références avant tout commit : aucune FK différée ne peut\n            # rester orpheline dans la base cible.\n            for table, pk, nouvel_id, champ, table_ref, ancien_ref in references_a_reparer:\n                if not self.mapping.Existe(table_ref, ancien_ref):\n                    raise ValueError("Référence différée non migrée %s.%s=%r vers %s" %\n                                     (table, champ, ancien_ref, table_ref))\n                nouvel_ref = self.mapping.Get(table_ref, ancien_ref)\n                if not self.DBcible.ReqMAJ(table, [(champ, nouvel_ref)], pk, nouvel_id, commit=False):\n                    raise RuntimeError("Réparation impossible de %s.%s pour ID %r" % (table, champ, nouvel_id))\n            if references_a_reparer:\n                self.rapport.append({"table": None, "references_differees": len(references_a_reparer),\n                                     "statut": "preparee"})\n            self.DBcible.Commit()\n'''
if old not in s:
    raise SystemExit('boucle Executer introuvable')
s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')
