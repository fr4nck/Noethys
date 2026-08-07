# Packaging et modernisation Windows 11

## Objectif

Produire et qualifier un dossier portable Noethys pour Windows 11 avec Python 3.10, wxPython 4 et PyInstaller, sans migration implicite du schéma de base de données et sans remplacer immédiatement l'ancien `setup.py`.

Ce chantier reprend les enseignements de la stabilisation de Teamworks-CCNS : détecter en amont les incompatibilités Python/wxPython/Windows, automatiser les contrôles reproductibles et réserver la recette humaine aux parcours qui nécessitent une vraie base ou une interface complète.

## État actuel

La branche de travail est `agent/windows11-pyinstaller` et la PR #2 constitue désormais un lot de modernisation plus large que le packaging initial. Elle reste volontairement en brouillon.

Un premier packaging Windows a déjà réussi sur le commit `2baaa7561ee4bdc1fb4f30c6dad514bfc64ee1e0` :

- installation des dépendances de fabrication : réussie ;
- compilation des sources : réussie ;
- construction PyInstaller `onedir` : réussie ;
- présence de `Noethys.exe` : vérifiée ;
- création de l'archive portable : réussie ;
- publication de l'artefact GitHub : réussie.

Ce résultat valide la chaîne de fabrication, mais ne qualifie pas encore la PR #2 actuelle : un nouveau packaging doit être effectué sur son HEAD avant qualification finale.

## Stratégie de packaging

Le résultat reste volontairement un dossier `onedir` :

- démarrage et erreurs plus faciles à diagnostiquer ;
- ressources visibles ;
- dépendances manquantes identifiables ;
- retour arrière immédiat ;
- aucune installation système requise.

Le packaging ne doit pas être lancé à chaque modification. Le workflow `Package Windows` est réservé aux validations utiles et publie l'artefact `Noethys-Windows11-portable` pendant 14 jours.

Attention : `Re-run jobs` reconstruit le commit du run d'origine. Pour qualifier le HEAD courant, il faut créer un nouveau run sur `agent/windows11-pyinstaller` et vérifier le SHA utilisé.

## CI frugale

La CI courante conserve une séparation entre contrôles fréquents et packaging coûteux :

- compilation Python et contrôles statiques dans la CI normale ;
- smoke-tests Windows ciblés pour les compatibilités runtime ;
- préflight statique sans PyInstaller pour détecter tôt les régressions ;
- packaging complet uniquement lorsqu'une nouvelle validation Windows est réellement nécessaire.

L'objectif est d'éviter les matrices et builds redondants tout en conservant une validation Windows réelle.

## Préflight

`scripts/package_preflight.py` orchestre les contrôles de préparation du packaging. Son manifeste est lui-même vérifié afin d'éviter les scripts absents, doublonnés ou mal classés.

Les contrôles couvrent notamment :

- compatibilité Python 3 et API modernes ;
- frontières `bytes` / `str` ;
- UTF-8 et fichiers texte ;
- CSV, JSON et XML ;
- chemins Windows et SQLite ;
- parsing fragile des dates ;
- arguments numériques wxPython et largeurs de listes ;
- layouts et cycle de vie wxPython ;
- imports dynamiques ;
- ressources embarquées ;
- dépendances utilisées ;
- Pillow et filtres de rééchantillonnage ;
- génération PDF ReportLab avec Unicode ;
- modules métier critiques ;
- alignement des hooks runtime et du fichier `.spec`.

Les audits informatifs ne doivent pas être transformés automatiquement en modifications massives. Une correction source n'est appliquée que lorsque son équivalence est sûre ou que le défaut est confirmé.

## Compatibilités runtime

Le packaging contient encore des hooks ciblés pour absorber certaines incompatibilités historiques, notamment autour de :

- wxPython / AUI ;
- ObjectListView ;
- Pillow ;
- anciennes constructions Python 2 ;
- SQLite et chemins Unicode ;
- cycle de vie GestionDB ;
- interface MySQL.

