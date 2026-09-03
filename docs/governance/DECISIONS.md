# Journal des décisions de gouvernance

Ce fichier conserve les décisions qui changent le périmètre des branches ou la manière de développer Noethys. Il doit être mis à jour lorsqu'une décision durable est prise afin qu'elle ne reste pas uniquement dans une conversation.

## 3 septembre 2026 — branche Qt expérimentale strictement isolée

### Décision

Créer une ligne expérimentale `poc/qt-theme-isole`, dérivée d'Upgrade, afin d'évaluer le remplacement progressif de la couche graphique wxPython par Qt/PySide6.

Le principe n'est pas de réécrire Noethys : la base, les règles métier, les traitements, les exports et les comportements fonctionnels historiques restent les invariants à préserver. Les tableaux actuels constituent un contrat de densité et de fonctionnalités, même si leur rendu est remplacé.

Le premier écran témoin est la gestion des activités (`Ol/OL_Activites.py`). Le prototype n°1 reste en lecture seule côté base et doit prouver le raccordement des vraies données à un `QTableView` avant toute migration des dialogues d'édition.

### Motif

La transition graphique de Teamworks a montré qu'une architecture graphique trop ambitieuse, un moteur de thème maison et des couches d'adaptation généralisées peuvent masquer très tôt la valeur réelle d'une migration. Noethys Qt doit donc être jugé sur un écran concret avant tout investissement transversal.

### Conséquences

- aucune modification de `maintenance/vanilla` ;
- aucune fusion automatique de la branche Qt vers `master` ;
- pas de moteur de thème maison comme préalable ;
- pas de dimensionnement fixe des boutons et formulaires comme méthode de layout ;
- conservation des colonnes, tris, sélections, menus et densité des tableaux historiques ;
- extraction métier/UI uniquement lorsqu'elle est nécessaire à un écran réel ;
- seuil d'arrêt : 2 jours sans tableau réel fonctionnel, 4 jours sans prototype complet ;
- toute décision de généraliser Qt à Upgrade devra faire l'objet d'une décision distincte après recette du prototype.

### Périmètre du prototype n°1

Opérationnel : chargement réel des activités, tri, sélection, redimensionnement, filtre des activités ouvertes, actualisation, export Texte et export Excel.

Hors périmètre provisoire : Ajouter, Modifier, Supprimer, Dupliquer, Importer, export complet d'une activité, aperçu avant impression et impression.

## 25 août 2026 — séparation stricte Vanilla / Upgrade

### Décision

Le terme **Vanilla** désigne désormais exclusivement la version historique issue du projet original Noethys, maintenue sans migration Python 3, sans wxPython Phoenix, sans nouvel UX et sans nouvelle fonction métier.

Une branche permanente est créée :

`maintenance/vanilla`

Point de départ :

`630ef4373dbc05dae1cbc597b9baccb1178e64e4`

Le `master` actuel conserve le chantier de modernisation et doit être désigné comme **Upgrade**.

### Motif

L'exploitation quotidienne ne doit pas dépendre de l'achèvement du portage Python 3, de Phoenix ou de la refonte UI. La version historique fonctionne déjà en production ; l'objectif immédiat est donc de la maintenir et d'y apporter des correctifs ciblés sans modifier son identité technique ou graphique.

### Conséquences

- les correctifs de bugs historiques doivent pouvoir être backportés vers `maintenance/vanilla` ;
- les changements Python 3 / Phoenix / UI restent dans Upgrade ;
- aucune fusion globale de `master` vers Vanilla ;
- compatibilité avec les bases existantes et le Connecthys actuellement exploité considérée comme contrainte prioritaire de Vanilla ;
- les travaux Vanilla doivent être testables indépendamment de l'avancement d'Upgrade ;
- les termes « Vanilla+ » ou « Vanilla modernisée » ne doivent plus être utilisés pour désigner `master`, car ils créent une ambiguïté de produit.

### Priorité

Le prochain jalon opérationnel est une première Vanilla maintenue et testable dans l'environnement d'exploitation actuel, avant toute dépendance à la finalisation du chantier Upgrade.

## Modèle pour les prochaines décisions

Ajouter une entrée avec :

- date ;
- décision ;
- motif ;
- branches ou composants concernés ;
- compatibilité / migration éventuelle ;
- conséquence sur la roadmap et les issues.
