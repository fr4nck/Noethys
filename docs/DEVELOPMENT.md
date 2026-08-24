# Développement — fork Upgrade Noethys

> Guide maintenu au 24 août 2026.

## Positionnement

Ce dépôt modernise Noethys Desktop sans réécriture métier. Les priorités de développement sont :

1. conserver les bases et configurations existantes ;
2. éviter toute migration implicite de schéma ;
3. maintenir le comportement métier historique sauf décision explicite ;
4. corriger les causes racines plutôt que masquer les symptômes ;
5. moderniser runtime, UI et architecture par lots ciblés ;
6. conserver Windows, macOS et Linux comme cibles du code source lorsque c'est raisonnablement possible ;
7. produire en priorité un portable Windows reproductible ;
8. conserver les décisions durables dans Git.

Lire également :

- `PROJECT_STATE.md` pour les décisions transversales ;
- `DESIGN_SYSTEM_UI_UX.md` pour la direction UI/UX ;
- `WXPYTHON_UI_RULES.md` pour les règles wxPython ;
- `ROADMAP.md` et `NOE-BACKLOG.md` pour le travail restant.

## Runtime de référence

La baseline de production reste **Python 3.10**.

Python 3.11 et 3.12 ont été qualifiés pour des revalidations ponctuelles mais ne sont pas encore la baseline de distribution.

wxPython Phoenix est utilisé sur les plateformes modernes. Les anciens aliases encore réellement supportés ne sont pas remplacés uniquement pour des raisons cosmétiques.

## Installation de l'environnement

Pour les audits et tests non GUI, utiliser Python 3.10 avec les dépendances du scénario concerné.

Pour reproduire le build Windows complet :

```bash
python -m pip install --upgrade pip wheel
python -m pip install -r requirements-build.txt
```

Sous Windows, la recette locale depuis les sources doit privilégier :

```text
DEV-Noethys.cmd
```

qui prépare le venv Python 3.10, applique les correctifs runtime validés et lance l'application avec les journaux de diagnostic dans `noethys/Portable/`.

## Organisation du dépôt

- `noethys/` : application historique et code métier ;
- `noethys/Ctrl/` : contrôles wxPython ;
- `noethys/Dlg/` : dialogues et écrans métier ;
- `noethys/Ol/` : listes/ObjectListView ;
- `noethys/Utils/` : services, fichiers, sauvegarde, intégrations et utilitaires ;
- `noethys/Data/` : descriptions et données structurelles ;
- `tests/` : tests unitaires et non-régression ;
- `scripts/` : audits, smoke tests et outils de recette ;
- `packaging/` : spec PyInstaller et runtime hooks ;
- `.github/workflows/` : CI, qualifications et packaging ;
- `docs/` : documentation actuelle et archives de décision.

Le point d'entrée historique reste :

```text
noethys/Noethys.py
```

## Tests de non-régression

Commande de base :

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

Elle couvre notamment SQL strict, base, exports comptables, restauration, mode portable et divers contrats métier/runtime.

Une correction d'un défaut reproductible doit ajouter ou renforcer un test lorsqu'il est raisonnablement automatisable.

Règle : tester un **invariant observable**, pas un détail d'implémentation sans valeur métier.

## Audits et garde-fous

Le dépôt dispose notamment d'audits runtime, SQL, imports dynamiques, compatibilité wxPython, encodages, dates, CSV, schéma et packaging.

Ces outils sont des garde-fous :

- un motif statique n'est pas automatiquement un bug ;
- une occurrence `REVIEW` demande une analyse ;
- ne pas transformer un audit en correcteur mécanique si la sémantique métier n'est pas démontrée.

## Bases de données

### Invariants

- aucune migration implicite ;
- SQLite reste supporté ;
- compatibilité MySQL/MariaDB historique conservée autant que possible ;
- ne pas introduire inutilement une fonction SQL réservée aux serveurs récents ;
- préserver cardinalité, ordre utile et sémantique des résultats.

### SQL strict

Ne pas :

- ajouter toutes les colonnes au `GROUP BY` mécaniquement ;
- utiliser `MIN()` / `MAX()` comme rustine sans invariant métier ;
- déduire qu'une requête classée `REVIEW` est nécessairement incorrecte.

Préférer les pré-agrégations et sous-requêtes lorsque cela préserve clairement la logique historique.

### Atomicité métier

Lorsqu'une action perçue comme unique écrit plusieurs objets liés, éviter les validations partielles.

Exemple déjà corrigé : sauvegarde d'un contrat PSU + prestations + consommations dans une transaction unique avec rollback en cas d'échec.

### Recette sur base existante

Utiliser une **copie**, jamais l'unique production.

Le préflight RC unifié est :

```bash
python scripts/rc_db_preflight.py ...
```

Les scripts de recette lecture seule peuvent également produire et comparer une empreinte de schéma.

## wxPython : règles obligatoires

Voir `WXPYTHON_UI_RULES.md` pour le détail.

Minimum à respecter :

