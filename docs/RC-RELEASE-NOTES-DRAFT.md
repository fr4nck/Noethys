# Noethys Upgrade — notes de Release Candidate (brouillon)

> Brouillon préparatoire. Ne pas publier comme RC validée avant la recette Noe-030 sur une copie de base réelle.

## Objectif de cette RC

Cette Release Candidate vise à rendre Noethys Desktop exploitable sur un environnement Python/wxPython moderne tout en conservant au maximum les bases, configurations et usages historiques.

La priorité est la compatibilité et la fiabilité ; il ne s'agit pas d'une réécriture fonctionnelle de Noethys.

## Principales évolutions

### Runtime moderne

- Python 3.10 comme baseline de production ;
- qualification prospective Python 3.11 et 3.12 ;
- wxPython Phoenix ;
- corrections ciblées des incompatibilités Python/wx réellement confirmées ;
- modernisation des frontières encodage, dates, fichiers et dépendances nécessaires.

### Bases de données

- maintien de SQLite ;
- stratégie conservatrice pour les installations MySQL/MariaDB historiques ;
- aucune migration implicite de schéma introduite par le chantier ;
- audit SQL strict et correction des requêtes concernées ;
- préflight lecture seule pour qualifier une copie de base existante ;
- contrôle d'empreinte de schéma avant/après recette.

### Fiabilité métier

- tests de non-régression exécutés automatiquement en CI ;
- couverture des migrations/copies de base ;
- couverture des règlements et de leurs ventilations ;
- couverture des exports comptables concernés par SQL strict ;
- couverture des échanges PMSL ajoutés au fork ;
- réparation de chemins historiques de restauration qui pouvaient échouer systématiquement.

### Windows portable

- build PyInstaller `onedir` reproductible ;
- layout plat compatible avec la résolution historique des ressources Noethys ;
- archive Windows identifiable par `BUILD-INFO.txt` ;
- extraction et exécution réelle de `Noethys.exe` en CI sans environnement Python externe ;
- contrôle des ressources et dépendances embarquées ;
- isolation portable historique via le dossier `Portable/` dès validation de Noe-041.

### Compatibilité multi-plateforme du code source

- smoke tests Windows ;
- smoke tests macOS ;
- smoke tests Linux GTK3 sous X virtuel ;
- tests de layout wxPython représentatifs.

La distribution utilisateur prioritaire de cette RC reste Windows. macOS et Linux sont qualifiés au niveau du code source, sans promesse de paquet utilisateur équivalent au portable Windows.

## Compatibilité

Cette RC est conçue pour rester compatible avec les données et configurations historiques autant que possible. La règle du projet reste :

- pas de migration de base silencieuse ;
- pas de remplacement automatique de la base ;
- pas de recette sur l'unique base de production ;
- test préalable sur une copie réelle avant adoption.

## Limites connues de la RC

Ne sont pas inclus comme exigences de cette première RC :

- installateur Windows système ;
- signature de code ;
- package macOS signé/notarisé ;
- package Linux ;
- bascule de la baseline vers Python 3.11/3.12 ;
- migration imposée vers une version MySQL/MariaDB récente ;
- transformation de Noethys Desktop en application web.

## Validation encore requise avant publication

Avant de transformer ce brouillon en notes de RC publiables :

1. fusionner Noe-041 ;
2. sélectionner le SHA candidat sur `master` ;
3. obtenir CI + packaging verts sur ce SHA ;
4. tester le portable sur Windows ;
5. ouvrir une **copie** d'une base Noethys réellement utilisée ;
6. exécuter la recette métier Noe-030 ;
7. vérifier l'absence de changement de schéma inattendu ;
8. consigner et corriger tout défaut bloquant.
