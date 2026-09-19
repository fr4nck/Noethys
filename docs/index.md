# Documentation Noethys

Cette documentation est la vue navigable du dossier `docs/` du dépôt **fr4nck/Noethys**. Les fichiers Markdown du dépôt restent la source documentaire : le site MkDocs n'en est qu'une publication recherchable.

## Deux lignes de produit

Le dépôt distingue explicitement deux lignes :

- **Upgrade** — branche `master`, modernisée avec Python 3, wxPython Phoenix, CI/packaging modernes et évolutions UI/UX ou métier décidées ;
- **Vanilla** — branche `maintenance/vanilla`, destinée à maintenir la version historique sans introduire les modernisations d'Upgrade.

Une page doit être lue dans le périmètre de la ligne qu'elle documente. En cas de doute, consulter d'abord la [stratégie de branches](governance/PROJECT_STRATEGY.md).

## Points d'entrée

Pour comprendre rapidement le projet :

1. [État et décisions durables](PROJECT_STATE.md)
2. [Roadmap Upgrade](ROADMAP.md)
3. [Backlog Noe-xxx](NOE-BACKLOG.md)
4. [Développement](DEVELOPMENT.md)
5. [Guide utilisateur Upgrade](USER-GUIDE-UPGRADE.md)
6. [Stratégie de gouvernance](governance/PROJECT_STRATEGY.md)

La [carte documentaire complète](README.md) décrit le rôle des principaux documents et leur ordre de lecture.

## Recherche

La recherche du site indexe le contenu Markdown publié. Elle est prévue pour retrouver rapidement une notion métier, une procédure, une décision d'architecture ou une règle de développement sans connaître le nom du fichier correspondant.

## Source de vérité

Pour le comportement et les décisions du projet, l'ordre de référence reste :

1. code et tests intégrés ;
2. issues et pull requests GitHub ;
3. documentation versionnée dans `docs/` ;
4. historique Git pour la provenance.

Une pull request ouverte n'est pas un comportement intégré tant qu'elle n'est pas fusionnée.

## Versions publiées

Le site est initialement construit depuis `master`. Le versionnement simultané de plusieurs documentations n'est pas activé dans ce premier lot : il pourra être ajouté plus tard, par exemple avec `mike`, lorsqu'il faudra réellement maintenir plusieurs versions publiées en parallèle.

## Contribuer

Voir [Contribuer à la documentation](CONTRIBUTING_DOCS.md) pour le cycle branche → modification Markdown → pull request → validation → publication.
