# Noe-032 — Sauvegarde et restauration

## Constats de l'audit

Le format de sauvegarde historique est conservé :

- `.nod` : archive ZIP non chiffrée ;
- `.noc` : archive chiffrée ;
- bases locales SQLite ajoutées telles quelles à l'archive ;
- bases réseau exportées via `mysqldump` puis réimportées via le client `mysql`.

L'audit a mis en évidence plusieurs `return False` mal indentés dans `UTILS_Sauvegarde.Restauration`. Ils provoquaient un arrêt inconditionnel après la confirmation de remplacement, après la première restauration SQLite et dans la restauration MySQL. Ces chemins sont maintenant couverts par des tests de non-régression.

## Complément Noe-032b — intégrité des chemins d'échec

Le peigne fin du flux de création de sauvegarde a confirmé plusieurs défauts indépendants du format historique :

- une liste de bases réseau pouvait être demandée sans contexte de connexion et être silencieusement ignorée, avec un succès final potentiellement incomplet ;
- le ZIP temporaire pouvait rester ouvert sur certains retours anticipés ;
- `savetemp` et `restoretemp`, qui contiennent notamment `logintemp.cnf` avec les identifiants MySQL nécessaires aux outils en ligne de commande, n'étaient supprimés que sur le chemin nominal ;
- une erreur d'envoi de courriel ne garantissait pas la fermeture du transport ;
- les archives temporaires `.nod` / `.noc` pouvaient subsister après certains échecs de copie ou d'envoi.

Le correctif Noe-032b conserve les formats, les commandes MySQL et la logique métier existants. Il ajoute uniquement des gardes et des nettoyages ciblés :

- refus d'une sauvegarde ou restauration réseau sans paramètres de connexion ;
- fermeture explicite du ZIP avant les retours anticipés de création couverts ;
- suppression de `savetemp` et `restoretemp` sur le chemin nominal et sur les retours d'erreur MySQL couverts ;
- tentative de fermeture du transport de messagerie après exception ;
- suppression des archives temporaires de travail sur les chemins de succès et d'échec explicitement gérés.

## Précautions obligatoires

1. Ne jamais valider une restauration pour la première fois sur la base de production.
2. Conserver une copie indépendante de la base avant restauration.
3. Pour SQLite, tester l'archive dans un répertoire de recette et vérifier que les fichiers restaurés s'ouvrent correctement.
4. Pour MySQL/MariaDB, restaurer d'abord vers une base de recette dédiée ; ne pas utiliser la base en exploitation pour qualifier une nouvelle version.
5. Une restauration réussie techniquement ne remplace pas la recette métier Noe-030 : familles, inscriptions, prestations, règlements et exports doivent encore être vérifiés sur la copie.
6. Aucun changement de schéma ne doit apparaître implicitement pendant la restauration ou la première ouverture de la base restaurée.

## Couverture automatisée

`tests/test_noe_032_restore_flow.py` vérifie sans donnée utilisateur réelle :

- restauration d'un fichier SQLite depuis une archive `.nod` ;
- remplacement d'un fichier SQLite existant après confirmation ;
- chemin de restauration réseau avec import MySQL simulé réussi ;
- valeur de retour listant correctement les fichiers restaurés.

`tests/test_noe_032_backup_integrity.py` couvre les nouveaux invariants Noe-032b :

- refus d'une sauvegarde réseau sans paramètres de connexion ;
- fermeture du ZIP et suppression d'une archive partielle lorsqu'un fichier local manque ;
- suppression de `savetemp` et de l'archive partielle après échec simulé de `mysqldump` ;
- suppression de `restoretemp` après échec simulé du client `mysql` ;
- fermeture du transport de messagerie et suppression de l'archive temporaire après échec d'envoi.

Ces tests sont inclus automatiquement dans la suite métier Noe-031 (`tests/test_*.py`).

## Limites

La CI ne lance pas un serveur MySQL/MariaDB 5.5 réel pour écraser une base de production. Les tests réseau simulent `mysqldump` et le client `mysql` afin de protéger le contrôle de flux et le nettoyage des ressources. La compatibilité serveur réelle reste couverte par la stratégie conservatrice du projet et doit être confirmée sur une copie avant RC.

### Durcissement des processus MySQL

Le flux réseau garantit désormais le nettoyage de `savetemp` et `restoretemp` même si `Popen`, `communicate()`, la création du fichier de connexion ou l’extraction SQL lève une exception. La commande `mysqldump` applique `--opt --single-transaction --skip-lock-tables`, afin que l’option groupée `--opt` ne réactive pas le verrouillage des tables après l’activation du mode transactionnel.
