# Consignes de développement — choisir la bonne ligne avant de coder

Avant toute modification, identifier explicitement la branche produit cible.

## Vanilla

Branche : `maintenance/vanilla`

Vanilla = version historique Noethys maintenue.

Autorisé : bugfix, robustesse, sécurité, compatibilité d'exploitation, tests, audits et documentation compatibles avec la stack historique.

Ne pas introduire dans Vanilla :

- Python 3 ;
- wxPython Phoenix ;
- nouvel UX / refonte graphique ;
- nouvelles fonctions métier ;
- migration de schéma ;
- merge global de `master`.

La compatibilité avec les bases existantes et le Connecthys actuellement exploité est prioritaire.

## Upgrade

Branche : `master`

Upgrade = ligne modernisée : Python 3, wxPython Phoenix, nouvelle UI/UX, packaging/CI modernes et évolutions fonctionnelles décidées.

## Règle de routage

Poser cette question avant de commencer :

> « Est-ce que ce changement corrige la version historique sans la moderniser ? »

- Oui → `maintenance/vanilla`.
- Non / dépend de Python 3, Phoenix, nouvel UX ou nouvelle fonction → `master`.

Ne pas commencer un changement tant que cette classification n'est pas claire.

## Backports

- Ne jamais fusionner `master` dans `maintenance/vanilla`.
- Backporter uniquement les bugs historiques sous forme de patches minimaux indépendants des modernisations.
- Reporter vers `master` les correctifs Vanilla encore pertinents.

## Références obligatoires

Lire avant un changement transversal :

- `docs/governance/PROJECT_STRATEGY.md` ;
- `docs/governance/DECISIONS.md` ;
- `docs/governance/ROADMAP.md` ;
- issue #120 pour le cockpit Vanilla ;
- issue #99 pour le cockpit Upgrade.

Une décision qui change la frontière Vanilla / Upgrade doit être documentée dans Git avant ou avec le code concerné.
