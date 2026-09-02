# Noe-040 — Packaging Windows final

## Baseline

Le build Windows repose sur :

- Python 3.10 ;
- wxPython Phoenix ;
- PyInstaller 6.x en mode `onedir` ;
- `packaging/noethys.spec` ;
- toutes les dépendances de `requirements-build.txt`.

Un même dossier PyInstaller sert de source à deux distributions distinctes :

- **portable** : `Noethys-Windows-portable.zip`, avec marqueur `Portable/` et configuration isolée ;
- **installable** : `Noethys-Upgrade-Setup.exe`, construit avec Inno Setup depuis une copie du bundle **sans** marqueur `Portable/`.

Les deux artefacts doivent provenir du même SHA et conserver `BUILD-INFO.txt`.

## Contrôles avant build

Le workflow vérifie avant PyInstaller :

- compilation du code Python ;
- piles fonctionnelles optionnelles ;
- génération PDF Unicode ;
- ressources essentielles et destinations définies dans la spec.

## Contrôle du véritable exécutable

La qualification ne s'arrête pas à la présence de `Noethys.exe`.

Après construction du bundle commun :

1. le layout historique est vérifié ;
2. une copie **installable** est préparée sans `Portable/` ;
3. l'installateur Inno Setup est construit ;
4. l'installateur est exécuté silencieusement dans un répertoire neuf ;
5. un faux profil `%APPDATA%` contient une configuration sentinelle existante ;
6. l'exécutable installé est lancé depuis un autre répertoire contenant un faux `Config.json` ;
7. le smoke vérifie que la configuration active est exactement celle du profil utilisateur et qu'elle reste inchangée ;
8. le faux `Config.json` du répertoire courant doit rester intact ;
9. le dossier installable ne doit contenir aucun marqueur `Portable/` ;
10. le bundle commun reçoit ensuite le marqueur `Portable/`, est archivé, extrait dans un répertoire neuf puis exécuté avec `NOETHYS_FROZEN_SMOKE=1` ;
11. le portable doit retrouver ses ressources/dépendances sans Python externe et ne rien écrire dans le profil Windows de test.

## Migration de configuration

`UTILS_Fichiers.DeplaceFichiers()` ne considère comme sources historiques que des emplacements explicitement rattachés à Noethys :

- répertoire applicatif ;
- ancien sous-répertoire `Data` ;
- ancien `~/noethys`.

Le répertoire courant du processus n'est jamais une source de migration.

Lorsqu'une configuration existe déjà dans le profil utilisateur, elle est autoritaire et n'est pas remplacée. `Config.json.bak` suit le même contrat que `Config.json` lors d'une vraie migration legacy.

## Installateur système

`packaging/noethys-installer.iss` produit `Noethys-Upgrade-Setup.exe` avec les principes suivants :

- `AppId` stable ;
- réutilisation du répertoire d'une installation précédente compatible ;
- aucun fichier de configuration ou de données utilisateur embarqué ;
- aucune suppression de données utilisateur à la désinstallation ;
- raccourcis Windows uniquement vers `Noethys.exe` installé.

L'installateur complète le portable ; il ne le remplace pas.

## Piles vérifiées depuis le bundle portable

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

`BUILD-INFO.txt` est inclus avec :

- le commit Git ;
- la version Python ;
- l'identifiant du workflow ;
- la date UTC du build ;
- le marqueur du mode portable uniquement dans l'archive portable.

## Recette humaine obligatoire

La CI garantit la construction, la séparation installable/portable et le contrat minimal de préservation de configuration. Elle ne remplace pas la recette sur Windows réel.

Avant validation d'une RC, suivre `RC-CHECKLIST.md` et l'issue de recette installateur courante pour vérifier au minimum :

- installation propre ;
- mise à niveau d'une installation existante ;
- lancement depuis un répertoire courant étranger contenant un `Config.json` sentinelle ;
- séparation stricte entre configuration installable `%APPDATA%` et mode `Portable/` ;
- désinstallation sans suppression des données/configurations utilisateur ;
- retour arrière sur une copie distincte lorsque pertinent.

La recette doit toujours porter sur **le SHA exact candidat**. Toute correction post-recette impose de recommencer la qualification sur le nouvel artefact.

## Limite volontaire

Ces qualifications prouvent que les distributions Windows lancent leur Python embarqué, retrouvent leurs ressources et respectent le contrat de configuration. Elles ne remplacent pas la recette métier Noe-030 sur une copie de base réelle.
