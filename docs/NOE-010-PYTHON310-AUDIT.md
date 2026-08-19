# Noe-010 — Audit de compatibilité Python 3.10+

## Conclusion

Python **3.10** est le runtime de référence actuel d'Upgrade Noethys.

Le code applicatif de premier niveau est déjà qualifié en CI sous Python 3.10 sur Linux, Windows et macOS. Le portable Windows moderne est également construit avec Python 3.10 et PyInstaller.

L'ancien `setup.py` reste un artefact de packaging Python 2 / py2exe et **ne doit pas être considéré comme le chemin de fabrication actuel**.

## Référence actuelle

### CI applicative

`.github/workflows/ci.yml` utilise Python 3.10 pour :

- compilation de l'arbre `noethys/` ;
- audits de motifs runtime ;
- génération d'une base de recette synthétique ;
- benchmark de lecture ;
- smoke tests des modules métier critiques ;
- test du migrateur DB vers DB ;
- audits bytes/texte, CSV, UTF-8, dates, imports dynamiques et arguments wx ;
- smoke tests Windows et macOS avec wxPython.

La PR Noe-003 (#24) a fourni une validation récente de ce socle : les jobs Linux, Windows et macOS ont terminé avec succès sous Python 3.10.

### Portable Windows

`.github/workflows/windows-package.yml` fixe également Python 3.10 et installe `requirements-build.txt`, puis :

1. compile les sources ;
2. valide les piles fonctionnelles optionnelles ;
3. valide ReportLab/Unicode ;
4. valide les ressources essentielles ;
5. construit `Noethys.exe` avec `packaging/noethys.spec` et PyInstaller.

`requirements-build.txt` retient actuellement PyInstaller `>=6.0,<7` et ajoute wxPython au jeu de dépendances runtime.

## Compatibilité du code premier niveau

`scripts/audit_runtime_patterns.py` surveille notamment :

- appels Python 2 résiduels (`unicode`, `basestring`, `raw_input`, `xrange`) ;
- `except:` nus ;
- `eval` / `exec` ;
- séquences d'échappement invalides ;
- encodage `mbcs` ;
- accès DB potentiellement fragiles.

Le CI applique actuellement une tolérance **zéro** à `PY2_BUILTINS` sur le code premier niveau audité.

Les répertoires tiers embarqués `ObjectListView/` et `Outils/` sont volontairement distingués du code Noethys maintenu : ils ne doivent pas masquer l'état de compatibilité du cœur applicatif.

## Dépendances

`requirements.txt` reste volontairement peu contraint en versions. Cela permet encore d'installer des versions adaptées à la plateforme, mais ne garantit pas à lui seul la reproductibilité d'un environnement dans le temps.

La reproductibilité et le verrouillage des versions relèvent des travaux de packaging/environnement futurs (notamment Noe-100/Noe-101), pas d'une migration implicite dans Noe-010.

## Cas particulier : `setup.py`

Le `setup.py` racine contient encore plusieurs constructions Python 2 historiques, notamment :

- `open(...).read().decode("utf8")` ;
- des instructions `print` sans parenthèses ;
- une configuration py2exe/VC90 ancienne.

Il n'est donc **pas** un point d'entrée de packaging Python 3 fiable.

Ce constat n'est pas bloquant pour le runtime actuel : le portable moderne utilise PyInstaller via `packaging/noethys.spec` et `.github/workflows/windows-package.yml`.

La bonne trajectoire est de retirer/remplacer proprement ce packaging historique lors du chantier dédié (`pyproject.toml` / environnement reproductible), plutôt que de le moderniser partiellement au risque de maintenir deux chaînes de fabrication concurrentes.

## Risques résiduels à surveiller

- dépendances non verrouillées : risque de dérive future des versions ;
- code tiers embarqué : compatibilité à traiter séparément quand une incompatibilité concrète apparaît ;
- chemins métier peu couverts par des tests automatisés : la recette fonctionnelle sur base existante reste indispensable ;
- Python 3.11 et 3.12 doivent être qualifiés séparément avant de relever le runtime de référence.

## Décision Noe-010

Le socle **Python 3.10 est considéré compatible et constitue la baseline** d'Upgrade Noethys.

Noe-010 ne demande pas de migration de base, ne change aucun format de données et ne nécessite pas de modification fonctionnelle. La suite logique est Noe-011 : qualification incrémentale de Python 3.11 sans abandonner la baseline 3.10 tant que la recette n'est pas terminée.
