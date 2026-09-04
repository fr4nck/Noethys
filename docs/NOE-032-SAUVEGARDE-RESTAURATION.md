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
- les archives temporaires `.nod` / `.noc` pouvaient subsister après certains échecs de copie ou d'envoi ;
- l'ordre `--single-transaction --opt` permettait à l'option groupée `--opt` de réactiver le verrouillage des tables.

Le correctif Noe-032b conserve les formats et la logique métier existants. Il ajoute des gardes et des nettoyages ciblés et corrige l'ordre des options de `mysqldump` :

- refus d'une sauvegarde ou restauration réseau sans paramètres de connexion ;
- fermeture explicite du ZIP avant les retours anticipés de création couverts ;
- suppression de `savetemp` et `restoretemp` sur le chemin nominal et sur les retours d'erreur MySQL couverts ;
- nettoyage garanti de ces répertoires même si `Popen`, `communicate()`, la création du fichier de connexion ou l'extraction SQL lève une exception ;
- commande `mysqldump` en `--opt --single-transaction --skip-lock-tables` ;
- tentative de fermeture du transport de messagerie après exception ;
- suppression des archives temporaires de travail sur les chemins de succès et d'échec explicitement gérés ;
- refus d'un SQL vide ou sans charge restauratrice avant lancement de `mysql` ;
- création d'une base MySQL absente uniquement après validation de la charge SQL, avec contrôle de l'échec de création ;
- après un retour `mysql` nul, reconnexion à la cible et exigence d'au moins une table ou vue avant de comptabiliser la restauration comme réussie.

## Complément Noe-032c — postcondition forte des restaurations MySQL

Le contrôle Noe-032b « code retour nul et au moins une table ou vue » ne prouvait pas que l'import avait atteint sa fin. Une interruption après quelques `CREATE TABLE` pouvait laisser des objets visibles et être prise à tort pour un succès.

Noe-032c remplace cette postcondition minimale par trois contrôles complémentaires :

1. **Intégrité du dump produit.** Chaque nouveau dump réseau reste stocké sous le même nom `<base>.sql` dans l'archive historique. Deux commentaires SQL compatibles avec les anciens clients l'encadrent désormais : un en-tête et un manifeste terminal contenant un identifiant, la taille exacte de la charge originale et son empreinte SHA-256. Une troncature ou une altération entre ces deux bornes est refusée avant création de la base et avant lancement de `mysql`.
2. **Marqueur terminal exécuté.** La restauration ajoute uniquement à la copie SQL extraite dans `restoretemp` la création puis l'alimentation d'une table au nom aléatoire. Cette instruction est placée après tout le dump. Après le retour du client, une nouvelle connexion doit retrouver la table et son jeton ; sinon l'import n'est pas considéré comme arrivé à son terme. Le marqueur est supprimé après la vérification, y compris sur les chemins d'échec couverts.
3. **Objets attendus réellement présents.** Le SQL validé est analysé pour recenser les tables ciblées par `CREATE`, `INSERT` ou `REPLACE`, ainsi que les vues, triggers, procédures, fonctions et événements créés. La postcondition compare cette liste avec `SHOW FULL TABLES` et, lorsque nécessaire, avec `information_schema`. Un marqueur présent ne suffit donc pas si un objet attendu manque ou n'a pas le bon type.

La compatibilité descendante est conservée :

- aucun membre obligatoire supplémentaire n'est ajouté au ZIP et les extensions `.nod` / `.noc` ne changent pas ;
- les lignes de manifeste sont des commentaires ignorés par les anciennes versions de MySQL et de Noethys ;
- un ancien dump sans manifeste reste restaurable s'il est non vide, se termine par une instruction SQL complète et expose au moins un objet persistant attendu ;
- les objets attendus d'un ancien dump sont dérivés du SQL disponible, puis le même marqueur terminal et la même postcondition sont appliqués.

Cette protection est une **détection de restauration partielle**, pas une transaction globale. Les DDL MySQL et certains effets du dump peuvent être validés implicitement ; en cas d'échec, les objets déjà modifiés peuvent donc rester partiellement restaurés et doivent être repris depuis une copie saine.

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
- succès complet d'un dump MySQL portant le manifeste Noe-032c ;
- succès d'un ancien dump complet sans manifeste ;
- analyse des objets de premier niveau d'un dump `mysqldump` avec commentaires conditionnels, fins de ligne CRLF et changements `DELIMITER`, sans confondre le SQL contenu dans le corps d'un trigger ;
- succès lorsque tables, vues, triggers, procédures, fonctions et événements attendus sont tous visibles dans les catalogues simulés ;
- refus d'un import interrompu après les premières instructions `CREATE TABLE`, même si le client simulé retourne zéro ;
- refus d'un marqueur terminal présent lorsque l'un des objets attendus manque ;
- refus d'un marqueur terminal présent lorsqu'un événement attendu manque dans `information_schema` ;
- refus avant appel à `mysql` d'un dump manifesté tronqué ;
- refus avant appel à `mysql` d'un ancien SQL tronqué au milieu d'une instruction ;
- refus d'un SQL sans effet (`SELECT 1;`) et absence de création d'une base manquante dans ce cas ;
- refus d'un retour `mysql` nul lorsque le marqueur terminal n'a pas été exécuté ;
- nettoyage du marqueur et de `restoretemp` sur les chemins couverts.

`tests/test_noe_032_backup_integrity.py` couvre les invariants Noe-032b et Noe-032c :

- refus d'une sauvegarde réseau sans paramètres de connexion ;
- création d'une archive réseau réussie dont le SQL contient un manifeste terminal vérifiable sans changement de nom de membre ;
- refus d'une charge SQL altérée à taille constante lorsque son empreinte ne correspond plus au manifeste ;
- fermeture du ZIP et suppression d'une archive partielle lorsqu'un fichier local manque ;
- suppression de `savetemp` et de l'archive partielle après échec simulé de `mysqldump` ;
- ordre des options transactionnelles de `mysqldump` ;
- confinement et nettoyage lorsqu'un appel à `Popen` lève pendant la sauvegarde ou la restauration ;
- confinement et nettoyage lorsqu'une extraction SQL échoue avant l'appel à `mysql` ;
- suppression de `restoretemp` après échec simulé du client `mysql` ;
- fermeture du transport de messagerie et suppression de l'archive temporaire après échec d'envoi.

Ces tests sont inclus automatiquement dans la suite métier Noe-031 (`tests/test_*.py`).

## Limites

La CI ne lance pas un serveur MySQL/MariaDB de production et n'écrase aucune base réelle. Les tests réseau simulent `mysqldump`, le client `mysql` et les catalogues du serveur afin de protéger le contrôle de flux, la postcondition et le nettoyage des ressources. Une qualification sur une copie dédiée reste requise avant RC.

La restauration MySQL reste non atomique : un échec après le début de l'import peut laisser une base partiellement modifiée. Noe-032c empêche de déclarer ce cas réussi, mais ne tente pas de l'annuler automatiquement.

Pour une nouvelle sauvegarde, le manifeste taille/empreinte permet de détecter une perte de fin du SQL. Pour un ancien dump sans aucune métadonnée terminale, une troncature nette exactement entre deux instructions complètes est indistinguable d'un dump volontairement plus court ; le marqueur prouve seulement que la totalité du fichier fourni a été exécutée. Ce risque résiduel est inhérent à l'absence de manifeste dans les archives historiques.
