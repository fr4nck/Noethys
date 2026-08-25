# Stratégie de branches — Vanilla et Upgrade

> Décision de gouvernance du 25 août 2026. Ce document prime sur les anciennes formulations qui appelaient « Vanilla+ » la branche Python 3 / wxPython Phoenix.

## 1. Deux lignes de produit distinctes

Le dépôt `fr4nck/Noethys` porte désormais deux objectifs qui ne doivent plus être mélangés.

### Vanilla — maintenance de la version originale

La branche canonique est :

`maintenance/vanilla`

Elle part du snapshot upstream `Noethys/Noethys` au commit :

`630ef4373dbc05dae1cbc597b9baccb1178e64e4`

Vanilla désigne la version historique distribuée par le projet Noethys original. Son but n'est pas de moderniser le logiciel, mais de maintenir une version exploitable et familière pour les utilisateurs actuels.

Sont autorisés sur Vanilla :

- correction d'un bug démontré ;
- correction de robustesse ou de sécurité strictement compatible ;
- correctif de compatibilité nécessaire au fonctionnement de la version historique ;
- tests et outils d'audit n'imposant pas une migration du runtime applicatif ;
- documentation d'installation, de sauvegarde, de recette et de maintenance ;
- packaging ou scripts d'exploitation qui ne modifient pas le comportement métier historique.

Sont exclus de Vanilla sauf décision explicite ultérieure :

- migration Python 3 ;
- migration wxPython Phoenix ;
- nouveau moteur de thème ou nouvelle UX ;
- refonte graphique ;
- nouvelles fonctions métier ;
- changement de schéma de base de données ;
- refactoring massif sans bug démontré ;
- dépendance nouvelle imposée uniquement pour moderniser la stack.

### Upgrade — modernisation du fork

La branche `master` reste la ligne Upgrade. Elle peut porter :

- Python 3 ;
- wxPython Phoenix ;
- modernisation UI/UX ;
- nouveaux modules et fonctions métier ;
- nouveaux outils de packaging et de CI ;
- évolutions d'architecture explicitement décidées.

Upgrade ne doit jamais bloquer la disponibilité ou la maintenance de Vanilla.

## 2. Compatibilité Connecthys

La compatibilité avec le Connecthys actuellement exploité constitue un invariant prioritaire de Vanilla.

Aucun correctif Vanilla ne doit modifier volontairement :

- les contrats de synchronisation ;
- les structures ou identifiants de données attendus par Connecthys ;
- le comportement de synchronisation historique ;
- les formats échangés ;
- le schéma de base nécessaire à l'instance Connecthys existante,

sans décision dédiée et validation de compatibilité.

Lorsqu'un correctif touche une zone liée à Connecthys, il doit être qualifié comme tel et testé sur une copie ou un environnement de recette avant utilisation en production.

## 3. Règle de routage avant tout développement

Avant chaque modification, répondre à la question suivante :

> Cette modification corrige-t-elle le comportement de la version historique sans la moderniser ?

- **Oui** → cibler `maintenance/vanilla`.
- **Non, elle dépend de Python 3, Phoenix, du nouvel UX ou d'une évolution fonctionnelle** → cibler `master` / Upgrade.

En cas de doute, ne pas commencer le code avant d'avoir classé le changement.

## 4. Politique de transfert des correctifs

Les deux branches ne sont pas fusionnées l'une dans l'autre en bloc.

- Un bug historique corrigé dans Upgrade doit être backporté vers Vanilla sous forme de patch minimal lorsque le défaut existe aussi dans le snapshot historique.
- Un correctif Vanilla pertinent pour Upgrade doit être porté vers `master` séparément.
- Ne jamais fusionner `master` dans `maintenance/vanilla`.
- Ne jamais importer dans Vanilla une dépendance Python 3/Phoenix/Repens uniquement parce que le correctif a été trouvé dans Upgrade.

Le but est de partager les corrections, pas les chantiers de modernisation.

## 5. Données et exploitation

Vanilla doit rester compatible avec les bases existantes sans migration implicite.

Pour toute correction touchant SQL, synchronisation, sauvegarde ou configuration :

1. tester d'abord sur une copie de base ;
2. vérifier l'absence de migration silencieuse ;
3. vérifier le retour arrière ;
4. ne jamais qualifier directement un nouveau build sur l'unique base de production.

## 6. Priorité opérationnelle

La priorité immédiate est de disposer rapidement d'une Vanilla maintenue, installable et utilisable dans les conditions d'exploitation actuelles.

La modernisation Upgrade continue séparément, mais elle ne conditionne pas ce jalon.

## 7. Source de vérité

Pour éviter une nouvelle divergence entre conversations et développement :

1. cette politique de branche ;
2. les issues GitHub correspondantes ;
3. le code et les tests de la branche ciblée ;
4. les autres documents techniques du dépôt.

Toute décision future qui modifie la frontière Vanilla / Upgrade doit être consignée dans `docs/governance/DECISIONS.md` avant ou avec le changement de code.
