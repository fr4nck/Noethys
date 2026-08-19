# Noe-004 — Audit des index de base de données

## Objectif

Identifier les index susceptibles d'améliorer les performances de Noethys sans modifier le modèle métier ni imposer de migration aux bases existantes.

Cette première passe est **statique et non destructive** : aucun `CREATE INDEX` supplémentaire n'est exécuté par l'application.

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

**Constat :** les exports comptables Quadra/Cerig relient les cotisations aux prestations par `IDprestation`. La table `cotisations` possède une clé primaire sur `IDcotisation`, mais aucun index déclaré sur `IDprestation`.

**Intérêt attendu :** accélérer la recherche des cotisations associées à une prestation et la sous-requête utilisée pour rendre ces exports compatibles avec le SQL strict.

**Décision :** candidat fort, mais ne pas le créer automatiquement avant mesure sur une copie d'une base réelle.

### P1 — `prestations (IDfacture)`

**Constat :** les traitements de facturation et les exports comptables utilisent régulièrement le lien prestation → facture. L'index déclaré sur `prestations` porte actuellement uniquement sur `IDcompte_payeur`.

**Intérêt attendu :** réduire le coût des recherches et regroupements par facture sur les bases volumineuses.

**Décision :** mesurer par `EXPLAIN` et chronométrage avant ajout.

### P2 — accès à `ventilation` par `IDprestation`

L'index existant est `ventilation (IDreglement, IDprestation)`. Il est adapté aux recherches dont le premier critère est `IDreglement`, mais n'est pas équivalent à un index commençant par `IDprestation` pour les requêtes qui partent d'une prestation.

**Candidat :** `ventilation (IDprestation)` ou éventuellement un index composite adapté aux requêtes réellement observées.

**Décision :** ne rien ajouter tant que l'audit des requêtes ne confirme pas un accès fréquent et coûteux par `IDprestation` seul.

### P2 — clés de rattachement de `prestations`

À mesurer séparément selon les écrans les plus coûteux :

- `prestations (IDfamille)` ;
- `prestations (IDactivite)` ;
- combinaisons incluant une date lorsque les requêtes utilisent réellement ces colonnes ensemble.

Il ne faut pas empiler des index unitaires par précaution : les gains doivent être démontrés sur les parcours métier concernés.

## Méthode de validation avant toute modification

1. utiliser une **copie** d'une base représentative ;
2. relever la taille de la base et les volumes des tables concernées ;
3. relever le plan d'exécution avant modification (`EXPLAIN` / `EXPLAIN QUERY PLAN`) ;
4. chronométrer plusieurs exécutions de la requête ou du parcours métier ;
5. créer l'index explicitement sur la copie ;
6. refaire les mêmes mesures ;
7. vérifier le coût sur les insertions/modifications ;
8. ne retenir que les index apportant un gain net et reproductible.

## Politique de déploiement proposée

Noe-004 ne doit pas transformer silencieusement une ancienne base. Si des index supplémentaires sont retenus, leur création devra passer par un mécanisme **explicite, documenté, idempotent et réversible**, avec contrôle préalable de leur existence.

## État

- inventaire des index déclarés : fait ;
- premiers candidats identifiés : fait ;
- modification du schéma : **aucune** ;
- mesures sur base réelle : à faire ;
- choix définitif des index : après mesures.
