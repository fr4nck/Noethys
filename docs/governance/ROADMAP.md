# Roadmap de gouvernance — Vanilla puis Upgrade

> Feuille de route de haut niveau. La roadmap technique détaillée d'Upgrade reste dans `docs/ROADMAP.md`.

## Piste A — Vanilla maintenance

Branche : `maintenance/vanilla`

### Objectif immédiat

Obtenir une version historique Noethys maintenue, utilisable sans attendre les migrations Python 3 / wxPython Phoenix ni la nouvelle interface.

### Étapes

1. figer le snapshot upstream de référence ;
2. inventorier les bugs historiques confirmés et les classer ;
3. sélectionner uniquement les correctifs compatibles avec la stack historique ;
4. backporter les correctifs déjà démontrés dans Upgrade lorsqu'ils sont réellement applicables ;
5. ajouter des tests/audits compatibles sans transformer le runtime de l'application ;
6. vérifier installation, ouverture, sauvegarde/restauration et parcours critiques ;
7. vérifier la compatibilité avec le Connecthys actuellement exploité ;
8. effectuer la recette sur une copie d'une base réelle ;
9. publier une première release de maintenance Vanilla.

### Critères de sortie

- aucun bug bloquant connu dans le périmètre ciblé ;
- aucun changement Python 3 / Phoenix / UX embarqué ;
- aucune migration implicite de base ;
- compatibilité Connecthys vérifiée sur les parcours concernés ;
- démarrage et usage quotidien validés sous Windows ;
- procédure d'installation et de retour arrière documentée.

## Piste B — Upgrade

Branche : `master`

Upgrade poursuit séparément :

- Python 3 ;
- wxPython Phoenix ;
- CI et packaging modernes ;
- UI/UX modernisée ;
- améliorations métier et architecture.

Upgrade peut continuer en parallèle mais ne doit pas retarder le jalon Vanilla.

## Flux entre les deux pistes

### Upgrade → Vanilla

Backporter uniquement les correctifs qui :

- correspondent à un bug présent dans la version historique ;
- peuvent être isolés de Python 3 / Phoenix / Repens ;
- ne changent pas le schéma ni le contrat Connecthys ;
- disposent d'une justification et d'une recette claire.

### Vanilla → Upgrade

Porter vers `master` les correctifs historiques encore pertinents afin d'éviter qu'un bug corrigé dans Vanilla reste présent dans Upgrade.

## Priorité de travail

Tant que la première release de maintenance Vanilla n'est pas qualifiée, lorsqu'un choix de priorité est nécessaire entre un correctif Vanilla utile à l'exploitation et une évolution non urgente d'Upgrade, le correctif Vanilla passe en premier.

## Interdiction de mélange

Un lot ne doit pas contenir simultanément :

- un bugfix Vanilla ;
- une migration Python 3/Phoenix ;
- une refonte UX ;
- une nouvelle fonction métier non liée.

Les lots restent petits, ciblés, testables et transférables entre branches lorsque pertinent.
