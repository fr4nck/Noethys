# Noethys

Noethys est un logiciel libre et gratuit de gestion multi-activités destiné notamment aux accueils de loisirs, crèches, garderies périscolaires, cantines, activités périscolaires, clubs sportifs et structures culturelles.

Le projet d'origine, sa documentation fonctionnelle et les informations destinées aux utilisateurs restent disponibles sur le site officiel de Noethys et dans le dépôt amont `Noethys/Noethys`.

## À propos de ce fork

Ce dépôt `fr4nck/Noethys` travaille à la **remise à niveau technique de Noethys** en conservant son fonctionnement métier et, autant que possible, sa compatibilité avec les données existantes et les plateformes historiquement visées.

**Base fonctionnelle : Noethys 1.3.4.2 (1er février 2026), issue du `master` du dépôt amont `Noethys/Noethys`.** Cette base est plus récente que la version 1.3.3.9 encore distribuée sur le site officiel. Le fork conserve donc les évolutions fonctionnelles et correctifs intégrés en amont jusqu'à la 1.3.4.2, auxquels s'ajoute le chantier de modernisation technique décrit ci-dessous.

La modernisation concerne donc le **code source multi-plateforme** de Noethys : Windows, Linux et macOS. Windows 11 est actuellement la plateforme la plus avancée dans la qualification, car un packaging PyInstaller y est en cours de stabilisation et dispose déjà d'un premier build réussi.

Le chantier porte principalement sur :

- la compatibilité avec Python 3 et les API modernes ;
- wxPython 4 et les écarts de comportement entre plateformes ;
- les encodages UTF-8 et les frontières texte/binaire ;
- les chemins de fichiers et les données historiques ;
- Pillow, ReportLab, SQLite et les dépendances utilisées par Noethys ;
- les imports dynamiques et anciennes compatibilités runtime ;
- une CI GitHub Actions ciblée et frugale ;
- la qualification progressive de Windows, Linux et macOS ;
- la production d'artefacts adaptés à chaque plateforme lorsque leur chaîne de fabrication est suffisamment stabilisée.

L'objectif n'est pas de réécrire Noethys ni d'ajouter des évolutions métier dans ce lot. Les corrections sont progressives et doivent rester portables sauf lorsqu'un comportement est intrinsèquement spécifique à un système d'exploitation.

## État de la modernisation

Le code modernisé doit rester compatible avec les trois familles de plateformes supportées par Noethys :

- **Linux** : la CI compile et audite le code sous Ubuntu ;
- **Windows** : la CI valide la compilation, les imports non-GUI et l'initialisation de `wx.App`, et un premier packaging portable Windows 11 a été construit avec succès ;
- **macOS** : la CI valide désormais la compilation, les imports non-GUI et l'initialisation de `wx.App` sur macOS.

Ces validations automatisées confirment la compatibilité technique de base des trois plateformes, mais elles ne remplacent pas une recette fonctionnelle complète avec une base réelle, les principaux écrans, impressions, exports et périphériques.

La modernisation active est actuellement suivie dans la branche `agent/windows11-pyinstaller` et dans la PR #2. Son nom reflète le premier chantier de packaging, pas une limitation fonctionnelle du fork à Windows.

## Windows

Windows 11 est aujourd'hui la plateforme de packaging la plus avancée. La chaîne Python 3.10 + wxPython 4 + PyInstaller a déjà produit un dossier `onedir`, un `Noethys.exe` et une archive GitHub Actions.

La CI Windows valide également la compilation des sources, plusieurs imports non-GUI et la création/destruction d'un `wx.App`. Ces contrôles constituent une qualification technique reproductible, mais **ne constituent pas encore une version stable destinée à remplacer l'installation historique**.

La procédure, les contrôles et les critères de qualification sont documentés dans [`docs/PACKAGING-WINDOWS11.md`](docs/PACKAGING-WINDOWS11.md).

Les artefacts produits pendant la modernisation doivent être testés avec une **copie** d'une base existante, jamais directement avec une base de production.

## Linux

Linux reste une cible du code source. La CI exécute déjà les contrôles de compilation et plusieurs audits sur `ubuntu-latest`.

Les anciennes instructions d'installation Linux du projet amont restent utiles pour comprendre les dépendances historiques, mais elles devront être réactualisées lorsque la cible Linux moderne aura été qualifiée de bout en bout avec les versions de Python, wxPython et des dépendances retenues pour ce fork.

## macOS

macOS reste également une cible du projet. Aucun choix d'architecture ne doit rendre le code Windows-only sans nécessité explicite.

La CI macOS exécute désormais une validation récente de compilation, des imports non-GUI et un smoke-test `wx.App`. Cela confirme que le socle Python/wxPython démarre correctement dans l'environnement GitHub Actions macOS.

Cette validation ne vaut toutefois pas encore qualification fonctionnelle complète : il reste à tester l'application avec une copie de base réelle, les principaux parcours GUI, impressions, exports et éventuelles intégrations spécifiques à macOS avant d'annoncer une compatibilité utilisateur totalement garantie.

## Développement depuis les sources

Le point d'entrée historique reste :

```text
noethys/Noethys.py
```

Les évolutions doivent privilégier les API Python et wxPython portables. Le code spécifique à Windows, Linux ou macOS doit rester isolé et explicitement conditionné lorsqu'il est réellement nécessaire.

## Compatibilité des bases

La conservation des données existantes est un invariant du chantier :

- aucune migration implicite de schéma ;
- recette sur copie de base réelle ;
- vérification des principaux modules métier ;
- contrôle de la compatibilité avec la version historique lorsque cela fait partie du scénario de validation.

Une CI verte ou un build réussi sur une plateforme ne suffisent pas à déclarer toutes les plateformes fonctionnellement qualifiées : chaque environnement doit disposer de ses propres contrôles adaptés et d'une recette réelle lorsque nécessaire.

## Documentation

- [`docs/PACKAGING-WINDOWS11.md`](docs/PACKAGING-WINDOWS11.md) — packaging, CI, recette et critères de qualification Windows 11 ;
- `noethys/Doc/` — documentation historique embarquée dans Noethys.

La documentation Linux et macOS sera complétée à mesure que leurs chaînes modernes de test et de distribution seront qualifiées.

## Principes de contribution

Les changements doivent rester ciblés : pas de refactorisation cosmétique massive, pas de nouvelle fonctionnalité métier mêlée à la modernisation, pas de multiplication inutile des workflows et pas de modification globale des données ou encodages sans preuve de compatibilité.

Lorsqu'un défaut apparaît, la priorité est de corriger sa cause racine et d'ajouter un garde-fou reproductible lorsqu'il apporte une réelle valeur. Une correction introduite pour une plateforme ne doit pas dégrader les autres sans justification documentée.

## Projet d'origine

Noethys est un projet existant dont ce dépôt dérive. Cette modernisation vise à prolonger sa compatibilité technique sur les plateformes actuelles, pas à effacer son origine ni à se substituer à sa documentation fonctionnelle historique.
