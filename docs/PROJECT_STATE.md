# Upgrade Noethys — état et décisions durables

> Consolidation au 24 août 2026. Ce document sert de point d’entrée durable afin que le chantier ne dépende pas de l’historique des conversations ChatGPT.

## 1. Positionnement du fork

Upgrade Noethys modernise **Noethys Desktop** sans réécrire inutilement son métier.

Priorités invariantes :

1. préserver les bases et configurations existantes ;
2. éviter toute migration implicite ou destructive ;
3. conserver le comportement métier historique sauf décision explicite ;
4. corriger les causes confirmées plutôt que masquer les symptômes ;
5. maintenir autant que raisonnablement possible la portabilité Windows / Linux / macOS ;
6. conserver une application desktop utilisable sans dépendance obligatoire à Internet.

Le dépôt amont reste une source de compatibilité, d’idées et de correctifs à examiner, pas une autorité qui doit écraser les choix du fork.

## 2. Sources de vérité du projet

Pour éviter que les décisions repartent dans les conversations, utiliser cet ordre :

1. **code et tests** pour le comportement réellement implémenté ;
2. **issues GitHub** pour le travail restant et les critères d’acceptation ;
3. **`docs/`** pour l’architecture, les décisions et les procédures ;
4. conversations uniquement pour le travail en cours avant consolidation.

Une décision durable prise en conversation doit donc finir dans une issue, un test ou un document du dépôt.

Une PR fermée sans fusion reste une référence historique de conception ou de diff, pas un comportement livré.

## 3. Frontières avec les projets voisins

### Noethys Desktop

Reste le cœur de gestion des familles, inscriptions, consommations, prestations, facturation et données ALSH/multi-activités.

### Teamworks-CCNS

Reste un projet distinct orienté RH / CCNS / contrôle du temps et organisation d’équipe. Ne pas fusionner ses responsabilités dans Noethys par simple commodité.

### PMSL-Équipe

Doit rester indépendant de Noethys. Les échanges doivent passer par une interface contrôlée, des identifiants stables et des imports/exports réconciliables, pas par un couplage direct aux tables de la base Noethys.

### Noethysweb / Connecthys

Noethysweb et Connecthys peuvent servir de sources d’idées, de modèles de données et de compatibilité future. Ils ne doivent pas devenir une dépendance obligatoire du desktop.

Le portail Connecthys peut évoluer par couches compatibles, sans exposer directement la base locale Noethys sur Internet.

## 4. Stabilité, CI, runtime et release

Références principales :

- `docs/DEVELOPMENT.md` ;
- `docs/CI-WINDOWS-AUDIT.md` ;
- `docs/RC-CHECKLIST.md` ;
- `docs/NOE-030-RECETTE-BASE-EXISTANTE.md` — procédure de recette sur copie réelle ;
- Noe-042 / issue #19 — **cockpit unique pré-RC** ;
- Noe-005 / issue #40 — reliquat SQL strict.

Les anciens lots Noe-002/#5, Noe-003/#6, Noe-004/#7 et Noe-030/#14 sont clos comme lots d’implémentation/outillage. Leurs opérations de validation réelle sont absorbées par le cockpit #19.

État courant de la CI :

- `.github/workflows/ci.yml` est la porte d’entrée commune ;
- PR / push `master` : validation rapide Ubuntu unique ;
- lancement manuel `complete` : recette synthétique, smokes Windows/macOS/Linux et packaging Windows ;
- `windows-package.yml` est réutilisable ;
- les audits UI font partie de la validation commune ;
- les diagnostics indépendants sont collectés avant le verdict final lorsque possible ;
- `scripts/audit_pre_rc.py` regroupe les inventaires SQL strict, cycle de vie wxPython et anciens outils de listes avant gel d’un SHA candidat.

Règles durables :

- une CI verte ne remplace pas une recette métier réelle ;
- ne jamais qualifier une RC sur l’unique base de production ;
- les audits statiques classent des risques, ils ne transforment pas automatiquement chaque occurrence en bug ;
- packaging Windows reproductible, mais sans fabriquer un paquet lourd à chaque modification sans raison ;
- les corrections runtime importantes doivent recevoir un test de non-régression lorsque cela est raisonnablement automatisable ;
- la qualification finale porte toujours sur le SHA exact destiné à la RC.

## 5. SQL et compatibilité des bases

Conserver :

- SQLite ;
- les installations MySQL/MariaDB historiques autant que raisonnablement possible ;
- les résultats métier et cardinalités historiques ;
- l’absence de migration silencieuse.

Ne pas moderniser une requête uniquement pour utiliser une fonctionnalité SQL récente si une forme plus compatible et claire existe.

