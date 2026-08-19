# Noe-002 - OL_Reglements SQL strict migration plan

## Objectif

Remplacer la requête utilisant un `GROUP BY` implicite par une requête compatible avec MySQL/MariaDB en mode `ONLY_FULL_GROUP_BY`.

## Constat

`noethys/Ol/OL_Reglements.py` utilise une agrégation :

```sql
SUM(ventilation.montant) AS total_ventilation
```

avec un regroupement uniquement sur :

```sql
GROUP BY reglements.IDreglement
```

## Stratégie retenue

Ne pas ajouter toutes les colonnes du SELECT dans le GROUP BY.

Utiliser une table dérivée calculant les ventilations :

```sql
SELECT ...
LEFT JOIN (
    SELECT IDreglement, SUM(montant) AS total_ventilation
    FROM ventilation
    GROUP BY IDreglement
) ventilation_totaux
ON ventilation_totaux.IDreglement = reglements.IDreglement
```

## Vérifications nécessaires

- même nombre de lignes affichées ;
- même montant ventilé ;
- gestion des règlements sans ventilation ;
- compatibilité SQLite/MySQL existante ;
- test sur copie de base réelle.

Aucun changement métier prévu.