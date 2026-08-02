# Packaging Windows 11

## Objectif

Produire un dossier portable Noethys pour Windows 11 avec Python 3.10, wxPython 4 et PyInstaller, sans modifier le schéma de base de données ni remplacer immédiatement l'ancien `setup.py`.

## Stratégie

Le premier résultat est volontairement un dossier `onedir` :

- démarrage et erreurs plus faciles à diagnostiquer ;
- ressources visibles ;
- dépendances manquantes identifiables ;
- retour arrière immédiat ;
- aucune installation système requise.

Le build ne s'exécute pas sur chaque PR. Le workflow `Package Windows` est lancé manuellement depuis GitHub Actions et publie un artefact conservé 14 jours.

## Contenu ajouté

- `packaging/noethys.spec` : configuration PyInstaller ;
- `requirements-build.txt` : dépendances de fabrication ;
- `.github/workflows/windows-package.yml` : build manuel et archive portable.

## Contraintes

- aucune migration de base ;
- aucune évolution métier ;
- aucun mode sombre ;
- aucun installateur dans ce premier lot ;
- aucune signature de code dans ce premier lot.

## Validation attendue

1. le workflow fabrique `Noethys-Windows11-portable.zip` ;
2. l'archive contient `Noethys.exe` et les ressources statiques ;
3. l'application démarre sur Windows 11 ;
4. une copie de base existante s'ouvre ;
5. après une opération de recette, l'ancienne version ouvre toujours la même copie.

## Risques connus à qualifier par le premier build

- anciennes dépendances telles que `pyttsx` ;
- compilation de `mysqlclient` ;
- modules COM Windows ;
- imports dynamiques wxPython, Matplotlib, Twisted et ReportLab ;
- ressources ou DLL chargées par chemin relatif.

Le premier échec de build sera traité comme un résultat d'audit : seules les dépendances réellement nécessaires seront corrigées ou remplacées.
