# Noethys

Noethys est un logiciel libre et gratuit de gestion multi-activités destiné notamment aux accueils de loisirs, crèches, garderies périscolaires, cantines, activités périscolaires, clubs sportifs et structures culturelles.

Le projet d'origine, sa documentation fonctionnelle et les informations historiques restent disponibles sur le site officiel de Noethys et dans le dépôt amont `Noethys/Noethys`.

## À propos de ce fork

`fr4nck/Noethys` poursuit la **remise à niveau technique de Noethys Desktop** en conservant son fonctionnement métier et, autant que possible, sa compatibilité avec les données et configurations existantes.

**Base fonctionnelle : Noethys 1.3.4.2 (1er février 2026), issue du `master` du dépôt amont `Noethys/Noethys`.** Cette base est plus récente que la version 1.3.3.9 encore distribuée sur le site officiel.

Le chantier ne vise pas une réécriture de Noethys ni une migration forcée vers NoethysWeb. Il modernise le code desktop par lots ciblés : Python 3, wxPython Phoenix, SQL strict, encodages, fichiers, dépendances, tests, sauvegarde/restauration et packaging.

## État actuel

Les principales portes **techniques automatisées** de la première RC modernisée sont désormais franchies :

- Python 3.10 comme baseline de production ;
- Python 3.11 et 3.12 qualifiés pour revalidation ponctuelle ;
- wxPython Phoenix ;
- SQL strict et non-régressions des règlements/exports comptables ;
- suite complète `tests/test_*.py` dans la CI ;
- préflight lecture seule des bases existantes ;
- sauvegarde/restauration auditée et réparée ;
- smoke tests Windows, macOS et Linux GTK3 ;
- build PyInstaller Windows `onedir` ;
- exécution réelle en CI de l'archive Windows extraite sans Python externe ;
- vrai mode portable via le dossier historique `Portable/` ;
- traçabilité du build via `BUILD-INFO.txt`.

Le projet dispose donc d'un **candidat technique RC**. La publication d'une RC validée reste volontairement bloquée jusqu'à une recette humaine sur une **copie d'une base réellement utilisée** et une validation visuelle/métier sous Windows.

## Windows

Windows est la plateforme de distribution prioritaire.

Le workflow `Package Windows` produit l'artefact :

```text
Noethys-Windows-portable
```

L'archive contient notamment :

```text
Noethys.exe
BUILD-INFO.txt
Static/
Portable/
```

La chaîne de qualification :

1. compile le code ;
2. valide les piles fonctionnelles et PDF ;
3. construit le bundle PyInstaller ;
4. vérifie les ressources historiques à côté de l'EXE ;
5. active le mode `Portable/` ;
6. crée l'archive ;
7. la ré-extrait dans un dossier neuf ;
8. neutralise `PYTHONHOME`, `PYTHONPATH` et le Python externe du `PATH` ;
9. exécute réellement `Noethys.exe` en mode smoke ;
10. vérifie les dépendances embarquées ;
11. publie l'artefact.

Le smoke automatique s'arrête avant l'ouverture de la configuration ou d'une base utilisateur. Une recette réelle reste donc nécessaire avant RC.

## Mode portable

Noethys reconnaît historiquement un dossier `Portable` à côté de l'exécutable. Le fork réutilise ce mécanisme au lieu d'en créer un nouveau.

Dans la distribution portable :

- configuration : `Portable/` ;
- bases locales : `Portable/Data/` ;
- temporaires : `Portable/Temp/` ;
- mises à jour : `Portable/Updates/` ;
- langues : `Portable/Lang/` ;
- synchronisation : `Portable/Sync/` ;
- extensions : `Portable/Extensions/`.

Les installations classiques sans dossier `Portable/` conservent leur comportement habituel.

## Linux

Le code source reste une cible Linux. La CI utilise Ubuntu avec wxPython GTK3 sous Xvfb et vérifie :

- le backend GTK/Phoenix ;
- la création/destruction de `wx.App` ;
- un layout wx représentatif avec sizers et `UltimateListCtrl`.

Il n'existe pas encore de paquet Linux utilisateur final équivalent au portable Windows.

## macOS

Le code source reste également une cible macOS. La CI valide compilation, imports, wxPython Phoenix, `wx.App` et layout représentatif.

Cette qualification confirme le socle technique du code source ; elle ne constitue pas encore une distribution macOS signée/notarisée ni une recette métier complète sur machine réelle.

## Compatibilité des bases

La conservation des données existantes est un invariant du chantier :

- aucune migration implicite de schéma ;
- SQLite conservé ;
- stratégie conservatrice pour les anciennes installations MySQL/MariaDB ;
- recette sur copie de base réelle ;
- possibilité de retour arrière ;
- contrôles de non-régression sur les requêtes modernisées.

Une CI verte ou un build réussi ne justifient jamais un premier essai sur l'unique base de production.

## Développement

Le point d'entrée historique reste :

```text
noethys/Noethys.py
```

La baseline de développement/distribution est Python 3.10. Les changements doivent privilégier les API portables et isoler le code spécifique à une plateforme uniquement lorsque c'est nécessaire.

Voir [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) pour l'environnement, l'architecture du dépôt, les tests, les audits et le build.

## Documentation

- [`docs/ROADMAP.md`](docs/ROADMAP.md) — feuille de route ;
- [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) — documentation développeur ;
- [`docs/USER-GUIDE-UPGRADE.md`](docs/USER-GUIDE-UPGRADE.md) — installation, mise à jour, sauvegarde et recette utilisateur ;
- [`docs/UPGRADE-HISTORY.md`](docs/UPGRADE-HISTORY.md) — historique et décisions du chantier ;
- [`docs/PACKAGING-WINDOWS11.md`](docs/PACKAGING-WINDOWS11.md) — packaging Windows ;
- [`docs/RC-CHECKLIST.md`](docs/RC-CHECKLIST.md) — checklist avant RC ;
- [`docs/NOE-030-RECETTE-BASE-EXISTANTE.md`](docs/NOE-030-RECETTE-BASE-EXISTANTE.md) — recette sur copie de base existante ;
- [`docs/NOE-042-RC-READINESS.md`](docs/NOE-042-RC-READINESS.md) — état de préparation de la RC ;
- `noethys/Doc/` — documentation historique embarquée dans Noethys.

## Principes de contribution

Les changements doivent rester ciblés : pas de refactorisation cosmétique massive, pas de nouvelle fonctionnalité métier mêlée à la modernisation, pas de multiplication inutile des workflows et pas de modification globale des données ou encodages sans preuve de compatibilité.

Lorsqu'un défaut apparaît, la priorité est de corriger sa cause racine et d'ajouter un garde-fou reproductible lorsqu'il apporte une valeur réelle.

## Projet d'origine

Noethys est un projet existant dont ce dépôt dérive. Cette modernisation vise à prolonger sa compatibilité technique sur les plateformes actuelles, pas à effacer son origine ni à se substituer à sa documentation fonctionnelle historique.
