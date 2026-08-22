# Noethys — fork Upgrade Noethys

Noethys est un logiciel libre et gratuit de gestion multi-activités destiné notamment aux accueils de loisirs, crèches, garderies périscolaires, cantines, clubs sportifs, structures culturelles et associations.

Ce dépôt est le fork `fr4nck/Noethys`, consacré à la **modernisation progressive de Noethys Desktop** en conservant son métier, ses bases existantes et ses configurations historiques autant que possible.

**Base fonctionnelle : Noethys 1.3.4.2 (1er février 2026), issue du `master` du dépôt amont `Noethys/Noethys`.**

Le projet d'origine et sa documentation fonctionnelle restent les références historiques pour Noethys. Ce fork ne cherche pas à effacer cette origine ni à imposer une réécriture ou un basculement vers NoethysWeb.

## État du projet — 22 août 2026

Le chantier a dépassé la seule remise à niveau Python/wxPython. Il comporte maintenant deux axes complémentaires.

### 1. Socle technique modernisé

Les principales portes automatisées d'une première Release Candidate conservatrice sont franchies :

- Python 3.10 comme baseline ;
- Python 3.11 qualifié et Python 3.12 étudié ;
- wxPython Phoenix ;
- SQL critique modernisé et tests de non-régression ;
- sauvegarde/restauration auditée et réparée ;
- CI Windows/macOS/Linux GTK3 ;
- portable Windows PyInstaller `onedir` réellement exécuté en CI ;
- mode historique `Portable/` qualifié ;
- préflight lecture seule des bases existantes ;
- sas RC manuel protégé.

La publication d'une RC validée reste volontairement bloquée jusqu'à une **recette humaine sur une copie d'une base réellement utilisée** et une validation visuelle/métier Windows du SHA candidat.

### 2. Modernisation métier et UI en cours

Le fork porte également désormais :

- design system desktop commun et thèmes clair/sombre ;
- échelle d'interface et accessibilité ;
- nettoyage wxPython des layouts, parentages et initialisations ;
- diagnostic des freezes et lenteurs MySQL distantes ;
- commandes de repas par points de livraison ;
- chantier de rapports métier fiables et rapports d'activité ;
- architecture tiers / conventions / mises à disposition / EPS ;
- portail Connecthys avec contenus dynamiques, RSS/Atom et barèmes Noethys en cours de développement ;
- expérimentation d'un registre minimal d'extensions optionnelles.

## Principes du fork

- aucune migration implicite de schéma ;
- préserver les données et configurations existantes ;
- conserver SQLite et les anciennes installations MySQL/MariaDB autant que raisonnablement possible ;
- corriger les causes racines plutôt que masquer les symptômes ;
- préférer des changements ciblés et testables aux refactorisations massives ;
- conserver Windows comme cible de distribution prioritaire sans rendre le code source Windows-only ;
- tester les changements métier sur une copie de base réelle ;
- une donnée métier = une source de vérité réutilisable par l'écran, l'export, le PDF, le rapport et le portail ;
- moderniser les composants communs avant les écrans particuliers ;
- documenter les décisions durables dans Git afin que le projet ne dépende pas d'un historique de conversations.

## Documentation — points d'entrée

- [`docs/README.md`](docs/README.md) — carte de la documentation et statut des documents ;
- [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md) — état transversal et décisions durables ;
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — trajectoire actuelle ;
- [`docs/NOE-BACKLOG.md`](docs/NOE-BACKLOG.md) — index des chantiers Noe-xxx et issues ;
- [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) — environnement, tests, CI, base et packaging ;
- [`docs/USER-GUIDE-UPGRADE.md`](docs/USER-GUIDE-UPGRADE.md) — installation, mise à jour et recette utilisateur ;
- [`docs/UPGRADE-HISTORY.md`](docs/UPGRADE-HISTORY.md) — historique des décisions ;
- [`docs/DESIGN_SYSTEM_UI_UX.md`](docs/DESIGN_SYSTEM_UI_UX.md) — direction UI/UX canonique ;
- [`docs/WXPYTHON_UI_RULES.md`](docs/WXPYTHON_UI_RULES.md) — règles d'implémentation wxPython ;
- [`docs/ARCHITECTURE-TIERS-PRESTATIONS-PLANNING.md`](docs/ARCHITECTURE-TIERS-PRESTATIONS-PLANNING.md) — tiers, conventions, EPS, planning et facturation ;
- [`docs/COMMANDES_REPAS_POINTS_LIVRAISON.md`](docs/COMMANDES_REPAS_POINTS_LIVRAISON.md) — commandes de repas ;
- [`docs/RC-CHECKLIST.md`](docs/RC-CHECKLIST.md) — qualification avant RC.

