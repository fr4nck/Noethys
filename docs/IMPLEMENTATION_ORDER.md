# Ordre d'implémentation UI

> Ordre consolidé au 22 août 2026.

La modernisation UI suit une règle simple : **corriger d'abord les briques communes, puis les écrans métier**. Les références canoniques sont `DESIGN_SYSTEM_UI_UX.md` et `WXPYTHON_UI_RULES.md`.

## 0. Socle — intégré

- tokens et rôles sémantiques ;
- clair / sombre / système ;
- échelle d'interface ;
- préférences d'apparence/accessibilité ;
- premières règles communes de listes et boutons ;
- instrumentation performance/freeze.

## 1. Nettoyage wxPython transversal — priorité immédiate

- parent visuel distinct du contrôleur métier ;
- ordre d'initialisation des dialogues ;
- suppression des flags sizer invalides ;
- suppression des hauteurs/largeurs historiques rigides lorsque le contenu peut piloter le layout ;
- élimination des `SetSize` / `SetPosition` / `CallAfter` utilisés uniquement comme rustines de layout ;
- aucun `WXSUPPRESS_SIZER_FLAGS_CHECK` ;
- tests ciblés des dialogues ayant déjà produit fenêtres vides, freezes ou assertions.

## 2. Composants communs

Ordre recommandé :

1. `ObjectListView` / `ListCtrl` ;
2. `wx.Grid` ;
3. champs de saisie / choix / dates ;
4. boutons et actions ;
5. toolbars ;
6. navigation / Choicebook / Notebook ;
7. dialogues communs ;
8. états hover/focus/pressed/selected/disabled/error ;
9. icônes Fluent migrées par rôle métier.

## 3. Reflow et scaling

- vrais contenus à 100/120-125/150 % ;
- titres longs non tronqués ;
- conteneurs dimensionnés depuis la police réellement affichée ;
- suppression de l'ancien contrat implicite de bandeaux à hauteur fixe ;
- texte secondaire et pied de fenêtre à la même échelle logique ;
- tests de contrat contre le retour des métriques rigides.

## 4. Thème sombre complet

- éliminer les zones blanches résiduelles ;
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

## 6. Recherche individus / familles

- retirer les éléments purement décoratifs ;
- rendre les colonnes utiles expansibles ;
- appliquer les composants communs plutôt que recréer un style local ;
- préserver densité et raccourcis de travail.

## 7. Planning semaine / échéancier

- s'appuyer sur les métriques et composants communs ;
- conserver la lisibilité des conflits, absences, sites et activités ;
- ne pas mélanger directement les responsabilités RH de PMSL-Équipe avec les données métier Noethys.

## 8. Modules métier spécifiques

Migrer ensuite, selon usage et retours de recette :

- commandes de repas ;
- statistiques/rapports ;
- conventions/mises à disposition ;
- portail Connecthys ;
- autres dialogues très utilisés.

L'ordre réel peut être ajusté par fréquence d'usage ou défaut observé, mais chaque écran doit consommer les composants communs déjà modernisés.

## 9. Messagerie optionnelle

Le module Messagerie reste optionnel et désactivé par défaut. Son UI ne doit être développée qu'après stabilisation des briques communes et sans connexion/timer lorsqu'il est désactivé.

Voir `MAIL_MODULE_ARCHITECTURE.md`.

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
