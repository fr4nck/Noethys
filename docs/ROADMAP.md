# Roadmap de modernisation de Noethys

> État consolidé au 22 août 2026.

Cette feuille de route décrit la trajectoire du fork `fr4nck/Noethys`. Elle complète :

- [`PROJECT_STATE.md`](PROJECT_STATE.md) — décisions transversales et sources de vérité ;
- [`NOE-BACKLOG.md`](NOE-BACKLOG.md) — correspondance entre séries Noe-xxx, issues et état opérationnel ;
- [`UPGRADE-HISTORY.md`](UPGRADE-HISTORY.md) — historique des choix déjà arrêtés.

L'objectif n'est pas de réécrire Noethys ni d'imposer une migration de données. Le projet prolonge Noethys Desktop en conservant son métier, ses bases existantes et sa compatibilité historique autant que possible, tout en modernisant progressivement runtime, interface, reporting et intégrations.

## Principes directeurs

- préserver les bases et configurations existantes ;
- ne jamais introduire de migration implicite de schéma ;
- conserver SQLite et la compatibilité MySQL/MariaDB historique autant que raisonnablement possible ;
- préférer des corrections ciblées aux refactorisations massives ;
- corriger les causes confirmées plutôt que masquer les symptômes ;
- maintenir Windows, Linux et macOS comme cibles du code source ;
- garder Windows comme cible de distribution prioritaire ;
- tester les changements touchant les données sur une copie de base réelle ;
- faire d'une donnée métier une source de vérité réutilisable par écran, export, PDF, rapport et portail ;
- moderniser les composants communs avant les écrans particuliers ;
- conserver les frontières entre Noethys, PMSL-Équipe, Teamworks-CCNS, Connecthys et les autres outils associés.

---

## Phase 1 — Stabilisation technique et préparation RC

### État

La modernisation technique nécessaire à une première Release Candidate conservatrice est terminée côté automatisation :

- SQL critique règlements / exports comptables sécurisé et couvert par des tests ;
- Python 3.10 baseline qualifiée ; Python 3.11 validé ; Python 3.12 étudié ;
- wxPython Phoenix qualifié ;
- smoke tests Windows, macOS et Linux/GTK3 ;
- tests de non-régression métier exécutés globalement ;
- sauvegarde/restauration auditée et réparée ;
- portable Windows PyInstaller construit, extrait et réellement exécuté en CI ;
- mode `Portable/` isolant configuration et données qualifié ;
- préflight Noe-002/003/004/030 regroupé en une seule commande ;
- sas RC manuel protégé : aucune RC ne peut être fabriquée sans confirmation explicite de la recette réelle et la release reste en brouillon.

### Verrou restant avant une RC validée

Il ne reste pas de chantier technique caché obligatoire. La validation reste volontairement bloquée par l'exploitation réelle :

1. exécuter `scripts/rc_db_preflight.py` sur une **copie** d'une base Noethys réellement utilisée ;
2. effectuer le parcours métier de `NOE-030-RECETTE-BASE-EXISTANTE.md` ;
3. valider visuellement l'interface Windows sur cette copie ;
4. corriger uniquement les anomalies réellement observées ;
5. déclencher le workflow `Release Candidate` depuis `master` ;
6. relire la release GitHub créée en brouillon avant publication.

Depuis la préparation initiale de la RC, plusieurs correctifs et fonctions ont été intégrés au fork. La recette finale doit donc porter sur **le SHA candidat réellement publié**, pas sur un ancien artefact déjà qualifié.

---

## Phase 2 — Dette SQL et performances mesurées

### Noe-005 — SQL strict progressif

L'audit complet conserve un reliquat de requêtes classées `REVIEW`. Ce reliquat représente une dette d'analyse, pas autant de bugs connus.

Règles :

- traiter d'abord les requêtes financières ou réellement rencontrées en recette ;
- ne jamais ajouter mécaniquement toutes les colonnes au `GROUP BY` ;
- ne jamais choisir `MIN()`/`MAX()` sans invariant métier démontré ;
- privilégier pré-agrégations et sous-requêtes lorsqu'elles préservent clairement la cardinalité historique ;
- ajouter un test lorsque la réécriture concerne une famille de requêtes importante.

