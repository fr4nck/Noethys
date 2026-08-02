# Backlog issu du projet Noethys original

## Objectif

Transformer les signalements du forum et du dépôt d’origine en backlog technique priorisé pour la modernisation Windows 11, sans modifier le schéma de base.

## Sources suivies

- Dépôt original : https://github.com/Noethys/Noethys
- Forum officiel : https://www.noethys.com/index.php/forum-34

## P0 — Démarrage et récupération

### Configuration locale corrompue

Signalement récurrent : `error: db type could not be determined` lors de l’ouverture du fichier de configuration `shelve/anydbm`.

Le contournement historique impose de maintenir CTRL ou ALT au démarrage afin de réinitialiser les préférences.

Travaux attendus :

- détecter automatiquement la corruption ;
- sauvegarder ou renommer le fichier fautif ;
- proposer une récupération explicite ;
- journaliser l’incident ;
- ne jamais toucher au fichier de données métier.

Références :

- https://www.noethys.com/index.php/forum-34/6-signaler-un-bug/6278-impossible-de-lancer-noethys
- https://www.noethys.com/index.php/forum-34/6-signaler-un-bug/5438-impossible-d-ouvrir-noethys-gros-bug
- https://www.noethys.com/index.php/forum-34/6-signaler-un-bug/5517-noethys-ne-s-ouvre-plus

## P0 — Compatibilité wxPython moderne

Des assertions ont été signalées sur les grilles et les indices de colonnes avec wxPython Phoenix. Le mainteneur indiquait que d’autres incompatibilités pouvaient subsister.

Travaux attendus :

- tests ciblés des grilles ;
- tests des listes et contrôles personnalisés ;
- ouverture/destruction de dialogues prioritaires ;
- qualification avec la version wxPython retenue pour Windows 11.

Référence :

- https://www.noethys.com/index.php/forum-34/6-signaler-un-bug/5371-importation-d-un-fichier-csv

## P1 — Facturation et impressions

Signalements :

- facture impossible à produire ou télécharger lorsque le logo ou le modèle est absent ;
- fichiers PDF temporaires potentiellement supprimés par la fermeture d’une autre instance ;
- édition ou envoi restant bloqué sans diagnostic clair.

Travaux attendus :

- garde explicite sur les ressources absentes ;
- répertoires temporaires isolés par processus ;
- test d’édition et d’envoi avec et sans logo ;
- diagnostic utilisateur exploitable.

Références :

- https://www.noethys.com/index.php/forum-34/noethysweb/6328-impression-des-factures-impossible
- https://www.noethys.com/index.php/forum-34/6-signaler-un-bug/5959-message-d-erreur-a-l-impression-et-a-l-envoi-des-factures

## P1 — Windows 11, réseau et MySQL

Les utilisateurs demandent explicitement une validation Windows 11, notamment en bureau à distance et avec une base MySQL.

Travaux attendus :

- recette Windows 11 locale ;
- recette TSE/RDP ;
- recette SQLite ;
- recette MySQL ;
- documentation des versions serveur supportées ;
- procédure de sauvegarde et restauration.

Référence :

- https://www.noethys.com/index.php/forum-34/installation/6262-passage-a-windows-11

## P2 — Installation et dépendances

Les procédures historiques et certaines dépendances deviennent obsolètes.

Travaux attendus :

- dépendances épinglées et testées ;
- version Python documentée ;
- version wxPython documentée ;
- packaging reproductible ;
- suppression progressive des dépendances non nécessaires.

Référence :

- https://www.noethys.com/index.php/forum-34/installation/5376-refaire-un-script-a-jour-pour-l-installation-de-noethys-sur-ubuntu-20-04

## Règles de traitement

- Une correction fonctionnelle ou runtime par PR ciblée.
- Aucun changement implicite du schéma de base.
- Toujours tester sur une copie de base réelle.
- Conserver la compatibilité avec l’ancienne version tant qu’aucune migration dédiée n’est décidée.
- Distinguer défaut confirmé, problème de paramétrage et faux positif.

## Ordre recommandé

1. Finaliser le ZIP Windows 11 portable.
2. Ajouter un test de récupération du fichier de configuration corrompu.
3. Ajouter les tests wxPython prioritaires.
4. Tester factures, impressions et fichiers temporaires.
5. Qualifier SQLite et MySQL sous Windows 11 et RDP.
6. Continuer l’inventaire du forum par lots.
