# Audit CI Windows — Noethys

Ce document décrit l'état **actuel** de la validation runtime/UI de Noethys et la recette manuelle à appliquer après la consolidation Repens.

## Objectif

La qualification doit détecter les régressions qui produisent des fenêtres vides, des freezes à l'ouverture, des dialogues partiellement construits, des assertions wxPython, des erreurs de sizer, des régressions clair/sombre ou de scaling et des incompatibilités runtime Python 3/Windows.

Le principe reste simple : **corriger à la source, ne jamais masquer le défaut**.

## Règles wxPython

1. Ne pas ajouter de surcouche destinée à contourner un bug wxPython.
2. Ne jamais utiliser `WXSUPPRESS_SIZER_FLAGS_CHECK`, `DisableConsistencyChecks()` ou un équivalent pour faire disparaître une assertion.
3. Conserver la logique métier existante lors des corrections structurelles.
4. Distinguer explicitement :
   - le **parent visuel wxPython**, qui possède le contrôle dans l'arbre de fenêtres ;
   - le **contrôleur métier**, qui expose les données, boutons et callbacks nécessaires.
5. Ne pas supposer que `self.parent` est le contrôleur métier. Un contrôle imbriqué dans un `Panel`, `StaticBox`, `ScrolledWindow`, `Notebook`, etc. reçoit un `controller=` explicite s'il a besoin d'accéder à la logique métier.
6. Vérifier l'ordre d'initialisation : un contrôle ne doit pas appeler `MAJ()`, `Refresh()`, `MAJListeCtrl()` ou un callback métier avant que les attributs qu'il utilise soient construits.
7. Corriger les familles de problèmes de façon cohérente : lorsqu'un motif est confirmé, rechercher les occurrences similaires avant le rerun.
8. Corriger les flags de sizer incompatibles plutôt que supprimer les contrôles ou inhiber les assertions.

Exemple attendu :

```python
contenu = self.section.GetContentPanel()
self.listCtrl = ListCtrl(contenu, controller=self)

class ListCtrl(wx.ListCtrl):
    def __init__(self, parent, controller):
        wx.ListCtrl.__init__(self, parent, ...)
        self.controller = controller
```

Le parent wx reste `contenu`; les appels métier passent par `self.controller`.

## Workflows actifs

### `.github/workflows/ci.yml`

C'est l'unique porte d'entrée de qualification générale.

Sur une PR ou un push `master`, un seul job Ubuntu rapide exécute notamment :

- compilation des sources et outils ;
- audits runtime ;
- tests métier et contrats UI ;
- surveillance des imports dynamiques PyInstaller ;
- garde des perspectives AUI ;
- audit layout wxPython ;
- audit du cycle de vie wxPython ;
- contrôle de compatibilité de schéma ;
- conservation des diagnostics UI.

Les contrôles indépendants continuent autant que possible après un échec, puis le bilan final rend le job rouge si nécessaire. La CI automatique ne lance pas de matrice multi-OS ni de packaging.

En lancement manuel `workflow_dispatch` avec le mode `complete`, le même workflow ajoute :

- recette synthétique et inventaires complets ;
- smoke test Windows ;
- smoke test macOS ;
- smoke test Linux GTK3 ;
- fabrication du package Windows portable via le workflow réutilisable.

### `.github/workflows/windows-package.yml`

Ce workflow est désormais un **workflow réutilisable** appelé par `ci.yml` en qualification complète. Il ne constitue plus une porte d'entrée autonome déclenchée à chaque PR.

L'ancien workflow séparé `ui-audit.yml` a été supprimé : les audits UI font désormais partie du job rapide unique de `ci.yml`.

## Audit layout

`scripts/audit_ui_layout.py` produit un inventaire des motifs historiques et modernes. Les catégories informatives servent à prioriser les corrections ; les suppressions d'assertions sont structurellement bloquantes.

Catégories suivies notamment :

- `align_expand_conflict` ;
- `aui_pane_fixed_size` ;
- `fixed_grid_column` ;
- `legacy_bitmap_button` ;
- `legacy_grid_lines` ;
- `legacy_style_dependency` ;
- `toolbar_bitmap_fixed` ;
- `window_fixed_min_size` ;
- `sizer_assertion_suppression`.

