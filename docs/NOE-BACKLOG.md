# Backlog Noe-xxx

> État consolidé au 24 août 2026.

Ce document associe les séries Noe-xxx aux chantiers GitHub. Les **issues GitHub restent la source de suivi opérationnelle** ; ce fichier sert d'index lisible et de vue d'ensemble.

Références complémentaires :

- [`ROADMAP.md`](ROADMAP.md) — trajectoire globale ;
- [`PROJECT_STATE.md`](PROJECT_STATE.md) — décisions transversales ;
- [`UPGRADE-HISTORY.md`](UPGRADE-HISTORY.md) — historique des choix.

## Vue consolidée actuelle

Pour éviter de disperser à nouveau le chantier, le suivi courant se lit désormais en trois niveaux :

### 1. Avant la prochaine RC — un seul chemin critique

Le **cockpit pré-RC est l'issue #19 (Noe-042)**. Elle rassemble les dernières étapes qui exigent encore une action concrète avant publication :

- choisir le SHA candidat sur `master` ;
- relancer les inventaires statiques consolidés sur ce SHA ;
- lancer la qualification complète du même SHA ;
- exécuter le préflight sur une copie de base réellement utilisée ;
- effectuer la recette métier Noe-030 ;
- effectuer la recette visuelle Windows ;
- corriger uniquement les défauts réellement observés ;
- relancer la qualification si le SHA change ;
- déclencher ensuite le workflow Release Candidate et relire la release brouillon.

Les lots techniques historiques **#5 (Noe-002)**, **#6 (Noe-003)**, **#7 (Noe-004)** et **#14 (Noe-030)** sont clos comme lots d'implémentation/outillage. Leurs opérations de qualification sur copie réelle sont désormais suivies dans **#19**. **#40 (Noe-005)** reste une dette SQL progressive et non un blocage générique de RC.

Avant de figer un SHA candidat, lancer :

```bash
python scripts/audit_pre_rc.py
```

Cette commande, ajoutée via PR #81, regroupe les inventaires SQL strict, cycle de vie/parentage wxPython et anciens outils de listes, avec rapports sous `tmp/pre-rc-audits/`. Une occurrence d'audit n'est corrigée que si sa sémantique ou son risque concret est établi.

### 2. Chantiers métier après / à côté de la RC

Ils restent suivis par leurs issues, sans PR de travail ancienne laissée ouverte :

- **Noe-060 / 061 — reporting et pilotage** : #51, #54, #55, #56, #57, #58, #59 ;
- **Noe-062 — conventions et mises à disposition** : #60 ;
- **Noe-063 — portail Connecthys** : suivi consolidé dans #62.

La piste **extensions optionnelles** n'est plus un chantier actif : l'issue #80 est close comme `not planned` tant qu'aucun premier consommateur concret ne justifie de la rouvrir.

Les anciennes PR de ces chantiers ont été fermées sans fusion lorsqu'elles étaient trop éloignées du `master`. Elles restent des références historiques de conception ; toute reprise doit repartir du `master` courant.

### 3. UI/UX transverse

Le socle Repens a été consolidé via PR #78. Il n'existe plus de backlog générique « moderniser toute l'interface ». La suite doit partir d'un **défaut visible en recette** ou d'un **besoin métier concret**. Les audits wxPython et listes servent à localiser les zones à relire, pas à déclencher une réécriture mécanique.

## Noe-000 — SQL / base de données

- **Noe-001 — Audit SQL strict complet** — terminé.
- **Noe-002 — Réécriture OL_Reglements SQL strict** — code terminé ; issue #5 fermée ; validation réelle intégrée au cockpit #19.
- **Noe-003 — Nettoyage DLG_Export_compta** — code terminé ; issue #6 fermée ; validation réelle intégrée au cockpit #19.
- **Noe-004 — Audit index base de données** — outillage terminé ; issue #7 fermée ; mesures sur copie réelle intégrées au cockpit #19.
- **Noe-005 — Reliquat SQL strict détecté par l'audit complet** — dette progressive, issue #40.

Le préflight `scripts/rc_db_preflight.py` regroupe les contrôles Noe-002, Noe-003, Noe-004 et Noe-030 nécessaires à la qualification réelle suivie dans #19.

## Noe-010 — Runtime Python

- **Noe-010 — Audit compatibilité Python 3.10+** — terminé.
- **Noe-011 — Préparation Python 3.11** — terminé.
- **Noe-012 — Étude Python 3.12** — terminé.

La baseline de production reste Python 3.10 tant qu'une décision explicite de migration n'est pas prise.

## Noe-020 — wxPython / plateformes

- **Noe-020 — Audit wxPython Phoenix complet** — terminé pour le socle de compatibilité.
- **Noe-021 — Compatibilité GTK3/Linux** — terminé pour le code source.
- **Noe-022 — Validation macOS** — terminé pour le code source.

