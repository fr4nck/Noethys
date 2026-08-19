# Roadmap de modernisation de Noethys

Cette feuille de route décrit la trajectoire de modernisation du fork `fr4nck/Noethys`.

Le suivi opérationnel détaillé est disponible dans le backlog associé :

- [`docs/NOE-BACKLOG.md`](NOE-BACKLOG.md) — correspondance entre les séries Noe-xxx et les chantiers GitHub.

L'objectif n'est pas de réécrire Noethys ni de forcer les utilisateurs à migrer leurs données. La priorité est de prolonger durablement le logiciel en conservant son fonctionnement métier, ses bases existantes et, autant que possible, sa compatibilité historique.

## Principes directeurs

- préserver les bases et configurations existantes ;
- ne jamais introduire de migration implicite de schéma ;
- conserver la compatibilité MySQL/MariaDB historique ;
- rendre progressivement les requêtes compatibles avec les modes SQL modernes et stricts ;
- préférer des corrections ciblées aux refactorisations massives ;
- maintenir Windows, Linux et macOS comme cibles du code source ;
- tester les changements affectant les données sur une copie de base réelle.

## Phases de modernisation

Les phases détaillées restent organisées selon l'ordre de marche :

`SQL strict → wxPython → runtime Python → tests métier → packaging → RC → stable`

Voir également `docs/NOE-BACKLOG.md` pour le découpage en tâches Noe-xxx.