Le chantier SQL strict restant est une dette progressive : traiter les requêtes par sémantique métier, jamais par ajout mécanique de colonnes au `GROUP BY` ou agrégats arbitraires.

## 6. UI/UX : direction canonique et état actuel

La référence actuelle est :

- `docs/DESIGN_SYSTEM_UI_UX.md` ;
- `docs/WXPYTHON_UI_RULES.md` ;
- `docs/IMPLEMENTATION_ORDER.md` ;
- `docs/CI-WINDOWS-AUDIT.md` pour la qualification réelle Windows.

`docs/INTERFACE_MATERIAL3.md` documente une étape antérieure de la modernisation : Material 3 reste utile pour les tokens et thèmes, mais **Fluent 2 est désormais la référence principale pour la grammaire desktop**.

Principes synthétiques :

- harmonie, frugalité, efficacité ;
- densité métier conservée ;
- composants communs avant corrections locales ;
- pas de grosses cartes ou marges décoratives qui gaspillent l’espace ;
- titres et contrôles réellement adaptatifs à l’échelle ;
- thème sombre complet, pas une simple inversion ;
- Fluent System Icons comme bibliothèque principale ;
- pas de surcouche destinée à cacher une assertion ou une architecture de layout incorrecte.

Le **socle transverse Repens est consolidé** depuis la PR #78 : listes/ObjectListView, grilles, outils de recherche/filtrage/cochage, navigation commune et états vides utilisent les règles partagées. Il n’existe plus de chantier générique « moderniser Noethys » à poursuivre pour lui-même.

Les travaux UI suivants doivent partir d’un défaut concret observé en recette Windows — fenêtre vide, freeze, mauvais contraste, texte tronqué, scaling cassé, contrôle spécialisé incohérent — ou d’un besoin métier explicite.

## 7. Règles wxPython désormais figées

Voir `docs/WXPYTHON_UI_RULES.md`.

Points à ne plus perdre :

- parent visuel et contrôleur métier sont deux responsabilités différentes ;
- pas de `WXSUPPRESS_SIZER_FLAGS_CHECK` pour cacher une erreur ;
- ne pas patcher le wxPython système/protégé pour corriger un défaut applicatif ;
- supprimer les sizers historiques rigides lorsqu’ils sont la cause du problème au lieu d’ajouter une couche par-dessus ;
- pas de hauteur de bandeau figée comme ancien contrat 76 px ;
- pas de titre tronqué artificiellement par découpe de chaîne ;
- tester les vrais contenus à 120/125 % et 150 % ;
- préserver les couleurs qui portent une sémantique métier ;
- traiter `Choicebook` avant les règles génériques de `Choice` dans le moteur de thème ;
- garder le texte lisible lorsqu’un contrôle conserve explicitement un fond clair en thème sombre ;
- résoudre les menus avec le libellé traduit correspondant à l’ID réellement utilisé.

## 8. Performance et ressenti

La vitesse technique et le confort perceptif sont deux sujets différents.

Une transition visuelle peut être légèrement amortie si cela améliore la compréhension, mais elle ne doit jamais ralentir le traitement métier ou réseau.

Pour les freezes et lenteurs :

- instrumenter avant dispatch ;
- mesurer les durées réelles ;
- conserver/loguer pendant l’investigation les actions dépassant 15 secondes ;
- distinguer latence widget/layout, blocage de boucle UI et latence MySQL distante.

Le but est d’éviter de « corriger » une lenteur réseau en bricolant le rendu, ou inversement.

## 9. Commandes de repas

Référence : `docs/COMMANDES_REPAS_POINTS_LIVRAISON.md`.

Décision métier : raisonner d’abord en **points de livraison**, pouvant agréger plusieurs groupes/unités.

Règle critique conservée : lorsqu’on complète les dates à partir des consommations, celles-ci doivent être filtrées par les couples `IDgroupe` / `IDunite` réellement configurés dans le modèle de commande. Il ne faut pas faire apparaître des journées étrangères au point de livraison.

## 10. Rapports, statistiques et source unique

Références :

- #51 — Rapports métier fiables et prédéfinis ;
- #54 — moteur partagé des indicateurs ;
- #55 — communes partenaires ALSH ;
- #53 — communes homonymes / codes postaux, **terminé** ;
- #56 — sorties écran/tableur/PDF du même résultat ;
- #57 — résidence datée ;
- #58 — annulations/absences ;
- #59 — rapports d’activité annuels.

Principe :

> une donnée → une règle de calcul canonique → plusieurs sorties.

L’objectif est de supprimer les recopies et les combinaisons manuelles de filtres qui rendent les bilans PMSL fragiles.

Les anciens rapports d’activité servent de cahier des charges empirique pour identifier les indicateurs réellement utiles.

