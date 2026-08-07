# Noethys

Noethys est un logiciel libre et gratuit de gestion multi-activités destiné notamment aux accueils de loisirs, crèches, garderies périscolaires, cantines, activités périscolaires, clubs sportifs et structures culturelles.

Le projet d'origine, sa documentation fonctionnelle et les informations destinées aux utilisateurs restent disponibles sur le site officiel de Noethys et dans le dépôt amont `Noethys/Noethys`.

## À propos de ce fork

Ce dépôt `fr4nck/Noethys` travaille à la **remise à niveau technique de Noethys**, en conservant son fonctionnement métier et la compatibilité avec les données existantes autant que possible.

Le chantier porte principalement sur :

- la compatibilité avec Python 3 et les API modernes ;
- wxPython 4 et le comportement réel sous Windows 11 ;
- les encodages UTF-8 et les frontières texte/binaire ;
- les chemins Windows et les données historiques ;
- Pillow, ReportLab, SQLite et les dépendances utilisées par Noethys ;
- les imports dynamiques et anciennes compatibilités runtime ;
- une CI GitHub Actions ciblée et frugale ;
- la production d'une version Windows portable avec PyInstaller.

L'objectif n'est pas de réécrire Noethys ni d'ajouter des évolutions métier dans ce lot. Les corrections sont progressives et doivent préserver la possibilité de travailler avec les bases existantes.

## État de la modernisation Windows 11

La modernisation active est suivie dans la branche `agent/windows11-pyinstaller` et dans la PR #2. Tant que cette PR n'est pas qualifiée et fusionnée, `master` reste la référence stable de ce fork.

Un premier packaging Windows portable a déjà été construit avec succès : la chaîne Python 3.10 + wxPython 4 + PyInstaller produit un dossier `onedir`, un `Noethys.exe` et une archive GitHub Actions.

Ce premier succès valide la chaîne de fabrication, mais **ne constitue pas encore une version stable destinée à remplacer l'installation historique**. Le HEAD courant de la branche de modernisation doit encore être packagé puis testé sur Windows 11 avec une copie de base réelle.

La procédure, les contrôles et les critères de qualification sont documentés dans [`docs/PACKAGING-WINDOWS11.md`](docs/PACKAGING-WINDOWS11.md).

## Windows

Pour la version stable historique de Noethys, utiliser les canaux de téléchargement du projet d'origine.

Les artefacts produits par ce fork pendant la modernisation sont des versions de développement. Ils doivent être testés avec une **copie** d'une base existante, jamais directement avec une base de production.

## Développement depuis les sources

Le point d'entrée historique reste :

```text
noethys/Noethys.py
```

Les instructions historiques du projet amont restent utiles pour comprendre l'environnement de Noethys. Les recettes anciennes figées sur une distribution Linux ou une génération précise de dépendances ne doivent toutefois pas être considérées comme la cible de la modernisation Windows 11.

## Compatibilité des bases

La conservation des données existantes est un invariant du chantier :

- aucune migration implicite de schéma ;
- recette sur copie de base réelle ;
- vérification des principaux modules métier ;
- contrôle de la compatibilité avec la version historique lorsque cela fait partie du scénario de validation.

Une CI verte ou un build PyInstaller réussi ne suffisent pas à déclarer une version compatible : la recette fonctionnelle Windows reste obligatoire.

## Documentation

- [`docs/PACKAGING-WINDOWS11.md`](docs/PACKAGING-WINDOWS11.md) — état du chantier, packaging, CI, recette et critères de qualification Windows 11 ;
- `noethys/Doc/` — documentation historique embarquée dans Noethys.

## Principes de contribution

Les changements doivent rester ciblés : pas de refactorisation cosmétique massive, pas de nouvelle fonctionnalité métier mêlée à la modernisation, pas de multiplication des workflows et pas de modification globale des données ou encodages sans preuve de compatibilité.

Lorsqu'un défaut apparaît, la priorité est de corriger sa cause racine et d'ajouter un garde-fou reproductible lorsqu'il apporte une réelle valeur.

## Projet d'origine

Noethys est un projet existant dont ce dépôt dérive. Cette modernisation vise à prolonger sa compatibilité technique, pas à effacer son origine ni à se substituer à sa documentation fonctionnelle historique.
