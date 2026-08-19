# Noe-004 — Audit des index de base de données

## Objectif

Identifier les index susceptibles d'améliorer les performances de Noethys sans modifier le modèle métier ni imposer de migration aux bases existantes.

L'audit est **non destructif** : aucun `CREATE INDEX`, `ALTER` ou `DROP` n'est exécuté par l'outil.

## Contraintes de compatibilité

- conserver les bases Noethys existantes telles quelles ;
- ne déclencher aucune migration implicite au démarrage ;
- rester compatible SQLite et MySQL/MariaDB anciens, notamment les installations 5.5 encore utilisées ;
- mesurer le bénéfice avant d'ajouter un index ;
- tenir compte du coût d'écriture, de stockage et de maintenance des index.

## Index actuellement déclarés par Noethys

La définition courante contient notamment :

| Index | Colonnes |
|---|---|
| `index_reglements` | `reglements (IDcompte_payeur)` |
| `index_payeurs` | `payeurs (IDcompte_payeur)` |
| `index_prestations` | `prestations (IDcompte_payeur)` |
| `index_utilisateurs` | `utilisateurs (identifiant, mdp)` |
| `index_familles` | `familles (internet_actif, internet_identifiant)` |
| `index_individus` | `individus (nom)` |
| `index_rattachements` | `rattachements (IDindividu, IDfamille)` |
| `index_inscriptions` | `inscriptions (IDindividu, IDfamille, IDactivite)` |
| `index_comptes_payeurs` | `comptes_payeurs (IDfamille)` |
| `index_ventilation` | `ventilation (IDreglement, IDprestation)` |
| `index_consommations` | `consommations (IDindividu, IDinscription, IDactivite, date, etat)` |
| `index_categories_tarifs` | `categories_tarifs (IDactivite)` |
| `index_pieces_manquantes` | `pieces_manquantes (IDfamille, IDindividu, IDpiece)` |
| `index_locations` | `locations (IDfamille, IDproduit, date_debut, date_fin)` |
| `index_demandes` | `demandes (IDfamille, IDindividu, IDactivite, date_debut, date_fin)` |
| `index_mandats` | `mandats (rum, IDfamille)` |
| `index_messages` | `messages (IDcategorie, IDtype, IDfamille, IDindividu, date_saisie, afficher)` |
| `index_logs` | `logs (IDutilisateur, IDindividu, IDfamille, date)` |
| `index_portail_actions` | `portail_actions (IDfamille, IDindividu, IDcategorie, IDaction, date)` |
| `index_portail_periodes` | `portail_periodes (IDperiode, IDactivite, date_debut, date_fin)` |
| `index_questionnaire_familles` | `questionnaire_familles (IDquestion, IDfamille)` |
| `index_questionnaire_individus` | `questionnaire_individus (IDquestion, IDindividu)` |

## Candidats prioritaires à mesurer

### P1 — `cotisations (IDprestation)`

Les exports comptables et le diagnostic Noe-003 utilisent `cotisations.IDprestation`. Le schéma historique ne déclare pas d'index commençant par cette colonne.

**Intérêt attendu :** accélérer les recherches prestation → cotisation et la détection des anomalies de prestations partagées.

### P1 — `prestations (IDfacture)`

Les traitements de facturation et les exports comptables utilisent régulièrement le lien prestation → facture. L'index historique de `prestations` commence par `IDcompte_payeur`.

**Intérêt attendu :** réduire le coût des recherches par facture sur les bases volumineuses.

### P2 — `ventilation (IDprestation)`

L'index existant est `ventilation (IDreglement, IDprestation)`. Il couvre bien les recherches commençant par `IDreglement`, mais pas une recherche dont le premier critère est uniquement `IDprestation`.

### P2 — `prestations (IDfamille)` et `prestations (IDactivite)`

Ces deux accès sont fréquents dans le code, mais il ne faut pas empiler des index unitaires sans gain démontré sur une base représentative.

## Outil de mesure

`scripts/audit_db_indexes.py` sait maintenant comparer les index déclarés avec ceux d'une base réelle **et mesurer les requêtes candidates en lecture seule**.

### Inventaire statique

```bash
python scripts/audit_db_indexes.py
```

### Copie SQLite

```bash
python scripts/audit_db_indexes.py \
  --sqlite copie.dat \
  --repeats 5 \
  --json noe004-sqlite.json
```

Le fichier est ouvert avec `mode=ro` et `PRAGMA query_only=ON`.

### Copie MySQL / MariaDB

Utiliser de préférence un compte `SELECT` uniquement sur une base de recette :

```bash
export NOETHYS_DB_PASSWORD='mot-de-passe'
python scripts/audit_db_indexes.py \
  --mysql-host 127.0.0.1 \
  --mysql-port 3306 \
  --mysql-database noethys_recette \
  --mysql-user noethys_recette_ro \
  --repeats 5 \
  --json noe004-mysql.json
```

L'outil lit `information_schema.statistics`, exécute `EXPLAIN`, lance de petits `SELECT COUNT(*)` répétés sur une valeur non nulle existante et termine la connexion sans commit.

## Résultats produits

Pour chaque candidat présent dans la base :

- présence ou absence d'un index dont le **préfixe gauche** couvre la colonne recherchée ;
- plan `EXPLAIN QUERY PLAN` sous SQLite ou `EXPLAIN` sous MySQL/MariaDB ;
- nombre de lignes correspondant à la valeur d'échantillon ;
- médiane et maximum du temps de lecture sur plusieurs répétitions.

La valeur métier choisie comme échantillon n'est pas exportée dans le rapport JSON.

## Comment interpréter les plans

### SQLite

Un plan contenant `SCAN <table>` sur une table volumineuse indique généralement qu'aucun index adapté n'est utilisé. `SEARCH ... USING INDEX` ou `USING COVERING INDEX` indique une recherche indexée.

### MySQL / MariaDB

À examiner principalement :

- `type` (`ALL` = scan complet, `ref`/`range`/`const` généralement plus favorable) ;
- `possible_keys` ;
- `key` réellement choisi ;
- `rows` estimées ;
- `Extra`.

Les anciennes versions de MySQL/MariaDB peuvent produire des estimations différentes des versions modernes ; la mesure sur la copie réellement représentative reste la référence.

## Méthode de décision avant toute création d'index

1. utiliser une **copie** d'une base représentative ;
2. exécuter l'audit et conserver le rapport JSON initial ;
3. relever les candidats avec scan complet et coût mesurable ;
4. seulement sur une copie de laboratoire, créer manuellement l'index candidat ;
5. relancer exactement le même audit ;
6. comparer plan et temps ;
7. vérifier l'impact sur les écritures/imports ;
8. ne retenir que les gains nets et reproductibles.

## Politique de déploiement

Noe-004 ne doit pas transformer silencieusement une ancienne base. Si des index supplémentaires sont finalement retenus, leur création devra passer par un mécanisme **explicite, documenté, idempotent et réversible**, avec contrôle préalable de leur existence.

## État

- inventaire des index déclarés : fait ;
- candidats query-driven : fait ;
- détection correcte du préfixe gauche des index composites : testée ;
- plans SQLite lecture seule : outillés ;
- plans MySQL/MariaDB lecture seule : outillés ;
- chronométrage répétable sans écriture : outillé ;
- modification du schéma : **aucune** ;
- mesures sur une copie de base réelle : **à faire dans la recette Noe-030** ;
- choix définitif des index : après mesures réelles.
