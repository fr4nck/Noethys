# Checklist de qualification RC

> Checklist maintenue au 24 août 2026.

Cette checklist sépare les garanties automatisées des vérifications qui nécessitent encore une recette humaine avec une copie de base réelle.

**Important : la recette doit porter sur le SHA réellement candidat à la publication.** Plusieurs fonctions ont été intégrées après la première préparation du sas RC ; un ancien artefact qualifié ne suffit donc pas à valider un nouveau SHA.

## Lecture rapide : un seul chemin critique

Le suivi pré-RC est centralisé dans **l'issue #19 (Noe-042)**. Les anciens lots techniques **#5 / Noe-002**, **#6 / Noe-003**, **#7 / Noe-004** et **#14 / Noe-030** sont clos comme lots d'implémentation/outillage ; leurs vérifications réelles sont intégrées au cockpit #19.

Avant de figer le SHA candidat, relire les inventaires statiques sur le `master` courant avec une seule commande :

```bash
python scripts/audit_pre_rc.py
```

Elle regroupe l'audit SQL strict, l'audit du cycle de vie/parentage wxPython et l'inventaire des anciens outils de listes. Les rapports sont écrits dans `tmp/pre-rc-audits/`.

Ces audits servent à **localiser** les zones à examiner. Ils ne doivent jamais déclencher une correction mécanique sans cause démontrée.

## Déjà couvert automatiquement par le socle

- compilation Python 3 ;
- audits runtime, encodages, dates, CSV et compatibilités wxPython ;
- garde-fous contre les migrations implicites prévues ;
- suite complète de non-régression métier `tests/test_*.py` ;
- imports des piles fonctionnelles critiques ;
- génération PDF Unicode ;
- sauvegarde/restauration sur scénarios automatisés ;
- construction PyInstaller Windows `onedir` ;
- layout plat des ressources compatible avec `Chemins.py` ;
- extraction de l'archive dans un dossier neuf ;
- exécution réelle de l'EXE extrait sans Python externe ;
- imports des dépendances critiques depuis le bundle ;
- isolation du mode `Portable/` ;
- génération de `BUILD-INFO.txt` ;
- smoke tests représentatifs Windows, macOS et Linux/GTK3 ;
- tests de contrat UI/DB ajoutés au fil des corrections lorsqu'ils sont automatisables ;
- socle transverse Repens des listes/ObjectListView, grilles, outils de liste, navigation et états vides ;
- CI rapide unifiée sur PR/push, qualification multi-OS et packaging réservés au mode manuel `complete` ;
- agrégateur d'inventaires pré-RC fusionné via PR #81.

## Avant de déclarer une RC validée

1. choisir un SHA candidat sur `master` ;
2. exécuter `python scripts/audit_pre_rc.py` et relire les rapports ;
3. lancer `CI Noethys` en mode `complete` pour ce SHA ;
4. utiliser l'artefact construit depuis **ce même SHA** ;
5. vérifier `BUILD-INFO.txt` ;
6. conserver une sauvegarde indépendante et une copie de recette ;
7. exécuter `scripts/rc_db_preflight.py` sur la copie avant ouverture ;
8. lancer `Noethys.exe` manuellement ;
9. vérifier l'accueil et l'absence de ressource/module manquant ;
10. exécuter la recette métier complète ;
11. effectuer la recette visuelle Windows ;
12. fermer/réouvrir l'application ;
13. exécuter le contrôle final de schéma/empreinte ;
14. corriger tout défaut bloquant puis recommencer sur un nouvel artefact si le SHA change ;
15. seulement ensuite déclencher le workflow `Release Candidate` et relire la release brouillon.

## Recette métier minimale historique

Tester au moins :

- familles et individus ;
- saisie/modification d'adresse, notamment commune/code postal ;
- activités, groupes et inscriptions ;
- consommations/réservations ;
- prestations/facturation ;
- règlements et ventilation ;
- liste des règlements/dépôts ;
- export comptable réellement utilisé ;
- génération d'au moins un PDF ;
- sauvegarde/restauration sur la copie si pertinent ;
- fermeture puis réouverture propre.

## Recette des changements intégrés depuis la préparation initiale du sas

### Interface / wxPython

Le parcours détaillé est dans `CI-WINDOWS-AUDIT.md`. Depuis les sources, `DEV-Noethys.cmd` prépare l'environnement Windows et active les journaux utiles.

Tester avec de vrais écrans métier :