Les travaux UI plus récents ne rouvrent pas ces tickets historiques : les règles de nettoyage et de layout sont désormais documentées dans `WXPYTHON_UI_RULES.md` et doivent être appliquées à chaque correction d'écran.

## Noe-030 — Tests et exploitation

- **Noe-030 — Scénario de recette base existante** — outillage et procédure terminés ; issue #14 fermée ; exécution réelle du prochain SHA suivie dans #19.
- **Noe-031 — Tests non-régression métier** — terminé.
- **Noe-032 — Audit sauvegarde/restauration** — terminé.

La recette finale doit être exécutée sur le SHA réellement candidat à la RC, car le fork a continué à évoluer après la première préparation du sas.

## Noe-040 — Distribution

- **Noe-040 — Packaging Windows final** — terminé.
- **Noe-041 — Version portable Noethys** — terminé.
- **Noe-042 — Préparation RC** — sas technique terminé ; recette réelle puis déclenchement RC restants. Issue #19, cockpit pré-RC.

## Noe-050 — Documentation et mémoire du chantier

- **Noe-050 — Documentation développeur** — socle terminé ; entretien continu.
- **Noe-051 — Documentation utilisateur** — socle terminé ; entretien continu.
- **Noe-052 — Historique Upgrade Noethys** — consolidation terminée. Issue #22, conservée comme index historique.

La mémoire transversale est notamment portée par :

- `PROJECT_STATE.md` ;
- `DESIGN_SYSTEM_UI_UX.md` ;
- `WXPYTHON_UI_RULES.md` ;
- `CI-WINDOWS-AUDIT.md` ;
- `ARCHITECTURE-TIERS-PRESTATIONS-PLANNING.md` ;
- `COMMANDES_REPAS_POINTS_LIVRAISON.md`.

## UI/UX transversal — socle consolidé

Ce chantier n'est pas renuméroté artificiellement dans la série Noe tant que les issues existantes ne le font pas.

Éléments intégrés :

- échelle générale et apparence Système / Clair / Sombre ;
- design system et tokens sémantiques ;
- instrumentation performance/freeze ;
- direction Fluent 2 + Material 3 ;
- règles de parentage/sizers wxPython ;
- `ObjectListView` / `ListCtrl` et `wx.Grid` raccordés aux règles Repens ;
- outils communs de recherche / filtrage / cochage ;
- navigation commune AUI / Notebook / Choicebook / Listbook / Treebook ;
- états vides ObjectListView sous Phoenix ;
- tests de contrat UI associés.

La consolidation transverse a été fusionnée via PR #78. Les anciennes PR empilées #73/#74/#75 ont été fermées sans fusion après reconstruction propre sur `master`.

La suite UI n'est plus un backlog générique de restylage : elle part d'un défaut concret observé en recette Windows ou d'un besoin métier explicite.

## Commandes de repas — lot intégré

La modernisation du module historique par points de livraison a été intégrée via PR #46 :

- regroupement de groupes/unités par point de livraison ;
- dates issues également des consommations réelles ;
- repas animateurs ;
- totaux livraison ;
- compatibilité des anciens modèles.

La règle de filtrage des dates par couples `IDgroupe` / `IDunite` configurés est conservée dans `COMMANDES_REPAS_POINTS_LIVRAISON.md`.

## Noe-060 — Rapports métier fiables et prédéfinis

**Issue #51 — ouverte.**

Objectif : remplacer les combinaisons manuelles fragiles de statistiques par des rapports métier dont les règles sont portées par le code.

Découpage :

- **Noe-060A — Référentiel des indicateurs et moteur de calcul partagé** — issue #54, ouverte ;
- **Noe-060B — Communes partenaires ALSH : pilotage, convention et états** — issue #55, ouverte ;
- **Noe-060C — Communes homonymes et codes postaux** — issue #53, **terminée et fermée** ;
- **Noe-060D — Exports et rapports issus du même jeu de données** — issue #56, ouverte ;
- **Noe-060E — Résidence datée et règles territoriales historisées** — issue #57, ouverte ;
- **Noe-060F — Annulations, absences et historique compact** — issue #58, ouverte.

Ordre recommandé désormais :

1. définir les indicateurs canoniques ;
2. fiabiliser résidence et règles territoriales datées ;
3. construire la vue communes partenaires ;
4. ajouter l'historique compact annulations/absences ;
5. brancher exports et PDF sur le même résultat.

L'ancienne PR de chantier #52 a été fermée : elle ne contenait qu'un cadrage documentaire et était trop en retard sur `master`. Le travail restant est porté par les issues et doit repartir du `master` courant.

## Noe-061 — Pilotage annuel et rapports d'activité

**Issue #59 — ouverte.**

Objectif : générer automatiquement les chiffres, tableaux, graphiques et comparatifs récurrents à partir des données Noethys.

Périmètre initial :

- ALSH ;
- École multisport ;
- Sport-Santé ;
- EPS / partenaires / mises à disposition ;
- indicateurs transversaux d'activité.