Une détection statique `ALIGN_* | wx.EXPAND` reste un **signal d'inspection**, pas une preuve de bug : l'orientation réelle du sizer doit être vérifiée avant correction.

## Audit cycle de vie wxPython

`scripts/audit_wx_lifecycle.py` cherche les couplages qui rendent la construction des fenêtres fragile.

Catégories :

- `visual_parent_business_coupling` : accès métier via le parent visuel ; informatif tant que le contexte n'est pas confirmé ;
- `visual_parent_ancestry_coupling` : accès métier via `self.parent.parent...` ou `GetGrandParent()` ; priorité élevée ;
- `constructor_callback_before_layout` : callback lancé pendant le constructeur avant layout ; inventaire large ;
- `constructor_callback_before_dependency` : callback lisant un attribut initialisé plus tard ; risque élevé ;
- `constructor_parent_callback` : callback métier lancé sur le parent depuis un constructeur wx explicite ; bloquant dans l'audit UI.

Les faux positifs provenant de classes métier non-wx comme certains `Track` sont exclus de la détection forte.

## Smoke test wxPython structurel

`tests/smoke_wx_layout.py` ne se contente pas de vérifier qu'un constructeur ne lève pas d'exception.

Pour les interfaces critiques, le test doit :

1. créer un `wx.App` valide ;
2. construire la fenêtre réelle ;
3. appeler `Layout()` ;
4. appeler `Show()` ;
5. laisser la boucle wx traiter les événements (`wx.Yield()` ou équivalent) ;
6. vérifier une taille cliente strictement positive ;
7. vérifier que les descendants attendus existent ;
8. vérifier qu'au moins un enfant visible possède une dimension positive ;
9. parcourir toutes les pages `Notebook`, `Treebook`, `Listbook`, `Choicebook` et `Toolbook` ;
10. sélectionner chaque page, relancer `Layout()`/yield et contrôler son contenu ;
11. restaurer proprement la sélection ;
12. appeler `Destroy()` proprement.

Une fenêtre vide, figée, partiellement construite ou déclenchant une assertion doit faire échouer la qualification.

## Dialogues prioritaires

La couverture structurelle et la recette manuelle doivent privilégier les fenêtres utilisées régulièrement :

- Préférences ;
- paramétrages ;
- fiches individuelles/familles ;
- inscriptions ;
- présences/consommations ;
- impressions ;
- autres dialogues métier ouverts depuis le shell principal.

Le dialogue Préférences est testé depuis son module réel `DLG_Preferences.py`. L'ancien adaptateur `DLG_Preferences_stable.py` a été supprimé : les corrections de layout doivent vivre dans le module métier d'origine.

`DLG_Impression_conso_differe.py` reste un chargement spécialisé distinct tant qu'il n'est pas démontré qu'il masque un défaut wxPython ; il doit être évalué séparément et non supprimé par analogie.

## Recette manuelle Windows post-Repens

La CI structurelle ne remplace pas l'observation de l'application réelle. Après un lot UI transverse, la recette locale Windows devient la source des prochains tickets : **on ne reprend pas une modernisation générale tant qu'aucun défaut concret n'est observé**.

### 1. Préparer la session

- synchroniser le dépôt sur le `master` courant et noter le SHA testé ;
- fermer les anciennes instances de Noethys ;
- lancer `DEV-Noethys.cmd` depuis la racine du dépôt.

`DEV-Noethys.cmd` appelle `scripts/dev_windows.ps1`, qui :

- crée si nécessaire un environnement `.venv` Python 3.10 ;
- met à jour les dépendances uniquement lorsque les fichiers requirements changent ;
- applique les correctifs Python 3/wxPhoenix validés ;
- lance Noethys depuis les sources avec diagnostics complets.

Les journaux utiles sont placés dans `noethys/Portable/`, notamment `journal.log`, `noethys_actions.log`, `noethys_crash.log` et `noethys_hang.log`.