- `parent` wxPython = vrai parent visuel ;
- contrôleur métier séparé lorsqu'il ne s'agit pas du parent visuel ;
- pas de `WXSUPPRESS_SIZER_FLAGS_CHECK` ;
- pas de fermeture/`EndModal()` prématurée pendant une construction incomplète ;
- corriger les flags/sizers invalides à la source ;
- éviter l'empilement de `SetSize`, `SetPosition`, `SetMinSize` et `CallAfter` comme système de layout ;
- pas de troncature artificielle de titre ;
- tester les contenus longs et l'échelle 100/120/150 % ;
- préserver les couleurs métier en thème sombre ;
- une CI verte ne remplace pas la validation visuelle.

Pour une correction GUI importante : compiler/importer, créer/détruire un vrai `wx.App(False)` lorsque possible et conserver un smoke ciblé du contrôle fautif.

## UI/UX

La référence canonique est `DESIGN_SYSTEM_UI_UX.md`.

Direction :

- Fluent 2 : grammaire desktop ;
- Material Design 3 : tokens, surfaces et thèmes ;
- Liquid Glass : inspiration très ciblée pour profondeur/couches fonctionnelles ;
- Fluent System Icons : iconographie principale.

Le socle transverse Repens est désormais intégré : listes/ObjectListView, grilles, outils communs de recherche/filtrage/cochage et navigation utilisent les règles communes. La suite ne consiste plus à ouvrir un chantier générique de modernisation : les corrections UI doivent partir d'un défaut concret observé en recette ou d'un besoin métier identifié.

Ne pas ajouter une dépendance lourde uniquement pour obtenir un effet visuel.

## Performance et freezes

Le fork dispose d'une instrumentation de performance Windows/MySQL distante.

Règles :

- mesurer avant d'optimiser ;
- distinguer temps de requête, latence réseau, blocage de la boucle UI et délai de layout ;
- ne pas ajouter un fondu ou délai artificiel pour cacher un traitement bloquant ;
- pendant l'investigation, conserver les actions lentes dans le journal prévu sans données métier sensibles.

## Packaging Windows

Build :

```bash
pyinstaller --noconfirm --clean packaging/noethys.spec
```

Le layout `onedir` reste volontairement plat (`contents_directory="."`) car `Chemins.py` résout historiquement les ressources depuis le dossier de `Noethys.exe`.

Le workflow de packaging :

1. installe les dépendances ;
2. exécute les contrôles prévus ;
3. construit le bundle ;
4. vérifie ressources et layout ;
5. active `Portable/` ;
6. crée `BUILD-INFO.txt` ;
7. archive ;
8. ré-extrait dans un dossier neuf ;
9. neutralise Python externe ;
10. exécute réellement l'EXE figé en mode smoke ;
11. publie l'artefact.

Le smoke s'arrête avant la recette d'une base utilisateur.

## Mode portable

La présence de `Portable/` à côté de l'EXE active le mécanisme historique.

Ne jamais supprimer ce dossier lors d'une mise à jour sans sauvegarde : il peut contenir configuration et bases locales.

## Architecture métier et projets voisins

Ne pas fusionner arbitrairement les responsabilités :

- Noethys : familles, consommations, prestations, facturation, structures/relations contractuelles et données métier ;
- PMSL-Équipe : RH/planning des intervenants ;
- Teamworks-CCNS : règles RH/CCNS et contrôle du temps ;
- Connecthys : portail synchronisé ;
- autres outils : intégrations explicites, idempotentes et découplées.

Les échanges doivent utiliser des identifiants stables et des interfaces contrôlées plutôt qu'un couplage direct aux tables entre projets.

## Style de modification attendu

- diff ciblé ;
- pas de reformatage massif sans valeur ;
- pas de fonctionnalité métier sans lien dans un correctif technique ;
- ne pas réécrire un mécanisme historique encore correct juste pour le moderniser ;
- documenter les exceptions de plateforme ;
- une correction centrale vaut mieux que des dizaines d'exceptions locales ;
- ajouter un garde-fou lorsqu'une régression importante peut être reproduite.

## CI rapide et qualification lourde

La séparation est désormais intégrée dans `.github/workflows/ci.yml` :

- PR et push `master` : un job rapide Ubuntu unique ;
- lancement manuel `workflow_dispatch` en mode `complete` : même porte d'entrée, puis recette synthétique, smokes Windows/macOS/Linux et packaging Windows.

`windows-package.yml` est un workflow réutilisable appelé par `ci.yml`. L'ancien workflow UI séparé a été supprimé ; les audits UI font partie de la validation rapide commune.

La règle documentaire reste : **les workflows présents sur `master` sont la description exécutable de la CI courante**. Ne jamais documenter une PR ouverte comme si elle était déjà intégrée.

## Avant une PR ou une fusion

Minimum :

```bash
python -m compileall -q noethys
python -m unittest discover -s tests -p 'test_*.py' -v
```

Pour tout changement touchant packaging, wxPython, base ou dépendances, s'appuyer ensuite sur les jobs GitHub Actions correspondants.

## Entretien documentaire

Une décision durable prise pendant une recette ou une conversation doit être portée par :

- le code/test si elle est exécutable ;
- une issue si du travail reste ;
- le document canonique correspondant si elle est architecturale ou transversale.

Voir `docs/README.md` pour savoir quel document est canonique et lequel est historique.
