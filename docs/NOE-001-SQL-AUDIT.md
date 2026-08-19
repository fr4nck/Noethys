# Noe-001 — SQL strict audit findings

## First identified candidate

### noethys/Ol/OL_Reglements.py

The query in `ListView.GetTracks()` contains:

```sql
SUM(ventilation.montant) AS total_ventilation
...
GROUP BY reglements.IDreglement
```

This is a likely `ONLY_FULL_GROUP_BY` compatibility issue because the SELECT clause contains many non aggregated columns coming from joined tables while grouping only on `reglements.IDreglement`.

## Decision

No automatic correction yet.

The query must be reviewed according to the expected business result:
- keep one row per payment;
- preserve the ventilation total;
- avoid changing displayed data.

## Next steps

- identify all similar patterns;
- decide between subquery aggregation, derived table, or expanded GROUP BY;
- add regression test before modification.
