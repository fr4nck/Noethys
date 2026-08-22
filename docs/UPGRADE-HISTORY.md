# Historique du chantier Upgrade Noethys

> Historique consolidé au 22 août 2026.

## Pourquoi ce document ?

Noethys est un logiciel ancien, vaste et fortement lié à des usages métier réels. Le chantier Upgrade Noethys a donc choisi une modernisation incrémentale plutôt qu'une réécriture.

Ce document conserve les décisions structurantes afin qu'une reprise future du projet ne réintroduise pas des choix déjà étudiés ou ne casse pas involontairement la compatibilité historique.

Pour l'état courant, lire d'abord `PROJECT_STATE.md`, `ROADMAP.md` et `NOE-BACKLOG.md`.

## Principes figés

### Compatibilité avant nouveauté

Le chantier vise d'abord à prolonger Noethys Desktop :

- mêmes bases existantes autant que possible ;
- mêmes configurations ;
- même logique métier ;
- pas de migration implicite ;
- retour arrière possible ;
- corrections ciblées plutôt que refactorisation globale.

### Base réelle protégée

Une CI verte ne justifie jamais un test directement sur l'unique base de production. Toute RC doit passer par une copie et le scénario Noe-030.

### Windows prioritaire, code source multi-plateforme

Windows est la cible de distribution prioritaire. Le code source reste toutefois qualifié sur macOS et Linux GTK3 afin d'éviter une dérive Windows-only inutile.

### Python 3.10 comme baseline

Python 3.10 est retenu comme baseline de production pour la première RC modernisée. Python 3.11 et 3.12 ont été qualifiés mais restent des cibles de requalification, pas une migration imposée.

### Bases MySQL/MariaDB historiques

Aucune migration de serveur n'est imposée dans le chantier de modernisation. Les changements SQL doivent rester conservateurs et compatibles avec les installations anciennes lorsque cela est raisonnablement possible.

## Audit des forks

Un audit du réseau de forks a montré que `fr4nck/Noethys` est le fork moderne le plus avancé du réseau examiné.

Les autres forks ont servi de sources d'idées et de checklists de régression, pas de branches à fusionner en bloc :

- `JurassicPork/Noethys` : plusieurs correctifs historiques utiles comme liste de vérification ;
- `fautpasycraindre/Noethys` : idées de packaging Python moderne, mais versions/dépendances trop agressives pour un cherry-pick global ;
- autres forks : généralement anciens ou très peu divergents.

Décision : importer les **idées démontrées utiles**, jamais les historiques complets sans audit.

## SQL strict et bases

### Règlements

`OL_Reglements` regroupait une sélection large par seul `IDreglement`. La correction a remplacé le `GROUP BY` permissif par une pré-agrégation de `ventilation`, conservant :

- une ligne par règlement ;
- l'ordre des colonnes attendu par `Track` ;
- la somme historique de ventilation ;
- la compatibilité avec les anciens serveurs.

Des tests reproduisent l'ancien et le nouveau résultat.

### Export comptable

Les `GROUP BY` historiques ont été audités et corrigés sans changer la sémantique des exports. Des tests protègent notamment les cas QuadraCOMPTA/Cerig concernés.

### Index et performances

L'audit a privilégié les mesures et les usages réels plutôt qu'une création massive d'index pouvant modifier le coût des écritures ou la compatibilité des bases.

Le reliquat SQL strict est conservé dans Noe-005 comme dette progressive : les occurrences `REVIEW` ne sont pas assimilées à des bugs sans démonstration métier.

## Qualification Python

### Python 3.11

Qualification fusionnée : `07a62df7`.

- cœur/audits Linux ;
- wxPython macOS ;
- dépendances Windows ;
- build PyInstaller complet Windows.

### Python 3.12

Étude fusionnée : `25e56c2b`.

La compatibilité a été démontrée sans modifier la baseline. Les workflows profonds 3.11/3.12 ont ensuite été passés en déclenchement manuel afin de garder une CI courante frugale.

## wxPython Phoenix et plateformes

### Noe-020 — Phoenix

Fusion : `de0dc583`.

Un audit runtime a distingué les anciens noms wxPython encore supportés des vraies incompatibilités. Il a trouvé un défaut concret :

```text
wx.SystemSettings_GetFont
```

remplacé par :

```text
wx.SystemSettings.GetFont
```

Décision : ne pas réécrire massivement les aliases historiques qui restent fonctionnels.

### Noe-021 — Linux GTK3

Fusion : `150c9ea9`.

La CI utilise Ubuntu, wxPython GTK3 et Xvfb pour tester backend GTK, API Phoenix, cycle `wx.App` et layout représentatif.

### Noe-022 — macOS

Fusion : `d8d61a31`.

Le code source est qualifié automatiquement sur macOS avec un smoke de layout représentatif. Cette qualification n'est pas présentée comme un paquet macOS utilisateur signé/notarisé.

## Recette et non-régression

### Noe-030 — base existante

Outillage fusionné : `acedfa58`.

Le préflight :

