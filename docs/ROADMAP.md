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

## État au 19 août 2026

La modernisation technique nécessaire à une première Release Candidate conservatrice est **terminée** :

- SQL critique règlements / exports comptables sécurisé et couvert par des tests ;
- Python 3.10 baseline qualifiée, Python 3.11 validé et Python 3.12 étudié avec succès ;
- wxPython Phoenix qualifié ;
- Windows, macOS et Linux/GTK3 protégés par CI ;
- tests de non-régression métier exécutés globalement ;
- sauvegarde/restauration auditée et une anomalie historique de restauration corrigée ;
- portable Windows PyInstaller construit, extrait puis exécuté réellement en CI ;
- mode `Portable/` isolant configuration et données validé ;
- préflight Noe-002/003/004/030 regroupé en une seule commande pour une copie de base réelle ;
- sas RC manuel protégé : aucune RC ne peut être fabriquée sans confirmation explicite de la recette réelle et la release produite reste en brouillon.

## Dernière ligne droite avant RC

Il ne reste plus de développement technique caché obligatoire. La RC est volontairement bloquée par une validation d'exploitation :

1. exécuter `scripts/rc_db_preflight.py` sur une **copie** d'une base Noethys réellement utilisée ;
2. effectuer le parcours métier documenté dans `NOE-030-RECETTE-BASE-EXISTANTE.md` sur une copie jetable ;
3. analyser/corriger uniquement les anomalies réellement observées ;
4. déclencher le workflow `Release Candidate` depuis `master` en confirmant la recette ;
5. relire la release GitHub créée en brouillon avant toute publication.

## Après la RC

Noe-005 porte la dette SQL stricte progressive issue de l'audit complet : 151 requêtes restent classées `REVIEW`. Elles ne correspondent pas à 151 bugs connus. Les chemins financiers critiques ont déjà été traités ; ce reliquat sera réduit progressivement après la RC, sauf si la recette réelle révèle un cas bloquant qui devra alors être corrigé avant publication.

## Ordre de marche réalisé

La trajectoire suivie reste :

`SQL / DB → runtime Python → wxPython / plateformes → tests métier / exploitation → packaging → portable → RC`

Voir `docs/NOE-BACKLOG.md` pour le découpage en tâches Noe-xxx et les tickets encore ouverts uniquement pour validation réelle.