### Index et MySQL distant

L'optimisation reste pilotée par les mesures :

- audit en lecture seule ;
- `EXPLAIN` ;
- chronométrages reproductibles ;
- aucun index ajouté uniquement parce qu'il « semble utile » ;
- distinguer coût SQL, latence réseau et blocage de boucle UI.

Le diagnostic de performance Windows / MySQL WAN est déjà instrumenté. Les actions lentes doivent être mesurées avant toute optimisation.

---

## Phase 3 — Modernisation UI/UX desktop

### Socle déjà intégré

- réglage d'échelle de l'interface ;
- modes Système / Clair / Sombre ;
- conservation des accents historiques Vert / Bleu / Noir ;
- design tokens et rôles sémantiques ;
- direction Fluent 2 pour la grammaire desktop ;
- Material Design 3 pour surfaces/tokens/thèmes ;
- Fluent System Icons comme bibliothèque principale ;
- instrumentation des freezes et temps d'ouverture ;
- modernisation progressive des composants communs.

### Références canoniques

- [`DESIGN_SYSTEM_UI_UX.md`](DESIGN_SYSTEM_UI_UX.md) ;
- [`WXPYTHON_UI_RULES.md`](WXPYTHON_UI_RULES.md) ;
- [`IMPLEMENTATION_ORDER.md`](IMPLEMENTATION_ORDER.md).

### Règles de travail

- parent visuel wxPython et contrôleur métier sont deux responsabilités différentes ;
- ne pas masquer une assertion avec `WXSUPPRESS_SIZER_FLAGS_CHECK` ;
- supprimer les sizers/tailles historiques rigides lorsqu'ils sont la cause ;
- pas de troncature artificielle des titres ;
- vérifier 100/120/150 % et les vrais contenus ;
- préserver les couleurs portant une information métier ;
- une correction centrale vaut mieux qu'une série de rustines locales.

### Suite

- poursuivre listes, grilles, champs, boutons, toolbars et dialogues partagés ;
- migrer ensuite les écrans métier ;
- consolider dashboard, navigation et panneaux AUI sans restaurer les rigidités historiques ;
- conserver une recette visuelle Windows réelle en complément des tests automatiques.

---

## Phase 4 — Commandes de repas

Le module historique est conservé, avec une logique métier recentrée sur le **point de livraison**.

Déjà intégré :

- dates issues des ouvertures et des consommations réellement réservées/présentes ;
- regroupement de plusieurs couples groupe/unité dans une même colonne de livraison ;
- colonne dédiée aux repas animateurs ;
- totaux par point de livraison ;
- modèles différents selon l'organisation de la période.

Règle critique : lorsqu'une date est complétée depuis les consommations, le calcul doit rester limité aux couples `IDgroupe` / `IDunite` configurés dans le modèle courant.

Référence : [`COMMANDES_REPAS_POINTS_LIVRAISON.md`](COMMANDES_REPAS_POINTS_LIVRAISON.md).

---

## Phase 5 — Reporting métier et pilotage annuel

### Noe-060 — Rapports fiables et prédéfinis

Objectif : supprimer les combinaisons manuelles fragiles de filtres pour les bilans récurrents.

Principe :

> une donnée → une règle de calcul canonique → plusieurs sorties.

Chantiers :

- Noe-060A : référentiel des indicateurs et moteur partagé ;
- Noe-060B : communes partenaires ALSH ;
- Noe-060C : communes homonymes / codes postaux ;
- Noe-060D : écran, tableur, PDF et annexes issus du même jeu de données ;
- Noe-060E : résidence datée et règles territoriales historisées ;
- Noe-060F : annulations, absences et historique compact.

### Noe-061 — Rapports d'activité

Les rapports PMSL existants servent de cahier des charges empirique pour automatiser les chiffres, tableaux, comparatifs et graphiques récurrents :

- ALSH ;
- EMS ;
- Sport-Santé ;
- EPS / mises à disposition ;
- indicateurs transversaux.

