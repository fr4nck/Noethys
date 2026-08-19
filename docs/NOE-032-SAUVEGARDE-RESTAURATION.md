# Noe-032 — Sauvegarde et restauration

## Constats de l'audit

Le format de sauvegarde historique est conservé :

- `.nod` : archive ZIP non chiffrée ;
- `.noc` : archive chiffrée ;
- bases locales SQLite ajoutées telles quelles à l'archive ;
- bases réseau exportées via `mysqldump` puis réimportées via le client `mysql`.

L'audit a mis en évidence plusieurs `return False` mal indentés dans `UTILS_Sauvegarde.Restauration`. Ils provoquaient un arrêt inconditionnel après la confirmation de remplacement, après la première restauration SQLite et dans la restauration MySQL. Ces chemins sont maintenant couverts par des tests de non-régression.

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

Ces tests sont inclus automatiquement dans la suite métier Noe-031 (`tests/test_*.py`).

## Limites

La CI ne lance pas un serveur MySQL/MariaDB 5.5 réel pour écraser une base de production. Le test réseau simule le client `mysql` et protège le contrôle de flux. La compatibilité serveur réelle reste couverte par la stratégie conservatrice du projet et doit être confirmée sur une copie avant RC.
