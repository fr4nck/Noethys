# Préflight base unifié avant RC

Le dernier contrôle technique sur une base réellement utilisée peut être lancé en **une seule commande**. Il regroupe Noe-002, Noe-003, Noe-004 et le préflight Noe-030, sans modifier les données.

## SQLite

Toujours travailler sur une **copie** de la base, Noethys fermé au moment de la copie :

```bash
python scripts/rc_db_preflight.py --sqlite "C:\\chemin\\vers\\copie-noethys.dat"
```

Le script ouvre la copie en lecture seule (`mode=ro` + `query_only`), vérifie notamment que son SHA-256 n'a pas changé pendant l'audit et produit les rapports dans `tmp/rc-db-preflight/`.

## MySQL / MariaDB

Utiliser de préférence une **copie de la base** et un compte SQL disposant uniquement du droit `SELECT`.

Sous PowerShell :

```powershell
$env:NOETHYS_DB_PASSWORD = "mot-de-passe-du-compte-de-recette"
python scripts/rc_db_preflight.py `
  --mysql-host 127.0.0.1 `
  --mysql-database noethys_recette `
  --mysql-user noethys_recette_ro
```

Le mot de passe n'est ni écrit dans le rapport ni passé sur la ligne de commande.

## Résultat à conserver

Le fichier à regarder en premier est :

`tmp/rc-db-preflight/RC-PREFLIGHT-SUMMARY.txt`

Il donne quatre états :

- **Noe-002** : la requête réelle de liste des règlements s'exécute et retourne bien ses 26 colonnes ;
- **Noe-003** : nombre non nominatif de prestations partagées par plusieurs cotisations ;
- **Noe-004** : couverture des candidats d'index, plans `EXPLAIN` et chronométrages en lecture seule ;
- **Noe-030** : structure générale, empreinte du schéma et contrôle de la copie.

`PASS` signifie que le préflight automatisé n'a trouvé aucun blocage. `REVIEW` signifie qu'un point doit être examiné avant RC, par exemple une prestation partagée entre plusieurs cotisations.

Les fichiers JSON détaillés restent dans le même répertoire. Ils ne contiennent pas de noms, prénoms, adresses, emails ni valeurs de clés métier utilisées pour les mesures d'index.

## Après le préflight

Ce contrôle automatise la partie lecture seule. La toute dernière recette avant RC reste le parcours métier sur une **copie jetable** décrit dans `NOE-030-RECETTE-BASE-EXISTANTE.md` : ouverture, familles/individus, inscription, facturation, règlement, export comptable, fermeture/réouverture.
