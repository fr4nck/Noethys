# Ordre d'implémentation UI

> Ordre consolidé au 24 août 2026.

La modernisation UI suit une règle simple : **corriger d'abord les briques communes, puis les écrans métier**. Les références canoniques sont `DESIGN_SYSTEM_UI_UX.md` et `WXPYTHON_UI_RULES.md`.

## 0. Socle — intégré

- tokens et rôles sémantiques ;
- clair / sombre / système ;
- échelle d'interface ;
- préférences d'apparence/accessibilité ;
- instrumentation performance/freeze ;
- composants communs Repens pour listes, grilles, actions et navigation.

## 1. Nettoyage wxPython transversal — garde-fou permanent

Le nettoyage structurel reste une règle de maintenance, mais **n'est plus un chantier transverse ouvert par défaut**. Il s'applique lorsqu'un défaut concret ou un audit ciblé met en évidence :

- confusion entre parent visuel et contrôleur métier ;
- ordre d'initialisation incorrect ;
- flags sizer invalides ;
- tailles historiques rigides qui cassent le contenu ;
- `SetSize` / `SetPosition` / `CallAfter` utilisés comme rustines de layout ;
- tentative de masquer une assertion wxPython.

Aucun `WXSUPPRESS_SIZER_FLAGS_CHECK` n'est admis. Les dialogues ayant déjà produit fenêtres vides, freezes ou assertions restent prioritaires lorsqu'une régression est observée.

## 2. Composants communs — socle transverse intégré

Les familles suivantes disposent désormais de règles communes Repens et ne doivent plus être redéveloppées écran par écran :

1. `ObjectListView` / `ListCtrl` ;
2. `wx.Grid` ;
3. barres de recherche / filtrage / cochage ;
4. actions et boutons communs ;
5. navigation AUI / Notebook / Choicebook / Listbook / Treebook ;
6. états vides et palette de listes ;
7. surfaces, typographie et métriques sémantiques.

Les champs de saisie, dates, contrôles spécialisés, toolbars ou icônes restant historiques sont traités uniquement lorsqu'ils apparaissent dans un écran réellement utilisé ou dans un défaut reproductible.

## 3. Reflow et scaling — validation par recette

- vrais contenus à 100/120-125/150 % ;
- titres longs non tronqués ;
- conteneurs dimensionnés depuis la police réellement affichée ;
- suppression de l'ancien contrat implicite de bandeaux à hauteur fixe lorsque celui-ci casse un écran ;
- texte secondaire et pied de fenêtre à la même échelle logique ;
- tests de contrat contre le retour des métriques rigides lorsqu'un défaut est corrigé.

La validation réelle se fait en priorité pendant la recette Windows décrite dans `CI-WINDOWS-AUDIT.md`.

## 4. Thème sombre — validation par défaut concret

- éliminer les zones blanches résiduelles observées ;
- préserver les couleurs métier ;
- traiter les contrôles spécialisés avant les règles génériques ;
- conserver la lisibilité lorsqu'un contrôle natif doit rester clair ;
- ne pas casser le comportement natif pour obtenir une uniformité décorative.

## 5. Accueil / dashboard

- retirer les éléments sans valeur métier ;
- structurer les panneaux utiles ;
- conserver les panneaux dockés au premier démarrage ;
- ne pas restaurer aveuglément d'anciennes perspectives AUI ;
- utiliser réellement la largeur disponible ;
- garder météo/Internet/messagerie optionnels et non bloquants.

Voir `DASHBOARD_MODERNISATION.md`.

Les évolutions supplémentaires de l'accueil sont désormais pilotées par recette ou besoin métier, pas par une refonte visuelle générale.

## 6. Recherche individus / familles

- retirer les éléments purement décoratifs lorsqu'ils nuisent à l'usage ;
- rendre les colonnes utiles expansibles ;
- appliquer les composants communs plutôt que recréer un style local ;
- préserver densité et raccourcis de travail.

À partir du socle actuel, les changements suivants doivent répondre à un défaut observé ou à un besoin utilisateur précis.

## 7. Planning semaine / échéancier

- s'appuyer sur les métriques et composants communs ;
- conserver la lisibilité des conflits, absences, sites et activités ;
- ne pas mélanger directement les responsabilités RH de PMSL-Équipe avec les données métier Noethys.

## 8. Modules métier spécifiques

Migrer ou corriger selon usage et retours de recette :

- commandes de repas ;
- statistiques/rapports ;
- conventions/mises à disposition ;
- portail Connecthys ;
- autres dialogues très utilisés.

L'ordre réel est déterminé par fréquence d'usage, défaut observé et valeur métier. Chaque écran doit consommer les composants communs déjà modernisés.

## 9. Messagerie optionnelle

Le module Messagerie reste optionnel et désactivé par défaut. Son UI ne doit être développée que pour un besoin concret et sans connexion/timer lorsqu'il est désactivé.

Voir `MAIL_MODULE_ARCHITECTURE.md`.

## Ligne d'arrivée de la refonte transverse — atteinte sur le code commun

Le lot #78 a consolidé sur `master` les briques transverses Repens :

- `ObjectListView` / `ListCtrl` et `wx.Grid` consomment les règles Repens communes ;
- la barre commune `CTRL_OutilsListeRepens` fournit recherche/filtrage/cochage pour les écrans raccordés ;
- la navigation commune (`AuiNotebook`, `Notebook`, `Choicebook`, `Listbook`, `Treebook`) est raccordée sans reprendre la géométrie native ;
- les états vides ObjectListView sont restaurés sous Phoenix sans flash de construction ;
- les couleurs métier sont préservées par les règles de palette ;
- les audits et tests de contrat protègent ce socle.

Cela signifie qu'il n'existe plus de backlog générique « moderniser Noethys ». Les travaux UI suivants partent d'un **défaut concret observé** (fenêtre vide, freeze, texte tronqué, mauvais contraste, scaling cassé, commande peu utilisable, etc.) ou d'un besoin métier identifié.

La recette Windows reste nécessaire pour confirmer le rendu réel en clair/sombre et aux échelles courantes : un contrat statique ne remplace pas wxWidgets en situation réelle.

## Règle de validation

Un écran n'est pas considéré modernisé uniquement parce qu'il « paraît plus moderne ».

Il doit :

- conserver le comportement métier ;
- rester dense et rapide au clavier/souris ;
- fonctionner en clair et sombre ;
- fonctionner aux échelles courantes ;
- ne pas masquer d'assertion wxPython ;
- réutiliser tokens, métriques, icônes et composants communs ;
- être testé sur Windows lorsqu'un comportement wxWidgets réel est concerné.
