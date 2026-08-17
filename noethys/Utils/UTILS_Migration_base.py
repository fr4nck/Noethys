#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Migration contrôlée d'une base Noethys vers une base neuve.

Le module sépare analyse, planification et exécution. La source n'est jamais
modifiée. L'exécution réelle sur la cible est transactionnelle et précédée par
une simulation explicite.
"""

from __future__ import unicode_literals


DEPENDANCES_COEUR = {
    "regimes": [],
    "caisses": ["regimes"],
    "banques": [],
    "secteurs": [],
    "categories_travail": [],
    "medecins": [],
    "types_sieste": [],
    "utilisateurs": [],
    "restaurateurs": [],
    "types_quotients": [],
    "produits_categories": [],
    "produits": ["produits_categories"],
    "types_cotisations": [],
    "unites_cotisations": ["types_cotisations"],
    "depots_cotisations": [],
    "questionnaire_categories": [],
    "questionnaire_questions": ["questionnaire_categories"],
    "questionnaire_choix": ["questionnaire_questions"],
    "individus": ["secteurs", "categories_travail", "medecins", "types_sieste"],
    "familles": ["individus", "caisses", "banques"],
    "activites": [],
    "categories_tarifs": ["activites"],
    "noms_tarifs": ["activites", "categories_tarifs"],
    "tarifs": ["activites", "categories_tarifs", "noms_tarifs", "types_quotients", "evenements", "produits"],
    "groupes": ["activites"],
    "unites": ["activites", "restaurateurs"],
    "evenements": ["activites", "unites", "groupes"],
    "comptes_payeurs": ["familles", "individus"],
    "rattachements": ["familles", "individus"],
    "inscriptions": ["familles", "individus", "activites", "groupes", "categories_tarifs", "comptes_payeurs"],
    "factures": ["comptes_payeurs"],
    "contrats": ["individus", "inscriptions", "tarifs", "activites"],
    "contrats_tarifs": ["contrats"],
    "prestations": ["comptes_payeurs", "activites", "tarifs", "factures", "familles", "individus", "categories_tarifs", "contrats"],
    "reglements": ["comptes_payeurs"],
    "consommations": ["individus", "inscriptions", "activites", "unites", "groupes", "utilisateurs", "categories_tarifs", "comptes_payeurs", "evenements"],
    "ventilation": ["reglements", "prestations", "comptes_payeurs"],
    "cotisations": ["familles", "individus", "types_cotisations", "unites_cotisations", "utilisateurs", "depots_cotisations"],
    "questionnaire_reponses": ["familles", "individus", "inscriptions", "questionnaire_questions"],
}

CLES_PRIMAIRES_COEUR = {
    "regimes": "IDregime",
    "caisses": "IDcaisse",
    "banques": "IDbanque",
    "secteurs": "IDsecteur",
    "categories_travail": "IDcategorie",
    "medecins": "IDmedecin",
    "types_sieste": "IDtype_sieste",
    "utilisateurs": "IDutilisateur",
    "restaurateurs": "IDrestaurateur",
    "types_quotients": "IDtype_quotient",
    "produits_categories": "IDcategorie",
    "produits": "IDproduit",
    "types_cotisations": "IDtype_cotisation",
    "unites_cotisations": "IDunite_cotisation",
    "depots_cotisations": "IDdepot_cotisation",
    "questionnaire_categories": "IDcategorie",
    "questionnaire_questions": "IDquestion",
    "questionnaire_choix": "IDchoix",
    "locations": "IDlocation",
    "locations_demandes": "IDdemande",
    "familles": "IDfamille",
    "individus": "IDindividu",
    "comptes_payeurs": "IDcompte_payeur",
    "rattachements": "IDrattachement",
    "activites": "IDactivite",
    "groupes": "IDgroupe",
    "unites": "IDunite",
    "evenements": "IDevenement",
    "categories_tarifs": "IDcategorie_tarif",
    "noms_tarifs": "IDnom_tarif",
    "tarifs": "IDtarif",
    "tarifs_lignes": "IDligne",
    "inscriptions": "IDinscription",
    "consommations": "IDconso",
    "prestations": "IDprestation",
    "factures": "IDfacture",
    "reglements": "IDreglement",
    "ventilation": "IDventilation",
    "cotisations": "IDcotisation",
    "questionnaire_reponses": "IDreponse",
    "contrats": "IDcontrat",
    "contrats_tarifs": "IDcontrat_tarif",
}

# Clés étrangères dont le remapping est suffisamment explicite pour autoriser
# une migration automatique. Toute autre référence potentielle reste en revue.
PERIMETRES_MIGRATION = {
    "dossiers": [
        "familles", "individus", "comptes_payeurs", "rattachements",
        "activites", "groupes", "unites", "evenements",
        "categories_tarifs", "noms_tarifs", "tarifs",
        "inscriptions", "consommations", "contrats", "contrats_tarifs",
        "questionnaire_categories", "questionnaire_questions", "questionnaire_choix",
        "questionnaire_reponses", "cotisations",
    ],
    "facturation": [
        "familles", "comptes_payeurs", "factures", "prestations",
        "reglements", "ventilation",
    ],
    "tarification": [
        "activites", "categories_tarifs", "noms_tarifs", "tarifs", "tarifs_lignes",
    ],
}


# Registre unique des références métier. La stratégie ``remapper`` exige que
# la cible ait déjà été migrée, ``differer`` répare la FK avant le commit, et
# ``conserver`` documente une valeur issue d'un catalogue applicatif plutôt que
# d'une table de la base. ``polymorphe`` choisit la cible depuis un discriminateur.
REGISTRE_REFERENCES_METIER = {
    "caisses": {"IDregime": ("regimes", "remapper")},
    "individus": {
        "IDcivilite": (None, "conserver"),
        "IDnationalite": (None, "conserver"),
        "IDpays_naiss": (None, "conserver"),
        "adresse_auto": ("individus", "differer"),
        "IDsecteur": ("secteurs", "remapper"),
        "IDcategorie_travail": ("categories_travail", "remapper"),
        "IDmedecin": ("medecins", "remapper"),
        "IDtype_sieste": ("types_sieste", "remapper"),
    },
    "familles": {
        "IDcompte_payeur": ("comptes_payeurs", "differer"),
        "IDcaisse": ("caisses", "remapper"),
        "allocataire": ("individus", "remapper"),
        "prelevement_banque": ("banques", "remapper"),
        "prelevement_individu": ("individus", "remapper"),
        "titulaire_helios": ("individus", "remapper"),
        "tiers_solidaire": ("individus", "remapper"),
    },
    "produits": {"IDcategorie": "produits_categories"},
    "unites_cotisations": {"IDtype_cotisation": "types_cotisations"},
    "questionnaire_questions": {"IDcategorie": "questionnaire_categories"},
    "questionnaire_choix": {"IDquestion": "questionnaire_questions"},
    "comptes_payeurs": {"IDfamille": "familles", "IDindividu": "individus"},
    "rattachements": {
        "IDfamille": "familles", "IDindividu": "individus",
        "IDcategorie": (None, "conserver"),
    },
    "groupes": {"IDactivite": "activites"},
    "unites": {"IDactivite": "activites", "IDrestaurateur": "restaurateurs"},
    "evenements": {"IDactivite": "activites", "IDunite": "unites", "IDgroupe": "groupes"},
    "categories_tarifs": {"IDactivite": "activites"},
    "noms_tarifs": {"IDactivite": "activites", "IDcategorie_tarif": "categories_tarifs"},
    "tarifs": {
        "IDactivite": "activites", "IDcategorie_tarif": "categories_tarifs",
        "IDnom_tarif": "noms_tarifs", "IDtype_quotient": "types_quotients",
        "IDevenement": "evenements", "IDproduit": "produits",
    },
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
        "IDcompte_payeur": "comptes_payeurs", "IDprestation": ("prestations", "differer"),
        "IDevenement": "evenements",
    },
    "prestations": {
        "IDcompte_payeur": "comptes_payeurs", "IDactivite": "activites", "IDtarif": "tarifs",
        "IDfacture": "factures", "IDfamille": "familles", "IDindividu": "individus",
        "IDcategorie_tarif": "categories_tarifs", "reglement_frais": ("reglements", "differer"),
        "IDcontrat": "contrats",
    },
    "factures": {"IDcompte_payeur": "comptes_payeurs"},
    "reglements": {"IDcompte_payeur": "comptes_payeurs"},
    "ventilation": {
        "IDreglement": "reglements", "IDprestation": "prestations",
        "IDcompte_payeur": "comptes_payeurs",
    },
    "cotisations": {
        "IDfamille": "familles", "IDindividu": "individus",
        "IDtype_cotisation": "types_cotisations",
        "IDunite_cotisation": "unites_cotisations",
        "IDutilisateur": "utilisateurs", "IDdepot_cotisation": "depots_cotisations",
        "IDprestation": "prestations",
    },
    "questionnaire_reponses": {
        "IDquestion": "questionnaire_questions", "IDfamille": "familles",
        "IDindividu": "individus",
        "IDdonnee": ({
            "discriminateur": "type",
            "cibles": {
                "famille": "familles", "individu": "individus",
                "inscription": "inscriptions", "produit": "produits",
                "categorie_produit": "produits_categories", "location": "locations",
                "location_demande": "locations_demandes",
            },
        }, "polymorphe"),
    },
    "contrats": {
        "IDindividu": "individus", "IDinscription": "inscriptions",
        "IDtarif": "tarifs", "IDactivite": "activites",
    },
    "contrats_tarifs": {"IDcontrat": "contrats"},
}

# Les entrées historiques ci-dessus utilisent des tuples. Les références déjà
# prises en charge avant l'introduction du registre sont normalisées ici afin
# de conserver l'API publique REFERENCES_COEUR.
for _table, _champs in list(REGISTRE_REFERENCES_METIER.items()):
    for _champ, _description in list(_champs.items()):
        if not isinstance(_description, tuple):
            _champs[_champ] = (_description, "remapper")

REFERENCES_COEUR = {
    table: {champ: description[0] for champ, description in champs.items()
            if description[1] in ("remapper", "differer")}
    for table, champs in REGISTRE_REFERENCES_METIER.items()
}

REFERENCES_PRESERVEES = {
    table: set(champ for champ, description in champs.items() if description[1] == "conserver")
    for table, champs in REGISTRE_REFERENCES_METIER.items()
}

REFERENCES_POLYMORPHES = {
    table: {champ: description[0] for champ, description in champs.items()
            if description[1] == "polymorphe"}
    for table, champs in REGISTRE_REFERENCES_METIER.items()
}

# Les noms non conventionnels doivent rester détectables même si une entrée du
# registre est retirée par erreur ou oubliée dans une configuration sur mesure.
NOMS_REFERENCES_HISTORIQUES = frozenset([
    "adresse_auto", "allocataire", "prelevement_banque", "prelevement_individu",
    "titulaire_helios", "tiers_solidaire", "reglement_frais",
])

# Références qui peuvent pointer vers une table migrée plus tard. Elles sont
# insérées à NULL puis réparées dans la même transaction avant le commit final.
REFERENCES_DIFFEREES = {
    table: {champ: description[0] for champ, description in champs.items()
            if description[1] == "differer"}
    for table, champs in REGISTRE_REFERENCES_METIER.items()
}


class MappingIDs(object):
    def __init__(self):
        self._mapping = {}

    def Ajouter(self, table, ancien_id, nouvel_id):
        self._mapping.setdefault(table, {})[ancien_id] = nouvel_id

    def Get(self, table, ancien_id, defaut=None):
        return self._mapping.get(table, {}).get(ancien_id, defaut)

    def Existe(self, table, ancien_id):
        return ancien_id in self._mapping.get(table, {})

    def GetTable(self, table):
        return dict(self._mapping.get(table, {}))

    def Resume(self):
        return {table: len(valeurs) for table, valeurs in self._mapping.items()}


class AnalyseMigration(object):
    def __init__(self, DBsource, DBcible=None):
        self.DBsource = DBsource
        self.DBcible = DBcible

    def _liste_tables(self, DB):
        if DB is None:
            return []
        return sorted([ligne[0] for ligne in DB.GetListeTables()])

    def _liste_champs(self, DB, table):
        return [nom for nom, _type in DB.GetListeChamps2(table)]

    def _compte_lignes(self, DB, table):
        if not DB.ExecuterReq("SELECT COUNT(*) FROM %s;" % table):
            return None
        resultat = DB.ResultatReq()
        if not resultat:
            return 0
        return int(resultat[0][0])

    def Inventaire(self, inclure_vides=True):
        inventaire = []
        for table in self._liste_tables(self.DBsource):
            nbre = self._compte_lignes(self.DBsource, table)
            if inclure_vides or nbre:
                inventaire.append({"table": table, "nbre": nbre, "champs": self._liste_champs(self.DBsource, table)})
        return inventaire

    def ComparerSchemas(self):
        if self.DBcible is None:
            tables_source = self._liste_tables(self.DBsource)
            return {"tables_source": tables_source, "tables_cible": [], "tables_communes": [],
                    "tables_source_uniquement": tables_source, "tables_cible_uniquement": [], "champs": {}}
        source = set(self._liste_tables(self.DBsource))
        cible = set(self._liste_tables(self.DBcible))
        communes = sorted(source & cible)
        details = {}
        for table in communes:
            champs_source = set(self._liste_champs(self.DBsource, table))
            champs_cible = set(self._liste_champs(self.DBcible, table))
            details[table] = {
                "communs": sorted(champs_source & champs_cible),
                "source_uniquement": sorted(champs_source - champs_cible),
                "cible_uniquement": sorted(champs_cible - champs_source),
            }
        return {"tables_source": sorted(source), "tables_cible": sorted(cible), "tables_communes": communes,
                "tables_source_uniquement": sorted(source - cible), "tables_cible_uniquement": sorted(cible - source),
                "champs": details}

    def Resume(self):
        inventaire = self.Inventaire(inclure_vides=False)
        comparaison = self.ComparerSchemas()
        return {"tables_non_vides": len(inventaire),
                "lignes_source": sum(item["nbre"] for item in inventaire if item["nbre"] is not None),
                "inventaire": inventaire, "schema": comparaison}


class PlanMigration(object):
    def __init__(self, analyse, dependances=None, cles_primaires=None, references=None, tables=None,
                 references_preservees=None, references_polymorphes=None,
                 noms_references_historiques=None):
        self.analyse = analyse
        self.dependances = DEPENDANCES_COEUR if dependances is None else dependances
        self.cles_primaires = CLES_PRIMAIRES_COEUR if cles_primaires is None else cles_primaires
        self.references = REFERENCES_COEUR if references is None else references
        self.references_preservees = (REFERENCES_PRESERVEES if references_preservees is None
                                      else references_preservees)
        self.references_polymorphes = (REFERENCES_POLYMORPHES if references_polymorphes is None
                                       else references_polymorphes)
        self.noms_references_historiques = (NOMS_REFERENCES_HISTORIQUES
                                            if noms_references_historiques is None
                                            else frozenset(noms_references_historiques))
        self.tables = self._resoudre_tables(tables)

    def _resoudre_tables(self, tables):
        if tables is None:
            return None
        if isinstance(tables, str):
            tables = PERIMETRES_MIGRATION.get(tables, [tables])
        selection = set(tables)
        # Ferme automatiquement le périmètre sur toutes ses dépendances connues.
        a_traiter = list(selection)
        while a_traiter:
            table = a_traiter.pop()
            for dep in self.dependances.get(table, []):
                if dep not in selection:
                    selection.add(dep)
                    a_traiter.append(dep)
        return selection

    def _ordre_topologique(self, tables):
        tables = set(tables)
        ordre, restant = [], set(tables)
        while restant:
            avances = []
            for table in sorted(restant):
                deps = [d for d in self.dependances.get(table, []) if d in tables]
                if all(dep in ordre for dep in deps):
                    avances.append(table)
            if not avances:
                return ordre, sorted(restant)
            for table in avances:
                ordre.append(table)
                restant.remove(table)
        return ordre, []

    def Construire(self):
        inventaire = {item["table"]: item for item in self.analyse.Inventaire(inclure_vides=False)}
        schema = self.analyse.ComparerSchemas()
        tables_source, tables_cible = set(inventaire), set(schema["tables_cible"])
        if self.tables is not None:
            tables_source &= self.tables
        migrables, revue, ignorees = [], [], []
        for table in sorted(tables_source):
            item = inventaire[table]
            if table not in tables_cible:
                revue.append({"table": table, "raison": "table_absente_cible", "nbre": item["nbre"]}); continue
            if table not in self.dependances or table not in self.cles_primaires:
                revue.append({"table": table, "raison": "mapping_non_decrit", "nbre": item["nbre"]}); continue
            details = schema["champs"].get(table, {})
            if details.get("source_uniquement", []):
                revue.append({"table": table, "raison": "champs_source_sans_cible",
                              "champs": details["source_uniquement"], "nbre": item["nbre"]}); continue
            pk = self.cles_primaires[table]
            refs_connues = set(self.references.get(table, {}))
            refs_preservees = set(self.references_preservees.get(table, set()))
            refs_polymorphes = set(self.references_polymorphes.get(table, {}))
            refs_non_decrites = [champ for champ in details.get("communs", [])
                                  if champ != pk
                                  and (champ.startswith("ID") or champ in self.noms_references_historiques)
                                  and champ not in refs_connues and champ not in refs_preservees
                                  and champ not in refs_polymorphes]
            if refs_non_decrites:
                revue.append({"table": table, "raison": "references_non_decrites",
                              "champs": refs_non_decrites, "nbre": item["nbre"]}); continue
            migrables.append(table)
        ordre, cycles = self._ordre_topologique(migrables)
        for table in cycles:
            revue.append({"table": table, "raison": "dependance_cyclique_ou_inconnue", "nbre": inventaire[table]["nbre"]})
        for table in sorted(tables_cible - tables_source):
            ignorees.append({"table": table, "raison": "absente_source"})
        return {"ordre": ordre,
                "tables_migrables": [{"table": table, "nbre": inventaire[table]["nbre"],
                    "cle_primaire": self.cles_primaires.get(table), "dependances": list(self.dependances.get(table, [])),
                    "strategie": "remap_ids" if self.dependances.get(table) else "copie_controlee"} for table in ordre],
                "tables_revue": revue, "tables_ignorees": ignorees}

    def Simuler(self):
        plan = self.Construire()
        return {"ecriture_effectuee": False, "pret": len(plan["tables_revue"]) == 0,
                "lignes_migrables": sum(item["nbre"] for item in plan["tables_migrables"] if item["nbre"] is not None),
                "lignes_a_revoir": sum(item.get("nbre", 0) or 0 for item in plan["tables_revue"]), "plan": plan}


class MoteurMigration(object):
    """Exécute une migration source -> cible avec rollback global sur la cible."""

    def __init__(self, DBsource, DBcible, plan=None, mapping=None, references=None, tables=None,
                 references_differees=None, references_preservees=None,
                 references_polymorphes=None, noms_references_historiques=None):
        self.DBsource = DBsource
        self.DBcible = DBcible
        self.analyse = AnalyseMigration(DBsource, DBcible)
        self.references = REFERENCES_COEUR if references is None else references
        self.references_preservees = (REFERENCES_PRESERVEES if references_preservees is None
                                      else references_preservees)
        self.references_polymorphes = (REFERENCES_POLYMORPHES if references_polymorphes is None
                                       else references_polymorphes)
        self.planificateur = plan or PlanMigration(
            self.analyse, references=self.references, tables=tables,
            references_preservees=self.references_preservees,
            references_polymorphes=self.references_polymorphes,
            noms_references_historiques=noms_references_historiques)
        self.mapping = mapping or MappingIDs()
        self.references_differees = (REFERENCES_DIFFEREES if references_differees is None
                                     else references_differees)
        self.rapport = []

    def _rollback(self):
        try:
            self.DBcible.connexion.rollback()
        except Exception:
            pass

    def _lire_table(self, table, champs):
        requete = "SELECT %s FROM %s;" % (", ".join(champs), table)
        if not self.DBsource.ExecuterReq(requete):
            return None
        return self.DBsource.ResultatReq()

    def _remapper_ligne(self, table, champs, valeurs, cle_primaire):
        donnees = dict(zip(champs, valeurs))
        ancien_id = donnees.pop(cle_primaire, None)
        differes = []
        for champ, table_ref in self.references.get(table, {}).items():
            if champ not in donnees or donnees[champ] is None:
                continue
            ancien_ref = donnees[champ]
            if self.mapping.Existe(table_ref, ancien_ref):
                donnees[champ] = self.mapping.Get(table_ref, ancien_ref)
                continue
            if self.references_differees.get(table, {}).get(champ) == table_ref:
                donnees[champ] = None
                differes.append((champ, table_ref, ancien_ref))
                continue
            raise ValueError("Référence non migrée %s.%s=%r vers %s" % (table, champ, ancien_ref, table_ref))
        for champ, configuration in self.references_polymorphes.get(table, {}).items():
            if champ not in donnees or donnees[champ] is None:
                continue
            discriminateur = configuration["discriminateur"]
            valeur_discriminante = donnees.get(discriminateur)
            table_ref = configuration["cibles"].get(valeur_discriminante)
            if table_ref is None:
                raise ValueError("Type de référence polymorphe inconnu %s.%s=%r (%s=%r)" %
                                 (table, champ, donnees[champ], discriminateur, valeur_discriminante))
            ancien_ref = donnees[champ]
            if not self.mapping.Existe(table_ref, ancien_ref):
                raise ValueError("Référence polymorphe non migrée %s.%s=%r vers %s" %
                                 (table, champ, ancien_ref, table_ref))
            donnees[champ] = self.mapping.Get(table_ref, ancien_ref)
        return ancien_id, donnees, differes

    def Simuler(self):
        """Valide lecture, registre et intégrité des FK sans écriture cible."""
        simulation = self.planificateur.Simuler()
        if not simulation["pret"]:
            return simulation
        erreurs, compte, identifiants_source = [], 0, {}
        schema = self.analyse.ComparerSchemas()
        tables_plan = set(simulation["plan"]["ordre"])

        def get_identifiants_source(table_ref):
            if table_ref in identifiants_source:
                return identifiants_source[table_ref]
            pk_ref = self.planificateur.cles_primaires.get(table_ref)
            if not pk_ref:
                identifiants_source[table_ref] = None
                return None
            if table_ref not in schema["tables_source"]:
                identifiants_source[table_ref] = set()
                return identifiants_source[table_ref]
            lignes_ref = self._lire_table(table_ref, [pk_ref])
            if lignes_ref is None:
                identifiants_source[table_ref] = None
            else:
                identifiants_source[table_ref] = set(ligne[0] for ligne in lignes_ref)
            return identifiants_source[table_ref]

        for item in simulation["plan"]["tables_migrables"]:
            table, pk = item["table"], item["cle_primaire"]
            champs = schema["champs"][table]["communs"]
            if pk not in champs:
                erreurs.append({"table": table, "erreur": "cle_primaire_absente"}); continue
            lignes = self._lire_table(table, champs)
            if lignes is None:
                erreurs.append({"table": table, "erreur": "lecture_source"}); continue
            refs = self.references.get(table, {})
            indexes = {champ: index for index, champ in enumerate(champs)}
            for champ, table_ref in refs.items():
                if champ not in indexes:
                    continue
                index = indexes[champ]
                ids_source = get_identifiants_source(table_ref)
                for valeurs in lignes:
                    ancien_ref = valeurs[index]
                    if ancien_ref is None or self.mapping.Existe(table_ref, ancien_ref):
                        continue
                    if table_ref not in tables_plan:
                        erreurs.append({"table": table, "champ": champ,
                                        "erreur": "reference_hors_perimetre",
                                        "cible": table_ref, "valeur": ancien_ref})
                        break
                    if ids_source is None:
                        erreurs.append({"table": table, "champ": champ,
                                        "erreur": "reference_cible_non_decrite",
                                        "cible": table_ref, "valeur": ancien_ref})
                        break
                    if ancien_ref not in ids_source:
                        erreurs.append({"table": table, "champ": champ,
                                        "erreur": "reference_source_absente",
                                        "cible": table_ref, "valeur": ancien_ref})
                        break
            for champ, configuration in self.references_polymorphes.get(table, {}).items():
                discriminateur = configuration["discriminateur"]
                if champ not in indexes:
                    continue
                if discriminateur not in indexes:
                    erreurs.append({"table": table, "champ": champ,
                                    "erreur": "configuration_polymorphe_incomplete",
                                    "discriminateur": discriminateur})
                    continue
                index_ref, index_discriminateur = indexes[champ], indexes[discriminateur]
                for valeurs in lignes:
                    ancien_ref = valeurs[index_ref]
                    if ancien_ref is None:
                        continue
                    valeur_discriminante = valeurs[index_discriminateur]
                    table_ref = configuration["cibles"].get(valeur_discriminante)
                    if table_ref is None:
                        erreurs.append({"table": table, "champ": champ,
                                        "erreur": "type_reference_polymorphe_inconnu",
                                        "discriminateur": discriminateur,
                                        "type": valeur_discriminante, "valeur": ancien_ref})
                        continue
                    if self.mapping.Existe(table_ref, ancien_ref):
                        continue
                    if table_ref not in tables_plan:
                        erreurs.append({"table": table, "champ": champ,
                                        "erreur": "reference_hors_perimetre",
                                        "cible": table_ref, "valeur": ancien_ref,
                                        "type": valeur_discriminante})
                        continue
                    ids_source = get_identifiants_source(table_ref)
                    if ids_source is None:
                        erreurs.append({"table": table, "champ": champ,
                                        "erreur": "reference_cible_non_decrite",
                                        "cible": table_ref, "valeur": ancien_ref,
                                        "type": valeur_discriminante})
                    elif ancien_ref not in ids_source:
                        erreurs.append({"table": table, "champ": champ,
                                        "erreur": "reference_source_absente",
                                        "cible": table_ref, "valeur": ancien_ref,
                                        "type": valeur_discriminante})
            compte += len(lignes)
        simulation["lignes_lues"] = compte
        simulation["perimetre"] = [item["table"] for item in simulation["plan"]["tables_migrables"]]
        simulation["erreurs"] = erreurs
        simulation["pret"] = simulation["pret"] and not erreurs
        return simulation

    def Executer(self):
        """Migre toutes les tables autorisées puis commit une seule fois."""
        simulation = self.Simuler()
        if not simulation.get("pret"):
            return {"succes": False, "commit": False, "simulation": simulation, "rapport": []}

        schema = self.analyse.ComparerSchemas()
        self.rapport = []
        references_a_reparer = []
        try:
            for item in simulation["plan"]["tables_migrables"]:
                table, pk = item["table"], item["cle_primaire"]
                champs = schema["champs"][table]["communs"]
                lignes = self._lire_table(table, champs)
                if lignes is None:
                    raise RuntimeError("Lecture impossible de %s" % table)
                nb = 0
                for valeurs in lignes:
                    ancien_id, donnees, differes = self._remapper_ligne(table, champs, valeurs, pk)
                    liste_donnees = [(champ, donnees[champ]) for champ in champs if champ != pk and champ in donnees]
                    nouvel_id = self.DBcible.ReqInsert(table, liste_donnees, commit=False)
                    if nouvel_id is None:
                        raise RuntimeError("Insertion impossible dans %s (ID source %r)" % (table, ancien_id))
                    if ancien_id is not None:
                        self.mapping.Ajouter(table, ancien_id, nouvel_id)
                    for champ, table_ref, ancien_ref in differes:
                        references_a_reparer.append((table, pk, nouvel_id, champ, table_ref, ancien_ref))
                    nb += 1
                self.rapport.append({"table": table, "lignes": nb, "statut": "preparee"})

            # Répare les références avant tout commit : aucune FK différée ne peut
            # rester orpheline dans la base cible.
            for table, pk, nouvel_id, champ, table_ref, ancien_ref in references_a_reparer:
                if not self.mapping.Existe(table_ref, ancien_ref):
                    raise ValueError("Référence différée non migrée %s.%s=%r vers %s" %
                                     (table, champ, ancien_ref, table_ref))
                nouvel_ref = self.mapping.Get(table_ref, ancien_ref)
                if not self.DBcible.ReqMAJ(table, [(champ, nouvel_ref)], pk, nouvel_id, commit=False):
                    raise RuntimeError("Réparation impossible de %s.%s pour ID %r" % (table, champ, nouvel_id))
            if references_a_reparer:
                self.rapport.append({"table": None, "references_differees": len(references_a_reparer),
                                     "statut": "preparee"})
            self.DBcible.Commit()
        except Exception as err:
            self._rollback()
            self.rapport.append({"table": None, "statut": "rollback", "erreur": str(err)})
            return {"succes": False, "commit": False, "simulation": simulation,
                    "mapping": self.mapping.Resume(), "rapport": list(self.rapport)}

        for item in self.rapport:
            item["statut"] = "migree"
        return {"succes": True, "commit": True, "simulation": simulation,
                "mapping": self.mapping.Resume(), "rapport": list(self.rapport)}