La rédaction qualitative reste humaine.

---

## Phase 6 — Tiers, conventions, mises à disposition et EPS

### Noe-062

Le but n'est pas de créer un second moteur de planning/facturation/documentation, mais de réutiliser les briques historiques de Noethys avec un modèle métier adapté aux structures.

Principes :

- tiers distinct de la relation contractuelle ;
- bénéficiaire et payeur éventuellement distincts ;
- contacts à rôles multiples ;
- programmation annuelle et renouvellement N-1 ;
- occurrences datées issues du moteur de récurrence historique ;
- convention, annexe et avenant depuis les mêmes données ;
- snapshots des documents officiels ;
- réalisé et facturation issus du même socle ;
- identifiants stables pour l'échange avec PMSL-Équipe.

### EPS écoles

Chaîne cible :

`vœux → arbitrage → cycles → programmation → affectation RH → réalisé → facturation → rapport d'activité`

Le planning annuel par école doit devenir une vue/export de la programmation acceptée, jamais une seconde saisie indépendante.

Référence : [`ARCHITECTURE-TIERS-PRESTATIONS-PLANNING.md`](ARCHITECTURE-TIERS-PRESTATIONS-PLANNING.md).

---

## Phase 7 — Portail Connecthys et contenus dynamiques

### Noe-063

Objectif : faire du portail une vue de données et contenus déjà maintenus ailleurs, sans double saisie et sans exposer directement la base locale.

Lots suivis :

- contenu externe compatible avec le Connecthys hébergé ;
- RSS / Atom natif avec cache sûr ;
- publication automatique des barèmes Noethys ;
- à terme, personnalisation authentifiée réellement liée au compte connecté ;
- contenus Piwigo / documents / réseaux lorsque le besoin est stabilisé.

Principes :

- le moteur tarifaire Noethys reste la source de vérité ;
- ne jamais afficher un faux « prix personnel » si le contexte de consommation est nécessaire ;
- conserver le dernier rendu valide en cas de panne d'une source externe ;
- aucune migration destructive ;
- compatibilité avec un Connecthys hébergé non modifié pour les premiers lots.

Les PR historiques empilées de ce chantier ne constituent pas toutes des cibles de fusion indépendantes ; la convergence doit se faire sur une branche propre construite depuis le `master` courant.

---

## Phase 8 — Extensions et intégrations optionnelles

Le dépôt expérimente un registre minimal d'extensions afin d'éviter d'intégrer chaque fournisseur ou besoin local directement au cœur historique.

Contraintes :

- opt-in ;
- aucun chargement arbitraire automatique ;
- aucune dépendance obligatoire à Internet ;
- aucune migration de base propre à une extension sans besoin concret et procédure testée ;
- premier usage potentiel : fournisseurs de communication, reporting ou connecteurs externes.

Ce socle reste séparé du noyau tant que ses hooks et cas d'usage réels ne sont pas stabilisés.

---

## Suivi opérationnel courant

Les issues GitHub constituent la source de vérité pour le travail restant. Au 22 août 2026, les grands groupes encore ouverts sont :

- validation réelle pré-RC : Noe-004 / Noe-030 / Noe-042 ;
- dette SQL progressive : Noe-005 ;
- reporting : Noe-060 et sous-lots ;
- rapport annuel : Noe-061 ;
- conventions / mises à disposition : Noe-062 ;
- portail Connecthys : Noe-063 et sous-lots.

Le détail et les numéros d'issues sont maintenus dans [`NOE-BACKLOG.md`](NOE-BACKLOG.md).

## Ordre de décision

Lorsqu'une nouvelle idée apparaît :

1. vérifier si une brique Noethys existe déjà ;
2. identifier la source de vérité métier ;
3. décider si le besoin appartient à Noethys ou à un projet voisin ;
4. documenter l'architecture avant une migration de données ;
5. implémenter par lot testable ;
6. valider sur copie réelle lorsque les données ou le métier sont concernés ;
7. mettre à jour issue, documentation et tests pour que la décision ne dépende pas d'une conversation.
