from pathlib import Path

p=Path('noethys/Utils/UTILS_Migration_base.py')
s=p.read_text(encoding='utf-8')

anchor='''REFERENCES_COEUR = {\n'''
insert='''PERIMETRES_MIGRATION = {\n    "dossiers": [\n        "familles", "individus", "comptes_payeurs", "rattachements",\n        "activites", "groupes", "inscriptions", "consommations",\n        "contrats", "contrats_tarifs", "questionnaire_reponses", "cotisations",\n    ],\n    "facturation": [\n        "familles", "comptes_payeurs", "factures", "prestations",\n        "reglements", "ventilation",\n    ],\n    "tarification": [\n        "activites", "categories_tarifs", "noms_tarifs", "tarifs", "tarifs_lignes",\n    ],\n}\n\n\n'''
if 'PERIMETRES_MIGRATION = {' not in s:
    s=s.replace(anchor, insert+anchor, 1)

s=s.replace('''    "prestations": ["comptes_payeurs"],\n''','''    "prestations": ["comptes_payeurs", "factures"],\n''',1)

old='''class PlanMigration(object):\n    def __init__(self, analyse, dependances=None, cles_primaires=None, references=None):\n        self.analyse = analyse\n        self.dependances = dependances or DEPENDANCES_COEUR\n        self.cles_primaires = cles_primaires or CLES_PRIMAIRES_COEUR\n        self.references = references or REFERENCES_COEUR\n'''
new='''class PlanMigration(object):\n    def __init__(self, analyse, dependances=None, cles_primaires=None, references=None, tables=None):\n        self.analyse = analyse\n        self.dependances = dependances or DEPENDANCES_COEUR\n        self.cles_primaires = cles_primaires or CLES_PRIMAIRES_COEUR\n        self.references = references or REFERENCES_COEUR\n        self.tables = self._resoudre_tables(tables)\n\n    def _resoudre_tables(self, tables):\n        if tables is None:\n            return None\n        if isinstance(tables, str):\n            tables = PERIMETRES_MIGRATION.get(tables, [tables])\n        selection = set(tables)\n        # Ferme automatiquement le périmètre sur toutes ses dépendances connues.\n        a_traiter = list(selection)\n        while a_traiter:\n            table = a_traiter.pop()\n            for dep in self.dependances.get(table, []):\n                if dep not in selection:\n                    selection.add(dep)\n                    a_traiter.append(dep)\n        return selection\n'''
if old not in s:
    raise SystemExit('PlanMigration init introuvable')
s=s.replace(old,new,1)

old='''        inventaire = {item["table"]: item for item in self.analyse.Inventaire(inclure_vides=False)}\n        schema = self.analyse.ComparerSchemas()\n        tables_source, tables_cible = set(inventaire), set(schema["tables_cible"])\n'''
new='''        inventaire = {item["table"]: item for item in self.analyse.Inventaire(inclure_vides=False)}\n        schema = self.analyse.ComparerSchemas()\n        tables_source, tables_cible = set(inventaire), set(schema["tables_cible"])\n        if self.tables is not None:\n            tables_source &= self.tables\n'''
if old not in s:
    raise SystemExit('Construire prelude introuvable')
s=s.replace(old,new,1)

old='''    def __init__(self, DBsource, DBcible, plan=None, mapping=None, references=None):\n        self.DBsource = DBsource\n        self.DBcible = DBcible\n        self.analyse = AnalyseMigration(DBsource, DBcible)\n        self.planificateur = plan or PlanMigration(self.analyse)\n'''
new='''    def __init__(self, DBsource, DBcible, plan=None, mapping=None, references=None, tables=None):\n        self.DBsource = DBsource\n        self.DBcible = DBcible\n        self.analyse = AnalyseMigration(DBsource, DBcible)\n        self.planificateur = plan or PlanMigration(self.analyse, references=references, tables=tables)\n'''
if old not in s:
    raise SystemExit('Moteur init introuvable')
s=s.replace(old,new,1)

# Ajoute le périmètre effectif au rapport de simulation.
old='''        simulation["lignes_lues"] = compte\n        simulation["erreurs"] = erreurs\n'''
new='''        simulation["lignes_lues"] = compte\n        simulation["perimetre"] = [item["table"] for item in simulation["plan"]["tables_migrables"]]\n        simulation["erreurs"] = erreurs\n'''
if old not in s:
    raise SystemExit('simulation tail introuvable')
s=s.replace(old,new,1)

p.write_text(s,encoding='utf-8')