### 2. Parcours minimal obligatoire

Tester au minimum :

1. démarrage et shell principal : aucune zone vide anormale, aucun freeze, panes AUI manipulables ;
2. recherche individus/familles : recherche, sélection, redimensionnement, actions principales ;
3. fiche famille puis fiche individu : navigation entre pages et fermeture propre ;
4. inscription : ouverture complète, changement de page, contrôles imbriqués ;
5. une liste métier ObjectListView : recherche, filtre, cochage et regroupement lorsqu'ils sont disponibles ;
6. un écran `wx.Grid` métier : sélection, scrolling, édition si autorisée, redimensionnement ;
7. Préférences : apparence, thème et échelle ;
8. présences/consommations puis un parcours d'impression représentatif ;
9. une saisie d'adresse : saisir/valider ville + code postal puis changer de focus ; si possible tester un nom de commune homonyme ;
10. fermeture de l'application sans assertion ni processus bloqué.

### 3. Clair, sombre et scaling

Le parcours doit être répété sur les contrôles critiques :

- en thème clair puis sombre ;
- à l'échelle normale puis au moins à une échelle agrandie courante (120/125 % ou 150 %).

À contrôler visuellement : texte non tronqué, absence de grands blocs blancs en sombre, focus visible, boutons accessibles, lignes et sélections lisibles, aucune perte de densité desktop injustifiée.

### 4. Format d'un défaut recevable

Pour chaque anomalie, relever :

- écran et chemin précis pour la reproduire ;
- thème et échelle utilisés ;
- résultat attendu / résultat observé ;
- capture d'écran si le défaut est visuel ;
- extrait du journal si une assertion, une exception ou un freeze apparaît ;
- SHA du `master` testé.

Un défaut visuel concret devient alors un lot ciblé. On recherche le même motif dans la famille de contrôles avant correction, mais on n'ouvre pas un nouveau chantier générique « moderniser Noethys ».

## wxAUI et Repens

La séparation actuelle est volontaire :

- **wxAUI** reste propriétaire de la géométrie : docking, sash, flottement, positions et perspectives utilisateur ;
- **Repens** applique la grammaire visuelle : surfaces, typographie, métriques, toolbars, notebooks, grilles et états.

Le code ne doit plus réinjecter en permanence une géométrie responsive dans les panes AUI après chargement d'une perspective ou déplacement utilisateur. `ReequilibrerWorkspace()` est un rafraîchissement natif, pas un moteur de placement.

## Boucle de correction

Pour chaque défaut confirmé :

1. reproduire le défaut ;
2. identifier la cause structurelle ;
3. rechercher le même motif dans la famille de contrôles ;
4. corriger un lot cohérent ;
5. relire le diff pour vérifier qu'aucune logique métier n'a changé accidentellement ;
6. relancer les chemins Windows critiques ;
7. répéter jusqu'au vert.

Les tests ne doivent pas être assouplis pour faire passer une implémentation cassée. En revanche, un test statique devenu obsolète après une évolution volontaire de l'architecture doit être réaligné sur le contrat réellement voulu.

## Risques runtime non-UI encore suivis

Les audits continuent de signaler notamment :

- accès à des résultats SQL par index sans garde suffisante ;
- connexions DB potentiellement non fermées ;
- `except:` trop larges ;
- séquences d'échappement invalides ;
- usages `eval()` / `exec()` à qualifier ;
- dépendances/chemins spécifiques à Windows ;
- packaging et modules COM.

Ces sujets restent distincts du nettoyage wxPython mais sont exécutés dans la même stratégie de stabilisation runtime.

## Critère de sortie

Une zone UI peut être considérée stabilisée lorsque :

- elle se construit avec le vrai module métier ;
- aucune assertion wxPython n'est supprimée ou masquée ;
- aucun accès métier fragile par ascendance visuelle n'est nécessaire ;
- les contrôles ne déclenchent pas de callbacks avant leurs dépendances ;
- les pages internes sont réellement construites et dimensionnées ;
- le smoke Windows passe ;
- les tests métier associés restent inchangés ou explicitement justifiés.
