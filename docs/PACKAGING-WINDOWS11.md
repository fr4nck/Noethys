# Packaging et modernisation Windows

## Statut

Le chantier de modernisation est intégré progressivement dans `master`.

Ce document décrit la chaîne de packaging Windows réellement utilisée et les validations encore nécessaires avant une RC.

## Objectif

Produire et qualifier un dossier autonome Noethys pour Windows avec Python 3.10, wxPython Phoenix et PyInstaller, sans migration implicite du schéma de base de données et sans remplacer immédiatement l'ancien `setup.py`.

Windows reste la cible de distribution prioritaire. Le code source demeure multi-plateforme et la CI valide également le socle sous Linux GTK3 et macOS.

## État actuel

La chaîne PyInstaller `onedir` couvre :

- installation des dépendances de fabrication ;
- compilation des sources ;
- imports des piles fonctionnelles optionnelles ;
- génération PDF ReportLab Unicode ;
- ressources essentielles PyInstaller ;
- construction de `Noethys.exe` ;
- création de l'archive ;
- **extraction dans un répertoire neuf et exécution réelle de `Noethys.exe`** ;
- publication de l'artefact GitHub Actions.

Chaque build contient `BUILD-INFO.txt` avec le SHA Git, la version Python, l'identifiant du run GitHub Actions et la date UTC de fabrication.

Le smoke de l'exécutable figé neutralise `PYTHONHOME` et `PYTHONPATH`, retire les chemins Python/pip du `PATH`, vérifie les ressources et plusieurs dépendances critiques depuis le bundle puis quitte avant l'ouverture de la configuration ou d'une base utilisateur. Il vérifie également qu'aucun répertoire Noethys n'a été créé dans le profil Windows de test.

Cela valide l'autonomie technique du bundle. Une recette métier sur poste Windows avec une copie de base réelle reste obligatoire avant RC.

## Stratégie de packaging

Le résultat reste volontairement un dossier `onedir` :

- démarrage et erreurs plus faciles à diagnostiquer ;
- ressources visibles ;
- dépendances manquantes identifiables ;
- retour arrière immédiat ;
- aucune installation système requise.

Le workflow `Package Windows` publie un artefact nommé `Noethys-Windows-portable`. Son archive contient `Noethys.exe`, les ressources nécessaires et `BUILD-INFO.txt`.

Le `.spec` reste sélectif : les suites de tests et backends inutiles des dépendances ne doivent pas être embarqués lorsqu'ils ne sont pas nécessaires au runtime.

## CI et contrôles automatisés

La CI couvre notamment :

- Python 3 et APIs modernisées ;
- frontières `bytes` / `str`, CSV et UTF-8 ;
- chemins de fichiers et SQLite ;
- parsing des dates ;
- arguments wxPython ;
- imports dynamiques et risques PyInstaller ;
- ressources embarquées ;
- Pillow et ReportLab Unicode ;
- modules métier critiques et suite de non-régression ;
- sauvegarde/restauration ;
- absence de migration implicite du schéma ;
- smoke tests wx sous Windows, macOS et Linux GTK3 ;
- lancement réel du bundle Windows extrait, sans environnement Python externe.

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
3. lancer un nouveau run si le workflow n'a pas déjà été déclenché ;
4. vérifier le SHA utilisé par le run ;
5. laisser les smoke tests puis PyInstaller s'exécuter ;
6. vérifier que l'étape **Tester l'archive extraite sans environnement Python** est verte ;
7. récupérer l'artefact `Noethys-Windows-portable` ;
8. ouvrir `BUILD-INFO.txt` et vérifier le SHA ;
9. conserver les logs du run en cas d'échec runtime.

Ne pas utiliser un ancien `Re-run jobs` pour qualifier une nouvelle révision : GitHub reconstruirait le SHA du run initial.

## Recette Windows attendue

Sur un poste Windows et avec une **copie** d'une base réelle :

1. extraire entièrement l'archive ;
2. contrôler `BUILD-INFO.txt` ;
3. lancer `Noethys.exe` normalement ;
4. vérifier l'affichage réel de l'interface ;
5. ouvrir une copie d'une base existante ;
6. parcourir familles, individus, inscriptions, facturation, règlements et comptabilité ;
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
- **exécution réussie de l'archive extraite sans Python externe** ;
- artefact traçable contenant l'exécutable et ses ressources ;
- ouverture manuelle de l'interface sur un poste Windows ;
- ouverture d'une copie de base existante ;
- recette minimale des modules critiques ;
- confirmation qu'aucune migration implicite de base n'a été introduite ;
- documentation à jour des limites restantes.

## Risques restant à qualifier humainement

Après les contrôles automatisés, les risques runtime restants sont principalement :

- comportements wxPython propres à certains dialogues ;
- impressions et périphériques ;
- accès réseau et bases distantes ;
- données historiques atypiques ;
- parcours métier moins fréquents ;
- compatibilité réelle du portail avec les serveurs utilisés en production.

Lorsqu'un défaut réel apparaît, corriger d'abord sa cause racine, ajouter un garde-fou reproductible lorsque c'est pertinent, puis relancer uniquement le niveau de validation nécessaire.
