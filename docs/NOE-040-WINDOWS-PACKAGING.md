# Noe-040 — Packaging Windows final

## Baseline

Le portable Windows est construit avec :

- Python 3.10 ;
- wxPython Phoenix ;
- PyInstaller 6.x en mode `onedir` ;
- `packaging/noethys.spec` ;
- toutes les dépendances de `requirements-build.txt`.

Le résultat est une archive `Noethys-Windows-portable.zip` contenant `Noethys.exe`, les bibliothèques embarquées et les ressources Noethys nécessaires.

## Contrôles avant build

Le workflow vérifie avant PyInstaller :

- compilation du code Python ;
- piles fonctionnelles optionnelles ;
- génération PDF Unicode ;
- ressources essentielles et destinations définies dans la spec.

## Contrôle du véritable exécutable

La qualification ne s'arrête plus à la présence de `Noethys.exe`.

Après construction :

1. le dossier est archivé ;
2. l'archive est extraite dans un répertoire neuf du runner ;
3. `PYTHONHOME` et `PYTHONPATH` sont vidés ;
4. les chemins Python/pip sont retirés du `PATH` ;
5. `Noethys.exe` est réellement lancé avec `NOETHYS_FROZEN_SMOKE=1` ;
6. un runtime hook vérifie que l'application est bien figée, que les ressources essentielles existent et que plusieurs dépendances critiques sont importables depuis le bundle ;
7. le processus doit sortir avec le code 0 ;
8. le smoke doit n'avoir créé aucun répertoire de configuration/données Noethys dans le profil Windows de test.

Le mode smoke s'arrête **avant** l'exécution de `Noethys.py` : il ne sélectionne, n'ouvre et ne migre donc aucune base utilisateur.

## Piles vérifiées depuis le bundle

Le smoke figé charge notamment :

- wxPython ;
- Pillow ;
- ReportLab ;
- python-dateutil / pytz ;
- lxml ;
- `mysql.connector` ;
- `MySQLdb` / mysqlclient ;
- PyCryptodome ;
- cryptography ;
- requests.

Ce contrôle complète les smoke tests fonctionnels exécutés avant le build.

## Identification du build

`BUILD-INFO.txt` est inclus dans le dossier portable avec :

- le commit Git ;
- la version Python ;
- l'identifiant du workflow ;
- la date UTC du build.

## Limite volontaire

Cette qualification prouve qu'une archive extraite lance son Python embarqué et retrouve ses ressources/dépendances sans utiliser l'environnement Python du runner. Elle ne remplace pas la recette métier Noe-030 sur une copie de base réelle.