Dépend principalement de Noe-060A et Noe-060D. Les rapports PMSL existants servent de cahier des charges empirique ; les parties qualitatives restent rédigées manuellement.

## Noe-062 — Conventions et mises à disposition

**Issue #60 — ouverte.**

Objectif : ajouter les structures et relations contractuelles sans créer un second moteur parallèle de planning, facturation ou documents.

Lots conçus dans l'ancienne branche de travail :

- socle convention / avenant ;
- structures et contacts ;
- relation contractuelle ;
- programmation annuelle et renouvellement N-1 ;
- annexe prévisionnelle date par date ;
- snapshot documentaire ;
- raccord futur au réalisé, à la facturation et au reporting ;
- échange avec PMSL-Équipe par identifiants stables.

Règles :

- bénéficiaire et payeur peuvent être distincts ;
- adhésion et mode de facturation appartiennent à la relation contractuelle ;
- réutiliser le calcul de récurrence historique ;
- aucune migration destructive ;
- le stockage persistant ne doit être introduit qu'après cartographie et validation sur copie réelle.

La PR #61 a été fermée sans fusion car sa branche était devenue trop en retard sur `master`. Elle reste une référence de conception ; les futurs lots devront être reconstruits proprement sur le `master` courant.

Référence : `ARCHITECTURE-TIERS-PRESTATIONS-PLANNING.md`.

## Noe-063 — Portail Connecthys : contenus dynamiques et source unique

**Issue #62 — ouverte et désormais unique issue de suivi du portail.**

Objectif : publier dans Connecthys des contenus et données maintenus dans Noethys ou des sources externes, sans double saisie et sans modification obligatoire du serveur hébergé pour les premiers lots.

Sous-chantiers conservés dans #62 :

- **Contenus externes** — concept conservé ; ancienne PR #63 fermée sans fusion ;
- **RSS / Atom natif** — ancien suivi #65 consolidé dans #62 ; ancienne PR #66 fermée ;
- **Barèmes Noethys / Mes tarifs** — ancien suivi #67 consolidé dans #62 ; anciennes PR #68/#69 fermées ;
- **convergence portail** — ancienne PR #72 fermée après inspection : elle reste une référence de diff mais doit être reconstruite depuis le `master` courant avant toute reprise.

Règles :

- les catégories persistantes historiques restent utilisées lorsqu'elles assurent la compatibilité Connecthys ;
- les barèmes viennent du moteur tarifaire Noethys ;
- pas de faux prix personnalisé si le contexte réel manque ;
- une panne de source externe ne bloque pas la synchronisation générale ;
- pas d'identifiant famille exposé en clair comme pseudo-personnalisation ;
- aucune migration destructive.

## Extensions optionnelles — piste dormante

L'ancienne PR #64 a exploré un registre minimal d'extensions, sans chargement automatique et sans modification du comportement historique. Elle reste une référence de conception, pas du code livré.

L'issue #80 est désormais **close comme `not planned`**. Le sujet ne doit être rouvert que lorsqu'un premier usage concret le justifie ; toute reprise repartira alors du `master` courant.

Usages envisagés si le besoin réapparaît : fournisseurs de communication, exports/reporting et connecteurs externes.

## CI — boucle rapide et qualification lourde

La consolidation CI a été fusionnée via PR #70.

État courant :

- `.github/workflows/ci.yml` est la porte d'entrée unique ;
- PR / push `master` : validation rapide Ubuntu unique ;
- `workflow_dispatch` mode `complete` : recette synthétique, smokes Windows/macOS/Linux et packaging ;
- `windows-package.yml` est réutilisable ;
- l'ancien workflow UI séparé a été supprimé ;
- les diagnostics indépendants sont collectés avant le verdict final lorsque possible ;
- `scripts/audit_pre_rc.py`, fusionné via #81, fournit l'inventaire consolidé à relire avant le gel d'un SHA candidat.

Le comportement réel des workflows présents sur `master` reste la référence exécutable.

## Situation pré-RC

Le verrou pré-RC reste unique : **validation du SHA candidat sur une copie de base réellement utilisée puis recette métier/visuelle Windows**, suivie dans #19.

Noe-005, Noe-060, Noe-061, Noe-062 et Noe-063 sont des chantiers parallèles ou post-socle ; ils ne doivent pas être confondus avec le minimum technique historiquement requis pour fabriquer la première RC. La piste extensions/#80 est dormante et n'appartient plus au backlog actif. En revanche, tout code déjà fusionné dans `master` au moment du gel RC fait naturellement partie du SHA à qualifier.

## Règle de suivi

- issue GitHub = travail restant / critères d'acceptation ;
- PR = implémentation proposée ou en cours ;
- PR fermée non fusionnée = référence historique, pas comportement livré ;
- code + tests = comportement effectivement intégré ;
- `PROJECT_STATE.md` = décisions transversales ;
- ce backlog = index, pas seconde source concurrente.