- apparence **Système**, **Clair** et **Sombre** ;
- accent historique utilisé dans l'installation ;
- échelle 100 %, puis au moins 120/125 % et 150 % ;
- titres longs sans troncature artificielle ;
- dialogues de préférences/paramétrage ;
- listes/ObjectListView, grilles, barres d'outils et boutons communs ;
- recherche, filtrage, cochage et regroupement lorsqu'ils existent ;
- navigation Notebook/Choicebook/AUI représentative ;
- états vides de listes ;
- absence de fenêtre vide ou partiellement construite ;
- absence d'assertion sizer ;
- ouverture/fermeture répétée de quelques dialogues critiques ;
- comportement normal des panneaux AUI/docking utilisés.

### MySQL distant / performance

Si l'installation utilise MySQL/MariaDB distant :

- ouvrir plusieurs écrans représentatifs ;
- distinguer lenteur réseau, requête longue et freeze réel ;
- récupérer `noethys_perf.log` si un comportement anormal est observé ;
- vérifier qu'aucun watchdog ne confond le démarrage/modal avec un gel ;
- ne pas qualifier une optimisation sans mesure reproductible.

### Commandes de repas

Si le module est utilisé :

- créer une commande avec un modèle existant ;
- vérifier les journées proposées ;
- vérifier un point de livraison regroupant plusieurs couples groupe/unité ;
- vérifier les repas animateurs et le total livraison ;
- confirmer qu'aucune date d'un autre site/point de livraison n'apparaît ;
- vérifier impression/export si utilisés.

### Contrats PSU

Si l'installation utilise les contrats PSU :

- créer/modifier un contrat de test ;
- vérifier prestations et consommations générées ;
- modifier/supprimer une période ;
- confirmer l'absence d'état partiellement enregistré en cas d'échec simulable ou d'annulation ;
- rouvrir le contrat et vérifier la cohérence des données.

### Adresses et communes homonymes

Le contrôle ville/code postal a été durci pour ne plus remplacer silencieusement un couple valide par le premier homonyme trouvé. Pendant la recette d'une fiche famille/individu, vérifier au moins un changement de focus après saisie d'une commune et, si possible, un cas de nom homonyme.

## Compatibilité des données historiques

Après la recette :

- comparer le `schema_digest` au préflight initial ;
- conserver la copie de sauvegarde intacte ;
- vérifier qu'aucune migration inattendue n'a été exécutée ;
- lorsque pertinent, vérifier le retour arrière avec la version historique sur une copie séparée.

## Fonctions optionnelles à tester si réellement utilisées

- MySQL/MariaDB distant ;
- portail/Connecthys ;
- SFTP avec clé hôte ;
- FTPS ;
- FTP historique avec avertissement de connexion non chiffrée ;
- Mailjet et pièces jointes ;
- impression et périphériques ;
- synthèse vocale ;
- extensions Python utilisateur ;
- modules spécifiques de commandes, conventions ou exports réellement utilisés.

## Travaux ouverts hors chemin critique RC

Les chantiers suivants restent suivis, mais ne bloquent pas la première RC tant que leur code n'est pas fusionné dans le SHA candidat et qu'aucun défaut concret du `master` n'est identifié :

- **Noe-005 / #40** — dette SQL progressive ;
- **Noe-060 / 061** — #51, #54, #55, #56, #57, #58, #59 ;
- **Noe-062** — #60 ;
- **Noe-063** — #62.

Les sous-issues portail #65 et #67 sont closes après consolidation dans #62. L'issue #80 « extensions optionnelles » est close comme **non planifiée** tant qu'aucun premier consommateur concret ne justifie de rouvrir ce chantier.

Les anciennes PR de ces chantiers sont des références historiques de conception. Toute reprise doit repartir du `master` courant.

La règle est simple :

> **code présent dans le SHA candidat = à qualifier ; idée/issue/PR fermée non fusionnée = pas un comportement de la RC.**

## Critères de décision

Une RC peut être publiée comme version de test lorsque :

- CI du commit candidat verte ;
- packaging du même code vert ;
- démarrage réel Windows confirmé ;
- copie de base existante ouverte ;
- parcours métier minimal validé ;
- changements déjà fusionnés pertinents pour l'installation testés ;
- aucune migration implicite ou corruption observée ;
- défauts visuels bloquants absents aux échelles/thèmes utilisés ;
- limites connues documentées.

La compatibilité Linux/macOS du code source reste vérifiée automatiquement, mais une distribution utilisateur sur ces plateformes nécessitera sa propre chaîne de qualification.