- ouvre SQLite en lecture seule ;
- calcule SHA-256 avant/après ;
- produit un `schema_digest` ;
- ne sort pas de données nominatives ;
- dispose d'un mode MySQL/MariaDB conservateur.

L'issue reste ouverte jusqu'à la recette sur une copie de base réellement utilisée.

### Noe-031 — suite métier

Fusion : `e8e286a2`.

Tous les `tests/test_*.py` sont exécutés dans la CI principale.

Décision : un test métier doit vérifier un invariant observable, pas un détail d'implémentation.

## Sauvegarde et restauration

### Noe-032

Fusion : `f8cd03fe`.

L'audit a découvert plusieurs `return False` mal indentés dans `UTILS_Sauvegarde.Restauration`, rendant plusieurs chemins de restauration inconditionnellement défaillants.

La correction conserve les formats historiques et ajoute des tests de restauration SQLite et de flux MySQL simulé.

Décision : aucun changement de format de sauvegarde dans cette RC ; réparer d'abord la fiabilité du comportement existant.

## Packaging Windows

### Noe-040 — véritable artefact

Fusion : `4916ca15`.

Le premier smoke du véritable EXE a révélé un défaut important : PyInstaller 6 utilise par défaut un sous-dossier `_internal`, tandis que `Chemins.py` recherche historiquement les ressources à côté de `Noethys.exe`.

Correction :

```python
contents_directory="."
```

Le layout `onedir` plat est donc explicitement conservé.

Le workflow construit le bundle, contrôle les ressources, archive, ré-extrait, retire Python externe du contexte, lance réellement l'EXE et vérifie les imports embarqués.

### Noe-041 — vrai mode portable

Fusion : `bcd8ca96`.

Le dossier `Portable/`, déjà reconnu historiquement par Noethys, est désormais livré explicitement dans l'archive Windows.

Décision : réutiliser le mécanisme historique plutôt que créer un second système de configuration portable.

## Préparation RC initiale

La préparation documentaire et le sas RC ont établi la règle suivante : une RC n'est pas « validée » par la CI seule.

Les deux portes humaines restent :

1. recette Noe-030 sur une copie de base réellement utilisée ;
2. validation visuelle et métier de l'interface Windows sur cette copie.

La fabrication de la release est protégée et reste en brouillon jusqu'à décision explicite.

---

# Deuxième phase — modernisation UI et métier

À partir du 20 août 2026, le fork a continué à évoluer au-delà du socle technique pré-RC. Cette évolution ne remet pas en cause les règles de compatibilité ; elle élargit le périmètre du produit.

## Commandes de repas — PR #46

Le module historique de commandes a été adapté au fonctionnement réel par **points de livraison** sans migration de schéma :

- dates complétées depuis les consommations réservées/présentes ;
- une colonne de suggestion peut regrouper plusieurs couples groupe/unité ;
- repas animateurs saisis séparément ;
- total livraison = enfants + animateurs ;
- modèles distincts selon la topologie de livraison de la période.

Décision ultérieure consolidée : le complément de dates depuis les consommations doit rester limité aux couples groupe/unité réellement configurés dans le modèle courant.

## Échelle et apparence — PR #47

Noethys a reçu :

- une échelle d'interface réglable ;
- Système / Clair / Sombre ;
- conservation des accents historiques Vert / Bleu / Noir ;
- palette sombre prudente respectant les couleurs métier ;
- détection du thème applicatif Windows lorsque disponible.

Cette étape a montré que le dark mode et le scaling ne pouvaient pas être traités comme un simple skin : les métriques, contrôles natifs et layouts historiques devaient être corrigés progressivement.

## Crash AUI — PR #48

Un crash Windows dans `wx.lib.agw.aui.dockart.DrawCaption` a été attribué à des coordonnées `float` refusées par `wx.DC.DrawText`.

Le correctif a renforcé la qualification du runtime Windows et rappelé une règle importante : les incompatibilités de dépendance doivent être reproduites et contrôlées explicitement, pas masquées par des suppressions globales d'erreur.

## Diagnostic performance — PR #49

Un instrument de diagnostic a été ajouté afin de distinguer :

- temps entre action utilisateur et fenêtre visible ;
- connexions/requêtes MySQL distantes ;
- faux gels de démarrage ;
- blocages réels de la boucle UI.

Décision : ne pas ajouter de délai/fondu artificiel pour « améliorer » une lenteur avant d'avoir mesuré son origine.

## Design system — PR #50

Le chantier UI a été recentré autour d'un système commun :

- Fluent 2 pour la grammaire desktop ;
- Material Design 3 pour tokens, rôles et surfaces ;
- profondeur très contenue inspirée de Liquid Glass ;
- Fluent System Icons comme bibliothèque principale ;
- densité métier conservée ;
- états focus/hover/pressed/disabled explicites ;
- préférences d'apparence et d'accessibilité sans impact sur les données métier.

La référence actuelle est `DESIGN_SYSTEM_UI_UX.md`. L'ancien `INTERFACE_MATERIAL3.md` est conservé uniquement comme document historique de la première étape.

