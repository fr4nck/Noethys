# Vanilla — politique de maintenance

Cette branche est la ligne **Vanilla** du fork `fr4nck/Noethys`.

Branche : `maintenance/vanilla`

Snapshot upstream de référence : `630ef4373dbc05dae1cbc597b9baccb1178e64e4` (Noethys upstream 1.3.4.2).

Version applicative Vanilla préparée au 19/09/2026 : **1.3.4.3**. Le numéro affiché par le logiciel et le changelog utilisateur ont pour source `noethys/Versions.txt`.

## But

Maintenir la version historique de Noethys telle qu'elle est réellement utilisée, sans attendre ni importer la modernisation du fork.

## Autorisé

- correction d'un bug historique démontré ;
- robustesse ou sécurité compatible ;
- correctif de compatibilité nécessaire à l'exploitation historique ;
- tests, audits et documentation ;
- packaging ou scripts n'imposant pas une migration du runtime applicatif.

## Interdit sans décision explicite

- Python 3 ;
- wxPython Phoenix ;
- nouvel UX / refonte graphique ;
- nouvelles fonctions métier ;
- migration de schéma ;
- merge global de `master`.

## Connecthys

La compatibilité avec le Connecthys actuellement exploité est un invariant prioritaire. Tout patch touchant synchronisation, formats échangés ou structures attendues doit être validé séparément sur une copie ou un environnement de recette avant production.

## Backports

Un bug historique corrigé dans `master`/Upgrade peut être backporté ici uniquement sous forme de patch minimal indépendant de Python 3, Phoenix et du nouvel UX.

Les correctifs Vanilla encore pertinents doivent être portés vers Upgrade séparément.

## Données

Aucune migration implicite. Tester les changements SQL, sauvegarde, configuration ou synchronisation sur une copie de base avant exploitation.

## Suivi

Cockpit GitHub : issue #120.

État de stabilisation courant : `docs/VANILLA_STABILISATION.md`. Le candidat fonctionnel consolidé #361 est intégré sur `maintenance/vanilla` ; la qualification automatisée est verte, mais la recette humaine Windows reste nécessaire avant déclaration stable.

La gouvernance générale du dépôt est maintenue sur `master` dans `docs/governance/`.
