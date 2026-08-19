# Noe-003 — Invariant cotisation / prestation

## Question examinée

La réécriture SQL strict de `DLG_Export_compta` utilise une sous-requête :

```sql
SELECT IDprestation, MIN(IDcotisation) AS IDcotisation
FROM cotisations
WHERE IDprestation IS NOT NULL
GROUP BY IDprestation
```

Elle évite qu'une prestation soit dupliquée dans l'export si plusieurs lignes de `cotisations` référencent le même `IDprestation`.

La question restante était : **plusieurs cotisations partageant une même prestation constituent-elles un cas métier normal ?**

## Évidence dans le code historique

Le cycle de vie normal indique une relation métier **une cotisation → sa prestation** :

- à la création d'une cotisation facturée, `DLG_Saisie_cotisation` crée une nouvelle ligne dans `prestations` et conserve son `IDprestation` ;
- la cotisation enregistrée reçoit cet `IDprestation` ;
- lors de la modification, si `IDprestation` existe, la prestation correspondante est mise à jour ;
- lors de la suppression d'une cotisation, `OL_Liste_cotisations` supprime les ventilations/déductions puis **la prestation portant cet `IDprestation`** avant de supprimer la cotisation.

Ce dernier point est déterminant : si deux cotisations partageaient volontairement la même prestation, supprimer l'une supprimerait la prestation encore référencée par l'autre. Le comportement historique n'est donc cohérent qu'avec une relation métier 1:1.

## Pourquoi le schéma permet quand même des doublons ?

La table `cotisations` contient un champ `IDprestation`, mais aucune contrainte `UNIQUE(IDprestation)` n'est imposée par le schéma historique.

Des doublons peuvent donc exister à cause de :

- données anciennes ;
- import ou manipulation externe ;
- ancienne anomalie applicative ;
- intervention directe en base.

Ils doivent être considérés comme **anomalies de données**, pas comme règle métier.

## Décision pour l'export comptable

`MIN(IDcotisation)` est conservé comme **filet déterministe de compatibilité** :

- il empêche la multiplication silencieuse des lignes d'écriture ;
- il reproduit de façon déterministe ce que l'ancien `GROUP BY` permissif faisait de façon indéterministe ;
- il ne crée aucune nouvelle contrainte ni migration de schéma.

En revanche, il ne doit pas masquer l'existence d'une base anormale.

## Diagnostic ajouté à Noe-030

Le préflight `scripts/recette_existing_db_readonly.py` expose désormais :

```json
"business_anomalies": {
  "cotisations_shared_prestation_count": 0
}
```

La valeur représente le **nombre de prestations référencées par plus d'une cotisation**, sans exporter d'identifiant ni de donnée nominative.

La requête reste compatible avec SQLite et les anciens MySQL/MariaDB :

```sql
SELECT COUNT(*)
FROM (
    SELECT IDprestation
    FROM cotisations
    WHERE IDprestation IS NOT NULL
    GROUP BY IDprestation
    HAVING COUNT(*) > 1
) shared_cotisation_prestations
```

## Interprétation pendant la recette réelle

### Valeur = 0

C'est l'état attendu. La relation historique 1:1 est respectée et la sélection déterministe de l'export n'a pas d'effet sur les données normales.

### Valeur > 0

Ne pas corriger automatiquement la base.

Avant RC :

1. conserver la copie intacte ;
2. identifier les prestations concernées uniquement sur l'environnement de recette ;
3. déterminer l'origine des doublons ;
4. vérifier l'impact comptable et la ventilation ;
5. décider d'une réparation de données séparée si nécessaire.

Aucune contrainte `UNIQUE` n'est ajoutée dans le cadre de Noe-003 afin de ne pas casser silencieusement une base historique qui contiendrait déjà ce type d'anomalie.

## Statut

- compatibilité `ONLY_FULL_GROUP_BY` de l'export : **traitée** ;
- cardinalité métier normale cotisation/prestation : **1:1 confirmée par le cycle de vie applicatif** ;
- comportement sur données anormales : **déterministe + diagnostic explicite** ;
- validation finale : exécuter le préflight sur une copie de base réellement utilisée dans le cadre de Noe-030.