## Doctrine wxPython issue de la recette visuelle

Les essais réels ont produit plusieurs règles désormais figées dans `WXPYTHON_UI_RULES.md` :

- parent visuel et contrôleur métier doivent être distincts lorsqu'ils n'ont pas le même rôle ;
- ne pas utiliser `WXSUPPRESS_SIZER_FLAGS_CHECK` ;
- ne pas masquer les erreurs de layout par une surcouche ;
- corriger l'ordre d'initialisation des dialogues et contrôles ;
- ne pas tronquer artificiellement les titres ;
- ne pas réintroduire les anciennes hauteurs figées ;
- vérifier les vrais contenus à 120/150 % ;
- préserver les couleurs portant une sémantique métier ;
- les contrôles spécialisés doivent être traités avant les règles génériques du moteur de thème.

## Atomicité des contrats PSU

Le commit `4e3b30dd953b4ae462c468c06f341e4edaae2adf` a rendu atomique la sauvegarde d'un contrat PSU, de ses prestations et de ses consommations.

Décision : en cas d'échec partiel, rollback de l'ensemble et aucun état intermédiaire validé.

Cette correction illustre la doctrine générale : lorsqu'une opération métier est perçue comme unique par l'utilisateur, les écritures liées doivent éviter autant que possible les validations partielles incohérentes.

---

# Troisième phase — source unique et extensions métier

## Noe-060 — reporting fiable

Le besoin métier récurrent a conduit à formaliser :

> une donnée → une règle de calcul canonique → plusieurs sorties.

Le chantier couvre indicateurs, communes partenaires, résidence datée, annulations/absences, exports cohérents et rapports prédéfinis.

## Noe-061 — rapports d'activité

Les rapports PMSL existants deviennent un cahier des charges empirique : Noethys doit produire automatiquement les chiffres, tableaux, graphiques et évolutions récurrentes, tandis que l'analyse qualitative reste humaine.

## Noe-062 — conventions et mises à disposition

Le chantier réutilise les moteurs historiques de Noethys au lieu de créer une deuxième chaîne parallèle.

Décisions structurantes :

- tiers distinct de la relation contractuelle ;
- bénéficiaire et payeur distincts si nécessaire ;
- programmation annuelle et renouvellement N-1 ;
- convention/avenant/annexe issus des mêmes données ;
- snapshots pour figer les documents officiels ;
- PMSL-Équipe reste la source RH/planning des intervenants ;
- identifiants stables pour synchroniser sans coupler directement les bases.

Le cas EPS est décrit comme une chaîne continue : vœux → arbitrage → cycles → programmation → affectation → réalisé → facturation → rapport.

## Noe-063 — portail Connecthys

Le portail est orienté vers une logique de **contenus dynamiques et source unique** :

- contenus externes sans HTML saisi à la main ;
- RSS/Atom natif ;
- barèmes générés depuis Noethys ;
- compatibilité avec le Connecthys hébergé pour les premiers lots ;
- aucune pseudo-personnalisation basée sur un ID famille exposé ;
- pas de duplication du moteur tarifaire.

Les anciennes branches empilées du chantier portail ont conduit à une décision de convergence : reconstruire proprement sur le `master` courant plutôt que fusionner une pile de commits devenue trop éloignée.

## Extensions optionnelles

Un registre minimal d'extensions a été proposé pour accueillir à terme des intégrations optionnelles sans ajouter chaque fournisseur directement au cœur historique.

Décision : pas de chargement arbitraire automatique, pas de dépendance obligatoire à Internet, et aucun élargissement du contrat d'extension avant un besoin concret.

---

# Consolidation documentaire du 22 août 2026

Une revue des conversations de travail a montré que la majorité des décisions étaient déjà dans Git, mais que certains choix récents restaient dispersés.

Ont donc été consolidés :

- `PROJECT_STATE.md` — point d'entrée durable ;
- `DESIGN_SYSTEM_UI_UX.md` — direction UI/UX canonique ;
- `WXPYTHON_UI_RULES.md` — doctrine wxPython ;
- `ARCHITECTURE-TIERS-PRESTATIONS-PLANNING.md` — architecture structures/EPS ;
- `COMMANDES_REPAS_POINTS_LIVRAISON.md` — règle métier repas ;
- `ROADMAP.md`, `NOE-BACKLOG.md`, `README.md` et les documents RC remis au niveau de l'état courant ;
- `docs/README.md` — index distinguant documents canoniques et historiques.

Décision finale : **une conversation ne doit plus être l'unique source d'une règle durable**. Le code/test, l'issue ou la documentation Git doivent conserver la décision avant que le chat puisse être supprimé.

## Choix toujours volontairement reportés

- installateur Windows système ;
- signature de code ;
- packaging utilisateur macOS ;
- packaging utilisateur Linux ;
- bascule baseline Python 3.11/3.12 ;
- migration obligatoire MySQL/MariaDB ;
- réécriture globale de l'architecture desktop.

Ces reports réduisent le risque et permettent de poursuivre l'amélioration sans casser le socle historique.
