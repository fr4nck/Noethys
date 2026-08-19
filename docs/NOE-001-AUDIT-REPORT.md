# Noe-001 — Rapport d’audit SQL strict

## Objectif

Identifier et classer les requêtes SQL du code Noethys susceptibles de dépendre du comportement permissif historique de MySQL/MariaDB, en particulier avec `ONLY_FULL_GROUP_BY`.

L’audit est **statique et non destructif** : il ne se connecte à aucune base et ne modifie aucun fichier métier.

## Scanner reproductible

Commande :

```bash
python scripts/audit_sql_strict.py --root noethys --format text
```

Pour n’afficher que les requêtes nécessitant une revue :

```bash
python scripts/audit_sql_strict.py --root noethys --format text --only review
```

Le scanner analyse les chaînes Python contenant `SELECT` + `GROUP BY`, y compris les sous-requêtes parenthésées, et classe chaque chaîne selon la portée SQL concernée.

## Résultat du closeout — 19 août 2026

**238** chaînes SQL avec `GROUP BY` ont été classées :

| Classe | Nombre | Signification |
|---|---:|---|
| `SAFE` | **77** | Tous les `GROUP BY` analysés sont strict-compatibles : chaque expression `SELECT` non agrégée est également groupée. |
| `DEDUPE` | **10** | `GROUP BY` sans agrégat mais strict-compatible ; usage historique de dédoublonnage, potentiellement simplifiable en `DISTINCT`, sans urgence SQL strict. |
| `REVIEW` | **151** | Au moins une expression `SELECT` non agrégée n’est pas groupée, un `HAVING` reste conservateur, ou une chaîne dynamique ne peut pas être certifiée automatiquement. |

Ces **151 REVIEW ne sont pas automatiquement 151 bugs fonctionnels**. Ils constituent la dette SQL à examiner avant de pouvoir garantir globalement `ONLY_FULL_GROUP_BY` sur tout Noethys.

La remédiation est désormais suivie dans **Noe-005 / issue #40**.

## Cas déjà corrigés / qualifiés

### `Ol/OL_Reglements.py` — Noe-002

Le code historique sélectionnait de nombreuses colonnes non agrégées avec :

```sql
GROUP BY reglements.IDreglement
```

La correction utilise une pré-agrégation de `ventilation` :

```sql
LEFT JOIN (
    SELECT IDreglement, SUM(montant) AS total_ventilation
    FROM ventilation
    GROUP BY IDreglement
) ventilation_totaux
    ON ventilation_totaux.IDreglement = reglements.IDreglement
```

Le `GROUP BY` permissif externe a disparu. Le scanner amélioré classe maintenant la chaîne **SAFE**, car il analyse correctement le `GROUP BY` de la sous-requête dans sa propre portée.

Des tests vérifient :

- une ligne par règlement ;
- la forme historique du résultat ;
- le total de ventilation inchangé.

La validation finale sur une copie de base réellement utilisée reste rattachée à Noe-002 / Noe-030.

### `Dlg/DLG_Export_compta.py` — Noe-003

Les requêtes QuadraCOMPTA/Cerig concernées sont désormais classées **SAFE** au sens `ONLY_FULL_GROUP_BY`.

Une question métier distincte reste ouverte : lorsqu’une prestation est liée à plusieurs cotisations, le code choisit actuellement une cotisation déterministe via `MIN(IDcotisation)`. Le scanner SQL strict ne peut pas décider si cette règle correspond au métier ; ce point reste donc suivi dans Noe-003.

## Nature du reliquat REVIEW

Les 151 requêtes restantes se répartissent principalement entre :

- listes métier sélectionnant une clé groupée et plusieurs attributs descriptifs non groupés ;
- requêtes avec `SUM` / `COUNT` et colonnes métier non agrégées ;
- dédoublonnages historiques où le `GROUP BY` ne couvre pas toutes les colonnes sélectionnées ;
- requêtes financières : facturation, ventilation, prélèvements, dépôts et comptabilité ;
- statistiques et impressions ;
- chaînes SQL dynamiques utilisant `%s`, volontairement laissées en revue lorsqu’un scanner statique ne peut pas connaître la liste finale de colonnes.

## Règles de remédiation

Le reliquat ne doit **pas** être corrigé par transformation mécanique globale.

À éviter :

- ajouter toutes les colonnes sélectionnées au `GROUP BY` sans vérifier la cardinalité ;
- envelopper arbitrairement une valeur avec `MIN()` ou `MAX()` ;
- remplacer un `GROUP BY` par `DISTINCT` lorsque les colonnes non groupées peuvent réellement varier.

Approches privilégiées :

- pré-agrégation dans une sous-requête lorsque l’agrégat porte sur une relation 1:N ;
- expansion du `GROUP BY` uniquement lorsqu’elle conserve démontrablement la même cardinalité ;
- `DISTINCT` uniquement lorsque l’intention est réellement le dédoublonnage de toutes les colonnes retournées ;
- test de non-régression pour les requêtes financières ou à forte portée métier ;
- validation sur une copie représentative de base pour les cas dépendant de données historiques réelles.

## Limites assumées du scanner

Le scanner est volontairement conservateur :

- il n’infère pas les dépendances fonctionnelles d’une clé primaire, car les anciennes versions MySQL/MariaDB strictes ne se comportent pas toutes comme les versions modernes ;
- il ne tente pas d’évaluer les substitutions dynamiques `%s` ;
- il ne prétend pas vérifier la sémantique métier d’un regroupement ;
- une classification `SAFE` signifie **strict-compatible selon les expressions SQL analysées**, pas « métier validé sur toutes les données historiques ».

## Statut Noe-001

- [x] scanner reproductible ;
- [x] détection des `SELECT` / `GROUP BY` ;
- [x] analyse des sous-requêtes ;
- [x] classification `SAFE` / `DEDUPE` / `REVIEW` ;
- [x] tests unitaires du classificateur ;
- [x] inventaire complet du code actuel ;
- [x] corrections restantes transférées vers Noe-005 ;
- [x] cas Noe-002 et Noe-003 reliés à leurs tickets dédiés.

Noe-001 peut donc être clos en tant que **travail d’audit**. La remédiation globale du reliquat continue dans Noe-005, sans bloquer la traçabilité de l’audit lui-même.
