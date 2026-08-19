# Audit SQL strict — Noethys

Ce document suit la phase 1 de la roadmap de modernisation.

## Objectif

Rendre progressivement les requêtes Noethys compatibles avec les modes SQL modernes, notamment `ONLY_FULL_GROUP_BY`, **sans casser la compatibilité MySQL/MariaDB historique (dont 5.5)** et sans migration implicite de schéma ou de données.

L'audit se concentre en priorité sur les `GROUP BY` historiques qui ont parfois été utilisés pour masquer des doublons de jointure ou qui reposent sur le comportement permissif des anciennes versions MySQL/MariaDB.

## Règles de correction

1. **Aucune agrégation réelle** : supprimer le `GROUP BY` si les jointures sont 1:1 et si le résultat reste une ligne métier par enregistrement.
2. **Relation 1:N provoquant des doublons** : isoler l'agrégation ou la relation dans une sous-requête ou une lecture séparée.
3. **Agrégation réellement souhaitée** : conserver le `GROUP BY`, mais rendre la requête déterministe et compatible SQL strict.
4. **Aucune correction globale automatique** : chaque requête est revue selon sa sémantique métier.
5. **Aucune migration de données** : les corrections portent uniquement sur la lecture SQL dans cette phase.
6. **Validation sur copie de base réelle** avant qualification.

## Outil d'audit

Le script `scripts/audit_sql_group_by.py` repère les blocs SQL contenant `GROUP BY` et distingue sommairement :

- `aggregation` : un agrégat (`SUM`, `COUNT`, `AVG`, etc.) est visible dans le `SELECT` ;
- `group-by-without-visible-aggregate` : aucun agrégat n'est visible dans le `SELECT` et la requête mérite donc une revue particulière.

Le script est volontairement conservateur : un résultat n'est pas nécessairement un bug.

## Premiers cas confirmés

### `noethys/Ol/OL_Reglements.py`

État actuel :

- jointure directe de `ventilation` ;
- `SUM(ventilation.montant)` ;
- sélection de nombreuses colonnes de `reglements` et tables associées ;
- `GROUP BY reglements.IDreglement` uniquement.

**Classification : à réécrire.**

Approche retenue : agréger `ventilation` dans une sous-requête par `IDreglement`, puis joindre ce résultat à la requête principale. Le `GROUP BY` principal devient inutile.

Cette solution conserve le résultat métier attendu (total ventilé par règlement) et évite de dépendre du mode SQL permissif.

### `noethys/Dlg/DLG_Export_compta.py`

Plusieurs familles de requêtes sont présentes :

- `GROUP BY prestations.IDprestation` sans agrégation visible ;
- `GROUP BY reglements.IDreglement` sans agrégation visible ;
- `GROUP BY depots.IDdepot, reglements.IDmode` dans des requêtes qui effectuent réellement des regroupements ;
- certaines variantes historiques joignent encore `cotisations` / `types_cotisations` avant de regrouper par prestation.

**Classification : audit par famille de requêtes.**

Priorités :

1. supprimer les `GROUP BY` devenus artificiels lorsque les jointures sont désormais 1:1 ;
2. séparer les informations de cotisation lorsque la jointure crée une cardinalité 1:N ;
3. conserver les agrégations dépôt/mode lorsqu'elles sont métier ;
4. vérifier l'égalité des totaux comptables avant/après correction.

## Régressions à exclure

Pour chaque correction SQL :

- même nombre de prestations lorsque le regroupement n'est pas métier ;
- mêmes montants de facturation ;
- mêmes montants ventilés ;
- mêmes totaux de dépôts ;
- mêmes totaux d'exports comptables ;
- aucun changement du schéma ;
- aucune écriture supplémentaire en base.

## État

- [x] Roadmap SQL strict définie
- [x] Scanner `GROUP BY` ajouté
- [x] `OL_Reglements.py` identifié comme premier cas prioritaire
- [x] `DLG_Export_compta.py` identifié comme sous-système prioritaire
- [ ] Réécriture SQL de `OL_Reglements.py`
- [ ] Revue complète des familles de requêtes de `DLG_Export_compta.py`
- [ ] Revue des autres résultats du scanner
- [ ] Tests de non-régression sur copie de base réelle
- [ ] Validation MySQL/MariaDB historique et SQL strict moderne
