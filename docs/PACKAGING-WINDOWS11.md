# Packaging et modernisation Windows 11

## Statut

Ce document décrit le chantier Windows 11 actuellement développé dans la branche `agent/windows11-pyinstaller` et suivi dans la PR #2.

Les éléments techniques décrits ici ne sont donc pas nécessairement tous présents dans `master` tant que la PR n'a pas été qualifiée et fusionnée.

## Objectif

Produire et qualifier un dossier portable Noethys pour Windows 11 avec Python 3.10, wxPython 4 et PyInstaller, sans migration implicite du schéma de base de données et sans remplacer immédiatement l'ancien `setup.py`.

Le chantier reprend les enseignements de la stabilisation de Teamworks-CCNS : détecter en amont les incompatibilités Python/wxPython/Windows, automatiser les contrôles reproductibles et réserver la recette humaine aux parcours qui nécessitent une vraie base ou une interface complète.

## État actuel

Un premier packaging Windows a déjà réussi sur le commit `2baaa7561ee4bdc1fb4f30c6dad514bfc64ee1e0` de la branche de modernisation :

- installation des dépendances de fabrication : réussie ;
- compilation des sources : réussie ;
- construction PyInstaller `onedir` : réussie ;
- présence de `Noethys.exe` : vérifiée ;
- création de l'archive portable : réussie ;
- publication de l'artefact GitHub : réussie.

Ce résultat valide la chaîne de fabrication, mais ne qualifie pas encore la version courante de la PR #2. Un packaging doit être effectué sur son HEAD actuel avant qualification finale.

## Stratégie de packaging

Le résultat reste volontairement un dossier `onedir` :

- démarrage et erreurs plus faciles à diagnostiquer ;
- ressources visibles ;
- dépendances manquantes identifiables ;
- retour arrière immédiat ;
- aucune installation système requise.

Le packaging complet ne doit pas être lancé à chaque modification. Le workflow `Package Windows` est réservé aux validations utiles et publie un artefact `Noethys-Windows11-portable`.

Attention : `Re-run jobs` reconstruit le commit du run d'origine. Pour qualifier le HEAD courant, il faut créer un nouveau run sur `agent/windows11-pyinstaller` et vérifier le SHA utilisé.

## CI et préflight

La branche de modernisation contient une CI frugale et un préflight destiné à éviter les builds inutiles. Les contrôles couvrent notamment :

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

La règle reste de corriger les défauts confirmés, sans lancer de transformation massive sur la seule base d'un motif statique.

## Contraintes du lot

- aucune migration implicite de base ;
- aucune évolution métier ;
- aucun mode sombre dans ce lot ;
- aucun installateur système ;
- aucune signature de code ;
- pas de refactorisation cosmétique globale ;
- pas de workflow redondant ;
- correction des causes confirmées plutôt que multiplication des rustines.

## Procédure de fabrication

Sur la branche de modernisation :

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

## Critères avant intégration

La PR #2 ne doit pas être considérée comme qualifiée uniquement parce que la CI est verte. Avant intégration, il faut au minimum :

- CI verte sur son HEAD ;
- packaging Windows réussi sur ce même HEAD ;
- artefact contenant l'exécutable et ses ressources ;
- démarrage réel sous Windows 11 ;
- ouverture d'une copie de base existante ;
- recette minimale des modules critiques ;
- confirmation qu'aucune migration implicite de base n'a été introduite ;
- documentation à jour des limites restantes.

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

Lorsqu'un défaut réel apparaît, corriger d'abord sa cause racine, ajouter un garde-fou reproductible lorsque c'est pertinent, puis relancer uniquement le niveau de validation nécessaire.
