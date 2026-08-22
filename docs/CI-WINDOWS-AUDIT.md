# Audit CI Windows — Noethys

Ce document décrit l'état **actuel** de la validation runtime/UI de Noethys. Il remplace l'ancien état initial du dépôt, désormais obsolète.

## Objectif

La CI doit détecter les régressions qui produisent des fenêtres vides, des freezes à l'ouverture, des dialogues partiellement construits, des assertions wxPython, des erreurs de sizer et des incompatibilités runtime Python 3/Windows.

Le principe est simple : **corriger à la source, ne jamais masquer le défaut**.

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

La CI générale valide notamment :

- compilation Python ;
- audits runtime ;
- tests métier purs Python ;
- tests de migration/restauration/portable/RC ;
- smoke tests wxPython sur Windows ;
- smoke layout wxPython sur Windows, macOS et Linux lorsque le job le permet.

Le job Windows possède un `timeout-minutes: 10` afin qu'un freeze de dialogue devienne un échec CI au lieu de bloquer indéfiniment le runner.

### `.github/workflows/ui-audit.yml`

Le workflow UI exécute :

- `scripts/audit_ui_layout.py` ;
- `scripts/audit_wx_lifecycle.py` ;
- les tests unitaires de l'audit de cycle de vie wxPython ;
- l'upload des inventaires JSON pour analyse et comparaison.

L'audit bloque explicitement les mécanismes de suppression d'assertions de sizer.

## Audit layout

`scripts/audit_ui_layout.py` produit un inventaire des motifs historiques et modernes. Les catégories informatives servent à prioriser les migrations ; les suppressions d'assertions sont structurellement bloquantes.

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

Les faux positifs provenant de classes métier non-wx comme certains `Track` ont été exclus de la détection forte.

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

Une fenêtre vide, figée, partiellement construite ou déclenchant une assertion doit faire échouer la CI.

## Dialogues prioritaires

La couverture structurelle doit progresser en priorité sur les fenêtres utilisées régulièrement :

- Préférences ;
- paramétrages ;
- fiches individuelles/familles ;
- inscriptions ;
- contrats ;
- recrutement ;
- présences ;
- autres dialogues métier ouverts depuis le shell principal.

Le dialogue Préférences est désormais testé depuis son module réel `DLG_Preferences.py`. L'ancien adaptateur `DLG_Preferences_stable.py` a été supprimé : les corrections de layout doivent vivre dans le module métier d'origine.

`DLG_Impression_conso_differe.py` reste un chargement spécialisé distinct tant qu'il n'est pas démontré qu'il masque un défaut wxPython ; il doit être évalué séparément et non supprimé par analogie.

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

Les tests ne doivent pas être assouplis pour faire passer une implémentation cassée. En revanche, un test statique devenu obsolète après une évolution volontaire de l'architecture doit être réaligné sur le contrat réellement voulu, comme pour la séparation wxAUI/Repens ou la suppression de l'adaptateur Préférences.

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