Ces hooks ne constituent pas une architecture définitive. Ils doivent être supprimés progressivement lorsque la correction source correspondante est prouvée et couverte par un test. L'audit `audit_runtime_hook_alignment.py` aide à détecter les hooks absents, orphelins ou dupliqués.

## UTF-8 et données

Le chantier vise UTF-8 comme convention de référence pour les fichiers texte et les échanges modernes, avec des smoke-tests de round-trip et de récupération de configuration.

Aucune conversion massive et aveugle des données historiques n'est autorisée. La compatibilité avec les bases existantes reste prioritaire et toute recette avec données réelles doit être effectuée sur une copie.

## Modules métier critiques

Le préflight analyse également le graphe d'imports des zones à fort risque sans ouvrir de base ni exécuter l'interface complète :

- familles et individus ;
- inscriptions ;
- prestations, facturation et règlements ;
- comptabilité ;
- éditions et impressions.

Cette validation ne remplace pas une recette fonctionnelle.

## Contraintes du lot

- aucune migration implicite de base ;
- aucune évolution métier ;
- aucun mode sombre dans ce lot ;
- aucun installateur système ;
- aucune signature de code ;
- pas de refactorisation cosmétique globale ;
- pas de nouveau workflow redondant ;
- correction des causes confirmées plutôt que multiplication des rustines.

## Procédure de fabrication

1. vérifier que la CI du HEAD de `agent/windows11-pyinstaller` est verte ;
2. ouvrir GitHub Actions > `Package Windows` ;
3. créer un nouveau run sur `agent/windows11-pyinstaller` ;
4. vérifier que le SHA du run correspond au HEAD attendu ;
5. laisser le préflight complet et PyInstaller s'exécuter ;
6. vérifier la présence de `Noethys.exe` ;
7. récupérer l'artefact `Noethys-Windows11-portable` ;
8. conserver les logs du run en cas d'échec runtime.

Ne pas utiliser un ancien `Re-run jobs` pour qualifier une nouvelle révision : GitHub réutilise alors le SHA du run initial.

## Recette Windows attendue

Sur un poste Windows 11 et avec une copie de base réelle :

1. extraire entièrement l'archive portable ;
2. lancer `Noethys.exe` ;
3. vérifier le démarrage sans DLL, module ou ressource manquante ;
4. ouvrir une copie d'une base existante ;
5. parcourir les zones principales : familles, individus, inscriptions, facturation, règlements et comptabilité ;
6. tester au moins une édition ou impression PDF ;
7. tester les exports utiles et les chemins comportant espaces ou accents ;
8. fermer proprement l'application ;
9. rouvrir la même copie avec la version historique de Noethys afin de vérifier l'absence de migration ou d'altération incompatible.

Les impressions physiques, périphériques, bases distantes, fonctions réseau et parcours métier spécifiques restent à qualifier lorsqu'ils sont réellement utilisés.

## Critères avant sortie de brouillon de la PR #2

La PR #2 ne doit pas être considérée comme qualifiée uniquement parce que la CI est verte. Avant de la sortir du statut brouillon, il faut au minimum :

- CI verte sur son HEAD ;
- packaging Windows réussi sur ce même HEAD ;
- artefact contenant l'exécutable et ses ressources ;
- démarrage réel sous Windows 11 ;
- ouverture d'une copie de base existante ;
- recette minimale des modules critiques ;
- confirmation qu'aucune migration implicite de base n'a été introduite ;
- documentation à jour des éventuelles limites restantes.

## Risques restant à qualifier

Même après un build PyInstaller réussi, les principaux risques runtime restent :

- dépendances anciennes ou optionnelles ;
- modules COM Windows ;
- imports réellement dynamiques ;
- ressources ou DLL chargées tardivement ;
- comportements wxPython qui n'apparaissent qu'à l'ouverture d'un dialogue ;
- impressions et périphériques ;
- accès réseau et bases distantes ;
- données historiques atypiques.

La règle reste la même que sur Teamworks : lorsqu'un défaut réel apparaît, corriger d'abord sa cause racine, ajouter un garde-fou reproductible lorsque c'est pertinent, puis relancer uniquement le niveau de validation nécessaire.
