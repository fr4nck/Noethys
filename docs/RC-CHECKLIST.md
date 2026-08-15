# Checklist de qualification RC

Cette checklist sépare les garanties déjà apportées par la CI des vérifications qui nécessitent encore une recette humaine avec une copie de base réelle.

## Déjà validé automatiquement

- compilation Python 3 ;
- audits runtime, encodages, dates, CSV et compatibilités wxPython ;
- absence de migration implicite du schéma dans les contrôles prévus ;
- imports des piles fonctionnelles critiques ;
- génération PDF Unicode avec ReportLab ;
- ressources essentielles du packaging ;
- construction PyInstaller Windows `onedir` ;
- présence de `Noethys.exe` ;
- génération d'un `BUILD-INFO.txt` traçant commit, version Python, run et date ;
- création et publication de l'artefact `Noethys-Windows-portable`.

## Avant de déclarer une RC testable

1. utiliser le dernier artefact construit depuis `master` ;
2. vérifier que le SHA dans `BUILD-INFO.txt` correspond au commit attendu ;
3. extraire l'archive dans un chemin comportant si possible espaces et accents ;
4. lancer `Noethys.exe` sans base de production ;
5. vérifier le démarrage complet, l'affichage de l'accueil et l'absence d'erreur de module, DLL ou ressource ;
6. ouvrir uniquement une copie d'une base existante ;
7. vérifier qu'aucune migration de schéma inattendue n'est proposée ou exécutée.

## Recette métier minimale

Tester au moins les parcours suivants :

- familles et individus ;
- activités, groupes et inscriptions ;
- consommations/réservations ;
- facturation ;
- règlements ;
- comptabilité ;
- génération d'au moins un PDF ;
- export CSV/XLSX utile ;
- formules et filtres ayant été modernisés ;
- fermeture puis réouverture propre de l'application.

## Compatibilité des données historiques

Après la recette sur la copie :

- fermer Noethys modernisé ;
- conserver une seconde copie de sauvegarde intacte ;
- rouvrir la base de recette avec la version historique lorsqu'il est pertinent de vérifier la compatibilité descendante ;
- contrôler qu'aucune altération incompatible n'a été introduite.

## Réseau et fonctions optionnelles

À tester uniquement si utilisées dans l'installation concernée :

- MySQL distant ;
- portail/Connecthys ;
- SFTP avec mémorisation de clé hôte ;
- FTPS si activé ;
- FTP historique, avec avertissement de connexion non chiffrée ;
- Mailjet et envoi de pièces jointes ;
- périphériques série, cartes, imprimantes et intégrations Windows ;
- synthèse vocale ;
- extensions Python utilisateur.

## Critères de décision

Une RC peut être publiée comme version de test lorsque :

- la CI du commit candidat est verte ;
- le packaging du même code est vert ;
- le démarrage réel sous Windows est confirmé ;
- une copie de base existante s'ouvre et les parcours métier minimaux fonctionnent ;
- aucune migration implicite ou corruption n'est observée ;
- les limites connues sont documentées.

La compatibilité Linux et macOS du code source continue d'être vérifiée par la CI, mais une distribution utilisateur sur ces plateformes nécessite encore sa propre recette et sa propre chaîne de packaging.
