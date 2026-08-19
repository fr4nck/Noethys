# Checklist de qualification RC

Cette checklist sépare les garanties déjà apportées par la CI des vérifications qui nécessitent encore une recette humaine avec une copie de base réelle.

## Déjà validé automatiquement

- compilation Python 3 ;
- audits runtime, encodages, dates, CSV et compatibilités wxPython ;
- absence de migration implicite du schéma dans les contrôles prévus ;
- suite complète de non-régression métier `tests/test_*.py` ;
- imports des piles fonctionnelles critiques ;
- génération PDF Unicode avec ReportLab ;
- sauvegarde/restauration sur scénarios synthétiques ;
- construction PyInstaller Windows `onedir` ;
- layout plat des ressources compatible avec `Chemins.py` ;
- présence de `Noethys.exe`, `Static`, `Versions.txt`, `Licence.txt` et `Icone.ico` ;
- extraction de l'archive dans un dossier neuf ;
- exécution réelle de l'EXE extrait sans Python externe ;
- imports des dépendances critiques depuis le bundle ;
- absence d'écriture dans le profil Windows pendant le smoke ;
- présence du dossier `Portable/` et tests d'isolation config/données ;
- génération d'un `BUILD-INFO.txt` traçant commit, version Python, run, mode portable et date ;
- création et publication de l'artefact `Noethys-Windows-portable`.

## Avant de déclarer une RC validée

1. utiliser le dernier artefact construit depuis le SHA candidat sur `master` ;
2. vérifier que le SHA dans `BUILD-INFO.txt` correspond au commit attendu ;
3. conserver une sauvegarde indépendante de la base utilisée pour la recette ;
4. lancer `Noethys.exe` manuellement sans toucher à l'unique base de production ;
5. vérifier le démarrage complet et l'affichage réel de l'accueil ;
6. ouvrir uniquement une copie d'une base existante ;
7. exécuter le préflight Noe-030 avant et après la recette ;
8. vérifier qu'aucune migration de schéma inattendue n'est proposée ou exécutée.

## Recette métier minimale

Tester au moins les parcours suivants :

- familles et individus ;
- activités, groupes et inscriptions ;
- consommations/réservations ;
- facturation ;
- règlements et ventilation ;
- comptabilité et export réellement utilisé ;
- génération d'au moins un PDF ;
- sauvegarde/restauration sur la copie si pertinent ;
- fermeture puis réouverture propre de l'application.

## Compatibilité des données historiques

Après la recette sur la copie :

- fermer Noethys modernisé ;
- comparer le `schema_digest` au rapport Noe-030 initial ;
- conserver une seconde copie de sauvegarde intacte ;
- rouvrir la base de recette avec la version historique lorsqu'il est pertinent de vérifier la compatibilité descendante ;
- contrôler qu'aucune altération incompatible n'a été introduite.

## Réseau et fonctions optionnelles

À tester uniquement si utilisées dans l'installation concernée :

- MySQL/MariaDB distant ;
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
- le démarrage réel de l'interface sous Windows est confirmé ;
- une copie de base existante s'ouvre et les parcours métier minimaux fonctionnent ;
- aucune migration implicite ou corruption n'est observée ;
- les limites connues sont documentées.

La compatibilité Linux et macOS du code source continue d'être vérifiée par la CI, mais une distribution utilisateur sur ces plateformes nécessite encore sa propre recette et sa propre chaîne de packaging.
