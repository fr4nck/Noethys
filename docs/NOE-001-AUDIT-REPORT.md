# Noe-001 — Audit SQL strict

## Objective

Identify SQL queries incompatible with MySQL/MariaDB strict mode, especially `ONLY_FULL_GROUP_BY`.

## Confirmed findings

### OL_Reglements.py

Location:

```
noethys/Ol/OL_Reglements.py
```

Pattern detected:

```sql
SELECT
...
SUM(ventilation.montant) AS total_ventilation
...
GROUP BY reglements.IDreglement
```

Risk:

The query selects many non-aggregated columns while grouping only by `reglements.IDreglement`.

Potential impact:

- MySQL/MariaDB with `ONLY_FULL_GROUP_BY` enabled may reject the query.
- Existing installations using permissive SQL mode may continue to work.

## Proposed correction

Do not simply extend the `GROUP BY` clause with every selected field.

Preferred approach:

- calculate ventilation totals in a subquery;
- join the calculated result to `reglements`;
- preserve one row per regulation.

## Status

- [x] Issue identified
- [x] Documentation started
- [ ] Patch prepared
- [ ] Regression test completed