La saisie ville/code postal a déjà été sécurisée pour ne plus remplacer silencieusement un couple valide par un homonyme lors de l’autocomplétion ou de la perte de focus.

## 11. Conventions, tiers et mises à disposition

Références :

- `docs/ARCHITECTURE-TIERS-PRESTATIONS-PLANNING.md` ;
- #60 — Noe-062, socle conventions et mises à disposition.

Ne pas recréer un deuxième moteur de planning, facturation ou documents.

Réutiliser les briques Noethys existantes lorsque leur sémantique convient, tout en séparant correctement :

- le tiers ;
- la relation contractuelle ;
- le bénéficiaire ;
- le payeur ;
- la programmation ;
- le réalisé ;
- la prestation/facturation ;
- les documents et champs de fusion.

Une même donnée canonique doit pouvoir alimenter interface, convention, annexe, reporting et export.

L’ancienne PR #61 a été fermée sans fusion car sa branche était devenue trop en retard sur `master`. Elle reste une référence d’architecture ; toute reprise doit reconstruire les lots utiles depuis le `master` courant.

## 12. Portail Connecthys et contenus dynamiques

Référence opérationnelle unique :

- #62 — contenus dynamiques, RSS/Atom, barèmes Noethys et source unique.

Les anciennes sous-issues #65 (RSS/Atom) et #67 (barèmes) sont closes après consolidation de leurs exigences dans #62.

Principes :

- pas de double saisie d’un tarif ou d’une donnée déjà disponible dans Noethys ;
- conserver la compatibilité avec un Connecthys hébergé existant pour les premiers lots ;
- ne pas inventer un deuxième moteur tarifaire simplifié ;
- afficher un barème applicable plutôt qu’un faux « prix personnel » lorsque la consommation réelle est nécessaire au calcul ;
- les intégrations web doivent être une vue sécurisée des données, pas un accès direct à la base locale.

Les anciennes PR #63/#66/#68/#69/#71/#72 ont été fermées sans fusion après inspection. Elles restent des références historiques ; toute reprise repart du `master` courant.

## 13. Extensions optionnelles

Le besoin d’un registre d’extensions opt-in reste une **piste dormante**, pas un chantier actif. L’issue #80 est close comme `not planned` tant qu’aucun premier consommateur concret ne justifie de rouvrir le sujet.

Si un besoin réel apparaît, conserver ces règles : pas de chargement arbitraire, pas de dépendance Internet obligatoire et pas de migration implicite.

L’ancienne PR #64 a été fermée et reste une référence historique de conception.

## 14. Doctrine de développement

À conserver pour les futurs chantiers :

- pas de reformatage massif sans valeur métier ;
- pas de surcouche cosmétique pour compenser une architecture incorrecte ;
- pas de nouvelle dépendance lourde uniquement pour un effet visuel ;
- une correction centrale vaut mieux que des dizaines d’exceptions locales ;
- conserver les anciennes configurations autant que possible ;
- ne pas mélanger un refactoring esthétique et une modification métier non liée ;
- lorsqu’un mécanisme historique reste correct, ne pas le réécrire pour le plaisir de le moderniser ;
- lorsqu’une branche de chantier dérive fortement de `master`, préserver le besoin dans une issue puis reconstruire un lot propre au lieu de forcer une fusion ancienne.

## 15. Ce qui a été consolidé depuis les conversations

Les points qui étaient encore particulièrement dépendants des échanges ont désormais une trace Git :

- direction UI/UX Fluent 2 + Material 3 + Liquid Glass ;
- catalogue/iconographie Fluent ;
- règles de parentage et de sizers wxPython ;
- politique contre les suppressions d’assertions ;
- comportement à l’échelle 120/150 % et titres longs ;
- exceptions dark mode et contrôles spécialisés ;
- méthode de diagnostic des freezes / MySQL distant ;
- distinction performance technique / confort perceptif ;
- filtrage des journées des commandes de repas ;
- frontières Noethys / Teamworks / PMSL-Équipe / Connecthys ;
- consolidation CI rapide/lourde ;
- agrégation des inventaires pré-RC via `scripts/audit_pre_rc.py` ;
- ligne d’arrivée du chantier UI transverse ;
- politique de fermeture/reconstruction des branches de chantier devenues obsolètes ;
- regroupement du suivi pré-RC dans #19 et du suivi portail dans #62.

À partir de ce point, ces décisions ne doivent plus dépendre de la conservation d’un chat.

## 16. Entretien de ce document

Mettre ce fichier à jour uniquement pour les décisions transversales qui seraient difficiles à retrouver dans une issue précise.

Le détail d’implémentation et les tâches doivent rester dans les issues et le code afin d’éviter que ce document devienne une seconde roadmap contradictoire.
