# Noe-030 — Recette sur une base existante

> Procédure maintenue au 22 août 2026.

## Principe

La recette ne doit **jamais** démarrer sur la base de production. Elle se déroule sur une copie jetable afin de pouvoir tester les parcours métier qui écrivent réellement des données sans risque pour l'exploitation.

Le point d'entrée technique actuel avant RC est le préflight unifié :

```bash
python scripts/rc_db_preflight.py ...
```

Il regroupe les validations encore utiles de Noe-002, Noe-003, Noe-004 et Noe-030 :

- requête OL_Reglements et forme attendue ;
- diagnostic des prestations/cotisations ;
- audit des index avec plans/chronométrages ;
- structure, volumes et empreinte de schéma ;
- contrôles en lecture seule prévus par le scénario.

Les scripts spécialisés restent utiles pour diagnostiquer un sous-problème, mais le préflight RC unifié est la procédure de référence pour la qualification finale.

## Préparation

1. fermer Noethys ;
2. réaliser une sauvegarde indépendante ;
3. créer une copie dédiée à la recette ;
4. identifier le SHA exact du candidat à tester ;
5. vérifier que l'artefact Windows provient du même SHA via `BUILD-INFO.txt` ;
6. conserver les rapports du préflight avec cette copie.

## Phase A — Préflight en lecture seule

### SQLite

Utiliser une copie cohérente du fichier de base.

Le préflight doit :

- ouvrir la copie en lecture seule pour ses contrôles ;
- calculer/vérifier les empreintes prévues ;
- produire un résumé et les fichiers de diagnostic dans `tmp/rc-db-preflight/` ;
- ne pas modifier la copie pendant la phase de contrôle.

Conserver notamment :

```text
tmp/rc-db-preflight/RC-PREFLIGHT-SUMMARY.txt
```

ainsi que les JSON de diagnostic utiles.

### MySQL / MariaDB

Utiliser de préférence **une copie de la base sur une instance de recette**, jamais l'unique base de production.

Pour renforcer la phase de préflight :

- utiliser si possible un compte SQL `SELECT`-only ;
- conserver les versions/configurations historiques du serveur ;
- ne pas profiter de la recette pour migrer le serveur ou le schéma ;
- conserver les rapports produits par le préflight.

## Phase B — Recette métier sur copie jetable

La copie de recette peut ensuite être ouverte par Noethys et recevoir les écritures nécessaires au scénario.

### 1. Démarrage et interface

- ouverture complète de Noethys ;
- accueil et menus principaux ;
- absence de ressource/module manquant ;
- absence de fenêtre vide ou freeze immédiat ;
- fermeture/réouverture d'au moins quelques dialogues courants.

### 2. Apparence et échelle

Le candidat actuel contient des changements UI qui n'existaient pas lors de la première version de cette recette.

Vérifier :

- Système / Clair / Sombre ;
- accent réellement utilisé ;
- 100 % puis au moins l'échelle réelle du poste, notamment 120/125 % ou 150 % ;
- titres longs ;
- listes, grilles, boutons et toolbars ;
- absence d'assertion sizer ou de zone blanche illisible en thème sombre.

### 3. Familles / individus

- ouvrir plusieurs familles existantes ;
- ouvrir plusieurs fiches individus ;
- vérifier rattachements et données principales ;
- effectuer une modification bénigne puis enregistrer sur la copie.

### 4. Inscriptions

- consulter une inscription existante ;
- créer ou modifier une inscription de test ;
- vérifier activité, groupe et catégorie tarifaire ;
- vérifier la persistance après fermeture/réouverture.

### 5. Consommations / réservations

- consulter une période réelle ;
- ajouter/modifier/supprimer une consommation de test ;
- vérifier états et rattachements ;
- confirmer la cohérence après réouverture.

### 6. Prestations / facturation

- générer ou modifier une prestation de test ;
- générer une facture si le contexte le permet ;
- vérifier montants, libellés et compte payeur ;
- contrôler les effets sur les listes utilisées au quotidien.

### 7. Règlements

- saisir un règlement de test ;
- vérifier mode, ventilation et affichage ;
- contrôler les listes de règlements et dépôts concernées par Noe-002.

### 8. Exports comptables

- lancer le format réellement utilisé ;
- vérifier nombre d'écritures et totaux attendus ;
- si la configuration le prévoit, contrôler les formats concernés par Noe-003.

### 9. PDF / impressions

- générer au moins un PDF réel ;
- vérifier accents, caractères Unicode et chemin de sortie ;
- tester une impression physique uniquement si elle fait partie de l'usage à qualifier.

### 10. Sauvegarde / restauration

- produire au minimum une sauvegarde de la copie ;
- si la recette le permet, restaurer vers une seconde copie jetable ;
- rouvrir et contrôler les données essentielles.

## Phase C — Scénarios supplémentaires selon les fonctions utilisées

### Commandes de repas

Si utilisées :

- créer une commande sur une période réelle ;
- vérifier les journées ;
- tester un point de livraison regroupant plusieurs couples groupe/unité ;
- tester repas animateurs et total ;
- vérifier qu'aucune date d'un autre site ne fuit dans la commande.

### Contrats PSU

Si utilisés :

- créer/modifier un contrat de test ;
- vérifier prestations et consommations associées ;
- modifier/supprimer une période ;
- rouvrir le contrat ;
- confirmer l'absence d'état partiellement enregistré.

### MySQL distant

Si utilisé :

- ouvrir plusieurs écrans représentatifs ;
- observer les lenteurs éventuelles ;
- exploiter `noethys_perf.log` si nécessaire ;
- distinguer latence réseau, requête longue et vrai freeze UI.

### Connecthys / fonctions réseau

Si utilisées dans le SHA candidat :

- tester la synchronisation réellement configurée ;
- vérifier les modes de transport utilisés ;
- ne tester comme fonction RC que ce qui est effectivement fusionné dans le SHA candidat, pas les PR encore ouvertes.

## Phase D — Contrôle après recette

Après les manipulations :

1. fermer proprement Noethys ;
2. relancer les contrôles d'empreinte/préflight prévus ;
3. confirmer qu'aucune migration de schéma inattendue n'a eu lieu ;
4. conserver les rapports avant/après avec le SHA du candidat ;
5. noter toute anomalie avec une recette reproductible.

Les volumes et montants peuvent légitimement changer pendant la recette. En revanche, un écart de schéma non prévu est un signal d'arrêt à analyser.

## Critères de validation

Noe-030 est considérée complète lorsque :

- le préflight unifié fonctionne sur une copie d'une base réellement utilisée ;
- le portable du SHA candidat démarre réellement ;
- les parcours familles, individus, inscriptions, consommations, facturation, règlements et export sont validés ;
- les fonctions récentes déjà fusionnées et réellement utilisées ont été testées ;
- aucune migration de schéma inattendue n'est observée ;
- aucune donnée de production n'a été modifiée ;
- les anomalies éventuelles ont été corrigées ou explicitement documentées avant RC.

Les tests synthétiques de CI valident l'outillage et de nombreux invariants, mais **ne remplacent jamais cette recette sur une copie de base réelle**.

Voir également `RC-CHECKLIST.md` et `NOE-042-RC-READINESS.md`.
