# Noethys

Noethys est un logiciel libre et gratuit de gestion multi-activités destiné notamment aux accueils de loisirs, crèches, garderies périscolaires, cantines, activités périscolaires, clubs sportifs et structures culturelles.

Le projet d'origine, sa documentation fonctionnelle et les informations destinées aux utilisateurs restent disponibles sur le site officiel de Noethys et dans le dépôt amont `Noethys/Noethys`.

## À propos de ce fork

Ce dépôt `fr4nck/Noethys` travaille à la **remise à niveau technique de Noethys**, en conservant son fonctionnement métier et la compatibilité avec les données existantes autant que possible.

Le chantier actuel porte principalement sur :

- la compatibilité avec Python 3 et les API modernes ;
- wxPython 4 et le comportement réel sous Windows 11 ;
- les encodages UTF-8 et les frontières texte/binaire ;
- les chemins Windows et les données historiques ;
- Pillow, ReportLab, SQLite et les dépendances utilisées par Noethys ;
- les imports dynamiques et anciennes compatibilités runtime ;
- une CI GitHub Actions ciblée et frugale ;
- la production d'une version Windows portable avec PyInstaller.

L'objectif n'est pas de réécrire Noethys ni d'ajouter des évolutions métier dans ce lot. Les corrections sont volontairement progressives et doivent préserver la possibilité de travailler avec les bases existantes.

## État de la modernisation Windows 11

La branche de travail `agent/windows11-pyinstaller` est actuellement en phase de qualification.

Un premier packaging Windows portable a déjà été construit avec succès : la chaîne Python 3.10 + wxPython 4 + PyInstaller produit bien un dossier `onedir`, un `Noethys.exe` et une archive GitHub Actions.

Ce premier succès valide la chaîne de fabrication, mais **ne constitue pas encore une version stable ou une release destinée à remplacer l'installation historique**. Le HEAD courant doit encore être packagé puis testé sur Windows 11 avec une copie de base réelle.

La CI automatise notamment la compilation, les audits de compatibilité, les contrôles UTF-8, plusieurs smoke-tests wxPython/Windows et le préflight de packaging. Le build PyInstaller complet reste volontairement manuel afin d'éviter des fabrications coûteuses et inutiles à chaque modification.

## Windows

Pour la version stable historique de Noethys, utiliser les canaux de téléchargement du projet d'origine.

Pour le travail de modernisation de ce fork, le workflow GitHub Actions `Package Windows` fabrique un artefact portable `Noethys-Windows11-portable`.

La procédure détaillée de fabrication, les contrôles exécutés et la recette attendue sont documentés dans [`docs/PACKAGING-WINDOWS11.md`](docs/PACKAGING-WINDOWS11.md).

> **Important :** les artefacts de développement doivent être testés avec une **copie** d'une base existante. Aucune base de production ne doit servir directement à une recette de migration ou de compatibilité.

## Développement depuis les sources

Le dépôt conserve `requirements.txt` pour les dépendances d'exécution et `requirements-build.txt` pour les dépendances nécessaires à la fabrication Windows.

Le point d'entrée historique reste :

```text
noethys/Noethys.py
```

Le dépôt contient également des scripts d'audit et de smoke-test dans `scripts/`. Ils servent à détecter les incompatibilités reproductibles sans transformer la CI en matrice lourde Linux/Windows.

Les instructions historiques du projet amont restent utiles pour comprendre l'environnement de Noethys, mais les anciennes recettes figées sur une distribution Linux ou une génération précise de dépendances ne doivent pas être considérées comme la référence de ce fork de modernisation.

## Compatibilité des bases

La conservation des données existantes est un invariant du chantier :

- aucune migration implicite de schéma dans le lot Windows 11 ;
- recette sur copie de base réelle ;
- vérification des principaux modules métier ;
- contrôle qu'une copie utilisée pour la recette reste ouvrable avec la version historique lorsque cela fait partie du scénario de validation.

Une CI verte ou un build PyInstaller réussi ne suffisent donc pas à déclarer une version compatible : la recette fonctionnelle Windows reste obligatoire.

## Documentation technique

- [`docs/PACKAGING-WINDOWS11.md`](docs/PACKAGING-WINDOWS11.md) — packaging, préflight, CI, recette et critères de qualification Windows 11 ;
- [`docs/UPSTREAM-BUG-BACKLOG.md`](docs/UPSTREAM-BUG-BACKLOG.md) — défauts ou compatibilités identifiés qui doivent être suivis sans mélanger correction technique et évolution métier ;
- `noethys/Doc/` — documentation historique embarquée dans Noethys.

## Principes de contribution à ce chantier

Les changements doivent rester ciblés : pas de refactorisation cosmétique massive, pas de nouvelle fonctionnalité métier mêlée à la modernisation, pas de multiplication des workflows et pas de modification globale des données ou encodages sans preuve de compatibilité.

Lorsqu'un défaut apparaît, la priorité est de corriger sa cause racine et d'ajouter un garde-fou reproductible lorsqu'il apporte une réelle valeur.

## Projet d'origine

Noethys est un projet existant dont ce dépôt dérive. Cette modernisation vise à prolonger sa compatibilité technique, pas à effacer son origine ni à se substituer à sa documentation fonctionnelle historique.
