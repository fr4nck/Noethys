# Noe-031 — Tests de non-régression métier

## Objectif

La modernisation ne doit pas seulement « compiler » : les invariants métier déjà couverts par des tests doivent être exécutés à chaque changement de code. Cette couverture automatisée complète la recette humaine Noe-030 ; elle ne la remplace pas.

## Couverture automatisée

La CI exécute l'ensemble des tests `unittest` présents dans `tests/test_*.py`.

Les familles de risques actuellement couvertes comprennent notamment :

- **migration / copie de base** : conservation des structures et données attendues lors des opérations DB→DB ;
- **règlements** : conservation du résultat historique de `OL_Reglements` après réécriture SQL strict, une ligne par règlement et total de ventilation inchangé ;
- **exports comptables** : conservation des résultats QuadraCOMPTA/Cerig après suppression des `GROUP BY` non stricts ;
- **pont PMSL** : contrats d'export, ouvertures, synchronisation et obligation de validation humaine avant application ;
- **autres tests métier ajoutés au dépôt** : ils entrent automatiquement dans la suite dès lors qu'ils respectent le motif `tests/test_*.py`.

La base synthétique volumique et le préflight Noe-030 restent exécutés séparément dans la même CI afin de couvrir les lectures DB, volumes et absence de migration implicite.

## Règle de maintenance

Un correctif qui répare une régression métier reproductible doit, lorsque c'est raisonnablement automatisable, ajouter ou renforcer un test sous `tests/test_*.py`.

Le test doit privilégier :

1. un invariant observable plutôt qu'un détail d'implémentation ;
2. des données synthétiques ou factices, jamais une donnée réelle d'usager ;
3. l'absence de dépendance réseau ;
4. une exécution déterministe ;
5. la compatibilité avec la baseline Python 3.10.

## Checklist humaine avant RC

La recette sur copie réelle doit encore vérifier les parcours que la suite unitaire ne sait pas certifier seule :

- ouverture d'une base réellement utilisée ;
- consultation et modification d'une famille et d'un individu ;
- création/modification d'une inscription ;
- prestation et facturation ;
- saisie, ventilation et consultation d'un règlement ;
- dépôts et listes associées ;
- export comptable réellement utilisé par l'association ;
- impression/PDF sur un cas représentatif ;
- fermeture/réouverture de Noethys et persistance des modifications ;
- absence de migration de schéma inattendue via le contrôle Noe-030.

## Critère de validation

Noe-031 est considéré automatisé lorsque la découverte complète `tests/test_*.py` est verte dans la CI principale. La validation finale d'une RC reste conditionnée au scénario humain Noe-030 sur une copie de base réelle.
