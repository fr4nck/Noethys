# Backlog Noe-xxx

> État consolidé au 22 août 2026.

Ce document associe les séries Noe-xxx aux chantiers GitHub. Les **issues GitHub restent la source de suivi opérationnelle** ; ce fichier sert d'index lisible et de vue d'ensemble.

Références complémentaires :

- [`ROADMAP.md`](ROADMAP.md) — trajectoire globale ;
- [`PROJECT_STATE.md`](PROJECT_STATE.md) — décisions transversales ;
- [`UPGRADE-HISTORY.md`](UPGRADE-HISTORY.md) — historique des choix.

## Noe-000 — SQL / base de données

- **Noe-001 — Audit SQL strict complet** — terminé.
- **Noe-002 — Réécriture OL_Reglements SQL strict** — code terminé ; validation sur copie réelle incluse dans Noe-030 restante.
- **Noe-003 — Nettoyage DLG_Export_compta** — code terminé ; validation sur copie réelle incluse dans Noe-030 restante.
- **Noe-004 — Audit index base de données** — outillage terminé ; mesures sur copie réelle restantes. Issue #7.
- **Noe-005 — Reliquat SQL strict détecté par l'audit complet** — dette progressive, issue #40.

Le préflight `scripts/rc_db_preflight.py` regroupe les contrôles encore nécessaires pour Noe-002, Noe-003, Noe-004 et Noe-030.

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

- **Noe-030 — Scénario de recette base existante** — outillage terminé ; recette sur copie réelle restante. Issue #14.
- **Noe-031 — Tests non-régression métier** — terminé.
- **Noe-032 — Audit sauvegarde/restauration** — terminé.

La recette finale doit être exécutée sur le SHA réellement candidat à la RC, car le fork a continué à évoluer après la première préparation du sas.

## Noe-040 — Distribution

- **Noe-040 — Packaging Windows final** — terminé.
- **Noe-041 — Version portable Noethys** — terminé.
- **Noe-042 — Préparation RC** — sas technique terminé ; recette réelle puis déclenchement RC restants. Issue #19.

## Noe-050 — Documentation et mémoire du chantier

- **Noe-050 — Documentation développeur** — socle terminé ; entretien continu.
- **Noe-051 — Documentation utilisateur** — socle terminé ; entretien continu.
- **Noe-052 — Historique Upgrade Noethys** — consolidation terminée. Issue #22, conservée comme index historique.

Depuis le 22 août, la mémoire transversale est également portée par :

- `PROJECT_STATE.md` ;
- `DESIGN_SYSTEM_UI_UX.md` ;
- `WXPYTHON_UI_RULES.md` ;
- `ARCHITECTURE-TIERS-PRESTATIONS-PLANNING.md` ;
- `COMMANDES_REPAS_POINTS_LIVRAISON.md`.

## UI/UX transversal — socle intégré

Ce chantier n'est pas renuméroté artificiellement dans la série Noe tant que les issues existantes ne le font pas.

Éléments déjà intégrés :

- échelle générale et apparence Système / Clair / Sombre ;
- design system et tokens sémantiques ;
- règles de composants communs ;
- diagnostic performance/freeze ;
- direction Fluent 2 + Material 3 ;
- règles de parentage/sizers wxPython.

Références principales : PR #47, PR #49, PR #50 et documentation canonique UI/UX.

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
- **Noe-060C — Communes homonymes et codes postaux** — issue #53, ouverte ;
- **Noe-060D — Exports et rapports issus du même jeu de données** — issue #56, ouverte ;
- **Noe-060E — Résidence datée et règles territoriales historisées** — issue #57, ouverte ;
- **Noe-060F — Annulations, absences et historique compact** — issue #58, ouverte.

Ordre recommandé :

1. sécuriser l'identité des communes ;
2. définir les indicateurs canoniques ;
3. fiabiliser résidence et règles territoriales datées ;
4. construire la vue communes partenaires ;
5. ajouter l'historique compact annulations/absences ;
6. brancher exports et PDF sur le même résultat.

Une PR de chantier existe sous #52 ; elle reste une branche de construction et ne remplace pas les issues comme source de suivi.

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

**Issue #60 — ouverte. PR de construction #61 en draft.**

Objectif : ajouter les structures et relations contractuelles sans créer un second moteur parallèle de planning, facturation ou documents.

Lots actuellement décrits/construits :

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

Référence : `ARCHITECTURE-TIERS-PRESTATIONS-PLANNING.md`.

## Noe-063 — Portail Connecthys : contenus dynamiques et source unique

**Issue #62 — ouverte.**

Objectif : publier dans Connecthys des contenus et données maintenus dans Noethys ou des sources externes, sans double saisie et sans modification obligatoire du serveur hébergé pour les premiers lots.

Sous-chantiers :

- **Noe-063 — Contenus externes** — socle développé dans PR #63 ;
- **Noe-063B — RSS / Atom natif** — issue #65, ouverte ; PR #66 en draft ;
- **Noe-063C — Barèmes Noethys / Mes tarifs** — issue #67, ouverte ; PR #68 et prolongements #69 ;
- **convergence du chantier portail** — PR #72 vise une reconstruction propre depuis le `master` courant afin de ne pas fusionner aveuglément les anciennes branches empilées.

Règles :

- les catégories persistantes historiques restent utilisées lorsqu'elles assurent la compatibilité Connecthys ;
- les barèmes viennent du moteur tarifaire Noethys ;
- pas de faux prix personnalisé si le contexte réel manque ;
- une panne de source externe ne bloque pas la synchronisation générale ;
- pas d'identifiant famille exposé en clair comme pseudo-personnalisation ;
- aucune migration destructive.

## Extensions optionnelles — expérimentation transversale

La PR #64 introduit un registre minimal d'extensions, sans chargement automatique et sans modification du comportement historique.

Ce travail reste **transversal et expérimental** tant qu'aucune issue Noe dédiée ne fixe son périmètre définitif. Ne pas lui attribuer artificiellement un numéro Noe.

Usages envisagés : fournisseurs de communication, exports/reporting et connecteurs externes.

## CI — boucle rapide vs qualification lourde

La PR #70 propose de séparer la boucle rapide quotidienne de la qualification RC lourde. Tant qu'elle n'est pas fusionnée, le comportement réel des workflows du `master` reste la référence.

Principe retenu pour la trajectoire : réduire le temps de retour quotidien sans retirer les contrôles lourds nécessaires avant diffusion.

## Situation pré-RC

Le verrou pré-RC reste unique : **validation du SHA candidat sur une copie de base réellement utilisée puis recette métier/visuelle Windows**.

Noe-005, Noe-060, Noe-061, Noe-062 et Noe-063 sont des chantiers parallèles ou post-socle ; ils ne doivent pas être confondus avec le minimum technique historiquement requis pour fabriquer la première RC. En revanche, tout code déjà fusionné dans `master` au moment du gel RC fait naturellement partie du SHA à qualifier.

## Règle de suivi

- issue GitHub = travail restant / critères d'acceptation ;
- PR = implémentation proposée ou en cours ;
- code + tests = comportement effectivement intégré ;
- `PROJECT_STATE.md` = décisions transversales ;
- ce backlog = index, pas seconde source concurrente.
