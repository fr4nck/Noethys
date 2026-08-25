# Journal des décisions de gouvernance

Ce fichier conserve les décisions qui changent le périmètre des branches ou la manière de développer Noethys. Il doit être mis à jour lorsqu'une décision durable est prise afin qu'elle ne reste pas uniquement dans une conversation.

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
