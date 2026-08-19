# Développement — fork Upgrade Noethys

## Positionnement

Ce dépôt modernise Noethys Desktop sans réécriture métier. Les priorités de développement sont, dans l'ordre :

1. conserver les bases et configurations existantes ;
2. éviter toute migration implicite de schéma ;
3. maintenir le comportement métier historique ;
4. moderniser Python, wxPython et les dépendances par corrections ciblées ;
5. conserver le code source compatible Windows, macOS et Linux lorsque c'est raisonnablement possible ;
6. produire en priorité un portable Windows reproductible.

## Runtime de référence

La baseline de production reste **Python 3.10**.

Python 3.11 et 3.12 ont été qualifiés par des workflows dédiés, conservés pour des requalifications ponctuelles avant des jalons importants. Ils ne sont pas encore la baseline de distribution.

wxPython Phoenix est utilisé sur les plateformes modernes. La CI vérifie les API historiques réellement encore employées et évite les remplacements cosmétiques lorsqu'un alias reste supporté.

## Installation de l'environnement

Pour les audits et tests sans GUI, un Python 3.10 suffit avec les dépendances nécessaires au scénario concerné.

Pour reproduire le build Windows complet :

```bash
python -m pip install --upgrade pip wheel
python -m pip install -r requirements-build.txt
```

`requirements-build.txt` inclut la chaîne nécessaire à PyInstaller et aux piles fonctionnelles vérifiées pendant le packaging.

## Organisation du dépôt

- `noethys/` : application historique et code métier ;
- `noethys/Ctrl/` : contrôles wxPython ;
- `noethys/Dlg/` : dialogues et écrans métier ;
- `noethys/Ol/` : listes/ObjectListView ;
- `noethys/Utils/` : services, fichiers, sauvegarde, intégrations et utilitaires ;
- `noethys/Data/` : descriptions et données structurelles ;
- `tests/` : tests unitaires/non-régression ;
- `scripts/` : audits, smoke tests et outils de recette ;
- `packaging/` : spec PyInstaller et runtime hooks ;
- `.github/workflows/` : CI multi-plateforme et packaging Windows ;
- `docs/` : roadmap, décisions, procédures de qualification et documentation du fork.

Le point d'entrée historique reste :

```text
noethys/Noethys.py
```

## Tests de non-régression

La suite métier complète s'exécute avec :

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

Elle couvre notamment :

- migration/copie de bases ;
- SQL strict des règlements ;
- exports comptables concernés ;
- passerelle PMSL ;
- restauration ;
- isolation du mode portable.

Une correction d'un défaut métier reproductible doit ajouter ou renforcer un test lorsqu'il est raisonnablement automatisable.

## Audits principaux

La CI exécute notamment :

- `scripts/audit_runtime_patterns.py` ;
- `scripts/audit_critical_business_modules.py` ;
- `scripts/audit_dynamic_import_risks.py` ;
- `scripts/audit_wxphoenix_compat.py` ;
- audits encodage, CSV, dates, bytes/texte et dépendances ;
- `scripts/check_schema_compatibility.py` ;
- base synthétique et benchmark lecture seule ;
- préflight Noe-030.

Ces outils sont des garde-fous. Un motif statique n'est pas automatiquement un bug : la règle reste de corriger les causes confirmées.

## Bases de données

### Invariants

- aucune migration implicite ;
- SQLite reste supporté ;
- la compatibilité avec les anciennes installations MySQL/MariaDB est conservée autant que possible ;
- ne pas introduire une fonctionnalité SQL nécessitant inutilement un serveur récent ;
- toute modification touchant les requêtes doit préserver la forme et la sémantique des résultats métier.

### Recette

Pour une base existante, utiliser :

```bash
python scripts/recette_existing_db_readonly.py --sqlite copie.dat --json avant.json
```

Puis, après la recette sur la copie :

```bash
python scripts/recette_existing_db_readonly.py \
  --sqlite copie.dat \
  --expect-schema-from avant.json \
  --json apres.json
```

Ne jamais utiliser l'unique base de production pour qualifier une branche ou une RC.

## wxPython et plateformes

La CI principale comporte :

- Windows : compilation, Phoenix, imports, `wx.App` et layout wx ;
- macOS : mêmes frontières techniques principales ;
- Linux GTK3 : wxPython système sous Xvfb, Phoenix, `wx.App` et layout représentatif.

Une CI verte valide le socle technique, pas chaque dialogue métier ni chaque périphérique.

## Packaging Windows

Le build s'effectue via :

```bash
pyinstaller --noconfirm --clean packaging/noethys.spec
```

Le layout `onedir` est volontairement **plat** (`contents_directory="."`) car `Chemins.py` résout historiquement les ressources depuis le dossier de `Noethys.exe`.

Le workflow `Package Windows` :

1. installe les dépendances ;
2. exécute les smoke tests fonctionnels ;
3. construit le bundle ;
4. vérifie ressources et layout ;
5. active le dossier historique `Portable/` ;
6. crée `BUILD-INFO.txt` ;
7. archive le dossier ;
8. ré-extrait l'archive ;
9. neutralise l'environnement Python du runner ;
10. exécute réellement l'EXE figé en mode smoke ;
11. publie `Noethys-Windows-portable`.

Le runtime hook de smoke quitte avant l'ouverture de la configuration ou d'une base utilisateur.

## Mode portable

La présence de `Portable/` à côté de l'EXE active le comportement historique :

- configuration dans `Portable/` ;
- bases locales dans `Portable/Data/` ;
- répertoires runtime sous `Portable/`.

Ne pas supprimer ce dossier lors d'une mise à jour d'une installation qui l'utilise : il peut contenir les données utilisateur.

## Style de modification attendu

- diff ciblé ;
- pas de refactorisation cosmétique massive ;
- pas de nouvelle fonctionnalité métier mélangée à un correctif de compatibilité ;
- conserver les interfaces historiques lorsque leur remplacement n'apporte pas de gain réel ;
- documenter les exceptions de plateforme ;
- ajouter un garde-fou lorsqu'une régression importante peut être reproduite automatiquement.

## Avant une PR ou une fusion

Au minimum :

```bash
python -m compileall -q noethys
python -m unittest discover -s tests -p 'test_*.py' -v
```

Pour tout changement touchant packaging, wxPython, base ou dépendances, s'appuyer ensuite sur les jobs GitHub Actions correspondants avant fusion.