Les documents d'audit `NOE-00x-*`, `CI-WINDOWS-AUDIT.md` et `INTERFACE_MATERIAL3.md` conservent volontairement l'historique d'une étape précise. Ils ne remplacent pas les documents canoniques ci-dessus.

## Windows

Windows est la plateforme de distribution prioritaire.

Le workflow de packaging produit un portable contenant notamment :

```text
Noethys.exe
BUILD-INFO.txt
Static/
Portable/
```

La chaîne de qualification construit l'archive, la ré-extrait dans un dossier neuf, neutralise l'environnement Python externe puis exécute réellement l'EXE figé en mode smoke.

Le smoke automatique s'arrête volontairement avant la recette métier complète. Une CI verte ne remplace donc pas l'ouverture réelle d'une copie de base utilisateur.

## Mode portable

Noethys reconnaît historiquement un dossier `Portable/` à côté de l'exécutable. Le fork réutilise ce mécanisme.

Dans une distribution portable :

- configuration : `Portable/` ;
- bases locales : `Portable/Data/` ;
- temporaires : `Portable/Temp/` ;
- mises à jour : `Portable/Updates/` ;
- langues : `Portable/Lang/` ;
- synchronisation : `Portable/Sync/` ;
- extensions : `Portable/Extensions/`.

**Ne jamais supprimer le dossier `Portable/` d'une installation existante sans sauvegarde : il peut contenir les données utilisateur.**

## Compatibilité des bases

La conservation des données existantes est un invariant :

- aucune migration implicite ;
- SQLite conservé ;
- stratégie conservatrice pour MySQL/MariaDB ;
- recette sur copie réelle ;
- contrôle d'empreinte de schéma ;
- possibilité de retour arrière ;
- tests de non-régression sur les requêtes modernisées.

Une nouvelle RC ou branche ne doit jamais être qualifiée directement sur l'unique base de production.

## Interface et wxPython

La direction visuelle actuelle combine :

- **Fluent 2** pour la grammaire desktop ;
- **Material Design 3** pour les tokens, surfaces et thèmes ;
- une inspiration **Liquid Glass** très limitée pour la profondeur fonctionnelle ;
- **Fluent System Icons** pour l'iconographie principale.

Les règles wxPython sont strictes : pas de suppression d'assertion pour cacher un défaut, pas de confusion entre parent visuel et contrôleur métier, pas de métrique historique rigide réintroduite pour « faire tenir » un écran.

Voir `docs/DESIGN_SYSTEM_UI_UX.md` et `docs/WXPYTHON_UI_RULES.md`.

## Développement

Le point d'entrée historique reste :

```text
noethys/Noethys.py
```

La baseline de développement/distribution est Python 3.10.

Avant une contribution :

```bash
python -m compileall -q noethys
python -m unittest discover -s tests -p 'test_*.py' -v
```

Pour les changements touchant wxPython, base de données, packaging ou dépendances, les jobs GitHub Actions correspondants restent nécessaires.

Voir [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md).

## Source de vérité du projet

Pour le comportement et les décisions :

1. code et tests ;
2. issues GitHub ;
3. documentation `docs/` ;
4. conversations de travail uniquement avant consolidation.

Une décision importante ne doit plus rester uniquement dans un chat.

## Projet d'origine

Le dépôt amont `Noethys/Noethys` reste une source de compatibilité, de correctifs et de contexte historique. Les changements amont ou issus d'autres forks sont audités et repris uniquement lorsqu'ils apportent une valeur démontrée au fork moderne.
