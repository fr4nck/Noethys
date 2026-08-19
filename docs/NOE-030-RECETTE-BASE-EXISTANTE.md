# Noe-030 — Recette sur une base existante

## Principe

La recette ne doit **jamais** démarrer sur la base de production. Elle se déroule sur une copie jetable afin de pouvoir tester les parcours métier qui écrivent réellement des données sans risque pour l'exploitation.

Le contrôle automatisé fourni par `scripts/recette_existing_db_readonly.py` ne lit que la structure et des agrégats. Il n'exporte aucun nom, prénom, adresse, email ni ligne métier nominative.

## Phase A — Préflight en lecture seule

### SQLite

1. Fermer Noethys afin d'obtenir une copie cohérente de la base.
2. Copier la base vers un fichier de recette, par exemple `recette-avant.dat`.
3. Lancer :

```bash
python scripts/recette_existing_db_readonly.py \
  --sqlite recette-avant.dat \
  --json recette-avant.json
```

Le script :

- calcule le SHA-256 de la copie avant l'audit ;
- ouvre SQLite avec `mode=ro` et active `PRAGMA query_only=ON` pour la session ;
- exécute uniquement des lectures de structure, volumes, sommes et plages de dates ;
- recalcule le SHA-256 après l'audit ;
- échoue si le fichier a changé ;
- enregistre un `schema_digest` permettant de détecter une modification ultérieure du schéma.

Conserver `recette-avant.json` avec la copie utilisée pour la recette.

### MySQL / MariaDB

Utiliser de préférence **une copie de la base sur une instance de recette**, jamais la base de production.

Pour renforcer la garantie côté serveur, utiliser un compte SQL réservé à la recette avec des droits `SELECT` uniquement pendant le préflight.

Exemple :

```bash
export NOETHYS_DB_PASSWORD='mot-de-passe-du-compte-lecture'
python scripts/recette_existing_db_readonly.py \
  --mysql-host 127.0.0.1 \
  --mysql-port 3306 \
  --mysql-database noethys_recette \
  --mysql-user noethys_recette_ro \
  --json recette-avant.json
```

Le script refuse toute requête qui n'est pas un `SELECT` ou un `SHOW`, désactive l'autocommit et termine la connexion par un rollback. Cette stratégie reste compatible avec les anciens serveurs MySQL/MariaDB ; elle n'impose aucune migration ni fonctionnalité SQL récente.

## Phase B — Recette métier sur copie jetable

Créer une **seconde copie** issue du même état initial et l'ouvrir avec la version de Noethys à qualifier. Cette copie est volontairement jetable : les écritures nécessaires à la recette y sont autorisées.

Parcours minimal :

1. **Ouverture**
   - ouverture de la base existante sans conversion ou migration implicite inattendue ;
   - navigation dans l'accueil et les menus principaux.
2. **Familles / individus**
   - ouvrir plusieurs familles existantes ;
   - ouvrir les fiches individus et vérifier les liens/rattachements ;
   - effectuer une modification bénigne puis l'enregistrer sur la copie.
3. **Inscriptions**
   - consulter une inscription existante ;
   - créer ou modifier une inscription de test ;
   - vérifier groupe, activité et catégorie tarifaire.
4. **Prestations / facturation**
   - générer ou modifier une prestation de test ;
   - générer une facture si le contexte de la copie le permet ;
   - vérifier montants, libellés et rattachement à la famille.
5. **Règlements**
   - saisir un règlement de test ;
   - vérifier son affichage, son mode de règlement et sa ventilation ;
   - contrôler les listes de règlements et dépôts concernées par Noe-002.
6. **Exports comptables**
   - lancer au moins le format réellement utilisé ;
   - si disponibles dans la configuration, vérifier également QuadraCOMPTA et Cerig, concernés par Noe-003 ;
   - comparer le nombre d'écritures et les totaux attendus.
7. **Sauvegarde / restauration**
   - le scénario détaillé relève de Noe-032 ;
   - au minimum, vérifier qu'une sauvegarde de la copie peut être produite avant toute RC.

## Contrôle après recette

Après les manipulations métier, exécuter à nouveau le préflight sur la copie modifiée :

```bash
python scripts/recette_existing_db_readonly.py \
  --sqlite recette-apres.dat \
  --expect-schema-from recette-avant.json \
  --json recette-apres.json
```

ou l'équivalent MySQL/MariaDB.

Les **volumes et montants peuvent légitimement changer** pendant la recette. En revanche, le `schema_digest` doit rester identique tant qu'aucune migration de schéma n'a été explicitement prévue et validée.

Un écart de schéma est donc un signal d'arrêt à analyser avant toute utilisation sur une vraie base.

## Critères de validation

La recette Noe-030 est considérée complète lorsque :

- le préflight lecture seule fonctionne sur une copie d'une base Noethys réellement utilisée ;
- la copie passe les parcours familles, individus, inscriptions, facturation, règlements et export ;
- aucune migration de schéma inattendue n'est observée ;
- aucune donnée de production n'est modifiée par la qualification ;
- les anomalies éventuelles sont consignées avant la RC.

Les tests synthétiques de CI valident l'outil et ses garde-fous, mais **ne remplacent pas cette recette sur une copie de base réelle**.
