# Noe-041 — Mode portable Noethys

## Fonctionnement historique conservé

Noethys possède déjà un mécanisme de mode portable : lorsque le dossier `Portable` existe à côté de `Noethys.exe`, `UTILS_Fichiers` redirige la configuration et les données vers ce dossier au lieu d'utiliser les emplacements du profil utilisateur Windows.

Le packaging moderne active désormais explicitement ce mécanisme dans l'archive `Noethys-Windows-portable.zip`.

## Arborescence

Une archive fraîche contient notamment :

```text
Noethys.exe
BUILD-INFO.txt
Static/
Portable/
  README.txt
```

À l'utilisation, les sous-dossiers nécessaires sont créés à la demande :

```text
Portable/
  Config.json
  Customize.ini
  journal.log
  Data/
  Temp/
  Updates/
  Lang/
  Sync/
  Extensions/
```

## Isolation

En mode portable :

- `GetRepUtilisateur()` pointe dans `Portable/` ;
- `GetRepData()` pointe dans `Portable/Data/` ;
- les répertoires temporaires, mises à jour, langues, synchronisation et extensions sont créés sous `Portable/` ;
- le mécanisme `appdirs` normal n'est pas utilisé pour ces chemins.

La présence du dossier `Portable` reste le déclencheur historique. Les installations classiques sans ce dossier conservent donc leur comportement habituel.

## Mise à jour d'un portable existant

Ne jamais supprimer le dossier `Portable` lors d'une mise à jour : il peut contenir la configuration et les bases locales.

La méthode prudente est :

1. sauvegarder le dossier portable existant ;
2. extraire la nouvelle version dans un nouveau dossier ;
3. pour une recette, copier uniquement une **copie** des données nécessaires ;
4. valider la nouvelle version avant de remplacer l'ancien dossier applicatif.

## Recette avec base réelle

Pour Noe-030 et la future RC :

- travailler sur une copie de la base ;
- placer cette copie dans `Portable/Data/` si la recette est locale ;
- conserver l'original hors du portable de test ;
- après recette, vérifier l'absence de changement de schéma inattendu avec l'outil Noe-030.

## Couverture automatisée

`tests/test_noe_041_portable_paths.py` vérifie que :

- la présence de `Portable/` redirige bien configuration et données ;
- `Data`, `Temp`, `Updates`, `Lang`, `Sync` et `Extensions` sont créés à la demande ;
- les chemins `appdirs` ne sont pas utilisés en mode portable.

Le workflow Windows vérifie également que le marqueur portable est présent après extraction de l'archive finale.
