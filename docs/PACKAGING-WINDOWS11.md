# Packaging et modernisation Windows

## Statut

Le chantier de modernisation est désormais intégré progressivement **directement dans `master`**. La PR #2 reste ouverte uniquement comme réservoir historique de lots à extraire ; elle ne doit pas être fusionnée en bloc.

Ce document décrit donc la chaîne de packaging réellement présente dans `master` et les validations encore nécessaires avant une RC.

## Objectif

Produire et qualifier un dossier portable Noethys pour Windows avec Python 3.10, wxPython 4 et PyInstaller, sans migration implicite du schéma de base de données et sans remplacer immédiatement l'ancien `setup.py`.

La cible de recette utilisateur prioritaire reste Windows 11. Le code source demeure toutefois multi-plateforme et la CI valide également le socle sur Linux et macOS.

## État actuel

La chaîne de fabrication PyInstaller `onedir` fonctionne sur `master` :

- installation des dépendances de fabrication : validée ;
- compilation des sources : validée ;
- imports des piles fonctionnelles optionnelles : validés ;
- génération PDF ReportLab Unicode : validée ;
- ressources essentielles PyInstaller : validées ;
- construction de `Noethys.exe` : validée ;
- création de l'archive portable : validée ;
- publication de l'artefact GitHub Actions : validée.

Chaque build contient désormais un fichier `BUILD-INFO.txt` indiquant notamment le SHA Git, la version Python, l'identifiant du run GitHub Actions et la date UTC de fabrication. Cela permet d'identifier sans ambiguïté le code contenu dans une archive de recette.

Un build réussi valide la chaîne de fabrication, **pas encore la compatibilité fonctionnelle complète** : une recette sur poste Windows avec une copie de base réelle reste obligatoire avant RC.

## Stratégie de packaging

Le résultat reste volontairement un dossier `onedir` :

- démarrage et erreurs plus faciles à diagnostiquer ;
- ressources visibles ;
- dépendances manquantes identifiables ;
- retour arrière immédiat ;
- aucune installation système requise.

Le workflow `Package Windows` publie un artefact nommé `Noethys-Windows-portable`. Son archive contient `Noethys.exe`, les ressources nécessaires et `BUILD-INFO.txt`.

Le `.spec` doit rester sélectif : les suites de tests et backends inutiles des dépendances ne doivent pas être embarqués dans l'application portable lorsqu'ils ne sont pas nécessaires au runtime.

## CI et contrôles automatisés

La CI couvre notamment :

- compatibilité Python 3 et API modernes ;
- frontières `bytes` / `str` ;
- encodages texte et UTF-8 ;
- CSV, JSON et XML ;
- chemins de fichiers et SQLite ;
- parsing fragile des dates ;
- arguments numériques wxPython ;
- imports dynamiques et risques PyInstaller ;
- ressources embarquées ;
- dépendances utilisées ;
- Pillow ;
- génération PDF ReportLab avec Unicode ;
- modules métier critiques ;
- absence de migration implicite du schéma ;
- smoke-tests Windows et macOS.

La règle reste de corriger les défauts confirmés, sans transformation massive fondée uniquement sur un motif statique.

## Contraintes du lot

- aucune migration implicite de base ;
- aucune évolution métier mélangée à la modernisation ;
- aucun installateur système pour cette première RC ;
- aucune signature de code à ce stade ;
- pas de refactorisation cosmétique globale ;
- pas de workflow temporaire conservé après usage ;
- correction des causes confirmées plutôt que multiplication des rustines.

## Procédure de fabrication

Depuis `master` :

1. vérifier que la CI du SHA à qualifier est verte ;
2. ouvrir GitHub Actions > `Package Windows` ;
3. lancer un nouveau run si le workflow n'a pas déjà été déclenché par une modification de packaging ;
4. vérifier le SHA utilisé par le run ;
5. laisser les smoke-tests puis PyInstaller s'exécuter ;
6. vérifier la présence de `Noethys.exe` ;
7. récupérer l'artefact `Noethys-Windows-portable` ;
8. ouvrir `BUILD-INFO.txt` et vérifier que le SHA correspond bien à la révision à tester ;
9. conserver les logs du run en cas d'échec runtime.

Ne pas utiliser un ancien `Re-run jobs` pour qualifier une nouvelle révision : GitHub reconstruit alors le SHA du run initial.

## Recette Windows attendue

Sur un poste Windows 11 et avec une **copie** d'une base réelle :

1. extraire entièrement l'archive portable ;
2. contrôler `BUILD-INFO.txt` ;
3. lancer `Noethys.exe` ;
4. vérifier le démarrage sans DLL, module ou ressource manquante ;
5. ouvrir une copie d'une base existante ;
6. parcourir les zones principales : familles, individus, inscriptions, facturation, règlements et comptabilité ;
7. tester au moins une édition ou impression PDF ;
8. tester les exports utiles et les chemins comportant espaces ou accents ;
9. tester, si utilisée, la synchronisation portail et son mode FTP/FTPS/SFTP ;
10. fermer proprement l'application ;
11. rouvrir la même copie avec la version historique de Noethys afin de vérifier l'absence de migration ou d'altération incompatible.

Les impressions physiques, périphériques, bases distantes et parcours métier spécifiques restent à qualifier lorsqu'ils sont réellement utilisés.

## Critères avant RC

Une RC ne doit pas être déclarée uniquement parce que la CI et PyInstaller sont verts. Il faut au minimum :

- CI verte sur le SHA retenu ;
- packaging Windows réussi sur ce même SHA ;
- artefact traçable contenant l'exécutable et ses ressources ;
- démarrage réel sous Windows 11 ;
- ouverture d'une copie de base existante ;
- recette minimale des modules critiques ;
- confirmation qu'aucune migration implicite de base n'a été introduite ;
- documentation à jour des limites restantes.

## Risques restant à qualifier humainement

Même après un build PyInstaller réussi, les principaux risques runtime sont désormais surtout :

- comportements wxPython qui n'apparaissent qu'à l'ouverture de certains dialogues ;
- impressions et périphériques ;
- accès réseau et bases distantes ;
- données historiques atypiques ;
- parcours métier moins fréquents ;
- compatibilité réelle du portail avec les serveurs utilisés en production.

Lorsqu'un défaut réel apparaît, corriger d'abord sa cause racine, ajouter un garde-fou reproductible lorsque c'est pertinent, puis relancer uniquement le niveau de validation nécessaire.
