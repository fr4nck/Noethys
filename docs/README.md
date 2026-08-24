# Documentation du fork Upgrade Noethys

> Index documentaire consolidé au 24 août 2026.

Ce dossier contient à la fois des **documents canoniques actuels** et des **documents historiques d'audit ou de décision**. L'objectif de cet index est d'éviter qu'un ancien document soit pris par erreur pour l'état courant du projet.

## Ordre de lecture recommandé

1. [`PROJECT_STATE.md`](PROJECT_STATE.md) — état transversal, frontières du projet et décisions durables ;
2. [`ROADMAP.md`](ROADMAP.md) — trajectoire actuelle ;
3. [`NOE-BACKLOG.md`](NOE-BACKLOG.md) — index des chantiers, issues et travaux restants ;
4. [`DEVELOPMENT.md`](DEVELOPMENT.md) — environnement de développement et règles techniques ;
5. document métier ou technique spécialisé correspondant au chantier concerné.

## Documents canoniques actuels

### Pilotage

- [`PROJECT_STATE.md`](PROJECT_STATE.md) — **canonique** : décisions transversales, sources de vérité, frontières Noethys / PMSL-Équipe / Teamworks / Connecthys.
- [`ROADMAP.md`](ROADMAP.md) — **canonique** : phases et trajectoire générale.
- [`NOE-BACKLOG.md`](NOE-BACKLOG.md) — **canonique** : correspondance Noe-xxx / issues / état opérationnel.
- [`UPGRADE-HISTORY.md`](UPGRADE-HISTORY.md) — **historique consolidé maintenu** : décisions structurantes déjà prises.

### Développement, distribution et recette

- [`DEVELOPMENT.md`](DEVELOPMENT.md) — **canonique** : runtime, tests, CI, bases, wxPython et packaging.
- [`CI-WINDOWS-AUDIT.md`](CI-WINDOWS-AUDIT.md) — **canonique pour la qualification runtime/UI et la recette Windows** : CI consolidée, audits wxPython et parcours manuel post-Repens.
- [`USER-GUIDE-UPGRADE.md`](USER-GUIDE-UPGRADE.md) — **canonique** : test/utilisation du fork et retour arrière.
- [`RC-CHECKLIST.md`](RC-CHECKLIST.md) — **canonique pour le prochain gel RC**.
- [`NOE-042-RC-READINESS.md`](NOE-042-RC-READINESS.md) — **état du sas RC** ; à lire avec `RC-CHECKLIST.md`.
- [`NOE-030-RECETTE-BASE-EXISTANTE.md`](NOE-030-RECETTE-BASE-EXISTANTE.md) — procédure de recette sur copie réelle.
- [`PACKAGING-WINDOWS11.md`](PACKAGING-WINDOWS11.md) — chaîne de fabrication Windows.

### UI/UX et wxPython

- [`DESIGN_SYSTEM_UI_UX.md`](DESIGN_SYSTEM_UI_UX.md) — **référence UI/UX canonique** : Fluent 2 + Material Design 3 + profondeur ciblée.
- [`WXPYTHON_UI_RULES.md`](WXPYTHON_UI_RULES.md) — **référence d'implémentation canonique** : parentage, sizers, scaling, dark mode, debugging.
- [`IMPLEMENTATION_ORDER.md`](IMPLEMENTATION_ORDER.md) — état de la modernisation UI et règle de poursuite après consolidation transverse.
- [`DASHBOARD_MODERNISATION.md`](DASHBOARD_MODERNISATION.md) — cible du dashboard.

### Métier et architecture

- [`COMMANDES_REPAS_POINTS_LIVRAISON.md`](COMMANDES_REPAS_POINTS_LIVRAISON.md) — commandes de repas et points de livraison.
- [`ARCHITECTURE-TIERS-PRESTATIONS-PLANNING.md`](ARCHITECTURE-TIERS-PRESTATIONS-PLANNING.md) — tiers, conventions, mises à disposition, EPS, planning, facturation, PMSL-Équipe.
- [`MAIL_MODULE_ARCHITECTURE.md`](MAIL_MODULE_ARCHITECTURE.md) — cible du module Messagerie optionnel.

## Documents historiques ou d'audit

Ces fichiers restent utiles comme **preuve de décision**, inventaire ou historique technique, mais ils ne doivent pas remplacer les documents canoniques ci-dessus.

- [`INTERFACE_MATERIAL3.md`](INTERFACE_MATERIAL3.md) — première direction Material 3, désormais explicitement historique ; la référence actuelle est `DESIGN_SYSTEM_UI_UX.md`.
- [`NOE-001-AUDIT-REPORT.md`](NOE-001-AUDIT-REPORT.md) — rapport d'audit runtime initial.
- [`NOE-001-SQL-AUDIT.md`](NOE-001-SQL-AUDIT.md) — inventaire SQL initial.
- [`NOE-002-OL_REGLEMENTS_PLAN.md`](NOE-002-OL_REGLEMENTS_PLAN.md) — plan de réécriture historique OL_Reglements.
- [`NOE-003-COTISATION-PRESTATION.md`](NOE-003-COTISATION-PRESTATION.md) — décision historique sur l'invariant cotisation/prestation.
- [`NOE-004-INDEX-AUDIT.md`](NOE-004-INDEX-AUDIT.md) — stratégie d'audit des index et mesures.

Les autres documents `NOE-xxx-*` conservent de la même manière le détail d'un lot ou d'une qualification. Leur date et leur périmètre doivent être lus avant d'en déduire l'état courant.

## Source de vérité

En cas de contradiction :

1. **code et tests** pour le comportement réellement intégré ;
2. **issues GitHub** pour le travail restant et les critères d'acceptation ;
3. **documents canoniques** listés ci-dessus pour l'architecture et les décisions ;
4. documents historiques pour comprendre pourquoi une décision a été prise.

Une PR ouverte n'est pas un comportement intégré tant qu'elle n'est pas fusionnée. Une PR fermée non fusionnée reste uniquement une référence historique de conception ou de diff.

## État courant des branches de travail

Les anciennes PR de consolidation UI et les anciennes branches empilées des chantiers Noe-060/062/063 ont été fermées lorsqu'elles étaient devenues trop en retard sur `master`. Les besoins non terminés restent portés par leurs issues ; toute reprise doit reconstruire un lot ciblé depuis le `master` courant plutôt que ressusciter une branche obsolète.

## Règle d'entretien

Lorsqu'une conversation ou une recette produit une décision durable :

- corriger le code et ajouter un test si la décision est exécutable ;
- ouvrir/mettre à jour une issue si du travail reste ;
- mettre à jour le document canonique correspondant si la règle est transversale ;
- ne pas créer un nouveau document concurrent lorsqu'un document existant peut porter proprement l'information.

Cette règle permet de supprimer les anciens échanges de travail sans perdre la mémoire du projet.
