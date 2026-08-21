# Modernisation UI/UX Noethys

Principes d'architecture repris de Teamworks pour la modernisation progressive de Noethys.

- Moderniser réellement l'interface wxPython historique, pas seulement sa palette.
- Ne pas introduire de monkey-patch ou de surcouche globale destinée à corriger les anciens écrans au runtime. Le comportement moderne doit être codé dans les contrôles et layouts concernés.
- Remplacer progressivement les `FlexGridSizer`, `GridSizer`, `MultiSplitterWindow` et dimensions figées lorsqu'ils empêchent le redimensionnement. Privilégier `wx.BoxSizer` et `wx.SplitterWindow` lorsqu'ils simplifient la structure.
- Supprimer les panneaux et spacers historiques sans fonction réelle.
- Une fenêtre large doit utiliser sa largeur : les colonnes textuelles utiles absorbent l'espace libre. En espace insuffisant, préférer un scroll horizontal à une troncature généralisée.
- Le changement d'échelle de texte doit provoquer un vrai reflow : hauteur des lignes, boutons, en-têtes, séparateurs et fenêtres suivent l'échelle.
- Les petites icônes historiques doivent être placées dans des cibles d'action confortables, typiquement 36 à 44 px selon l'échelle, avec bitmap/SVG adapté.
- Les fenêtres et dialogues ont une taille initiale proportionnelle à l'écran et restent redimensionnables ; éviter les géométries historiques fixes.
- Les panneaux secondaires redimensionnables utilisent des splitters et des proportions initiales raisonnables.
- Conserver la densité d'une application desktop : pas de grosses cartes de type mobile.
- Séparer l'accent visuel (Vert/Bleu/Neutre) de l'apparence (Système/Clair/Sombre) et utiliser des tokens sémantiques.
- Le mode sombre utilise une palette dédiée, jamais une inversion.
- Préserver autant que possible les contrôles wx natifs pour hover/focus/pressed/accessibilité et compatibilité Windows/Linux/macOS.
- Les panneaux de dashboard peuvent utiliser `wx.aui.AuiManager` pour docking/détachement, mais démarrent visibles et dockés. Ne pas forcer `.Float()` à la création.
- Masquer/supprimer un gadget ne doit pas reconstruire tout le dashboard ni bloquer l'UI : masquer/détacher le pane, sauvegarder son état puis actualiser AUI.
- Versionner les perspectives afin qu'une ancienne disposition cassée ne soit pas restaurée après une évolution du dashboard.
- Refactoriser progressivement en conservant logique métier, callbacks et modèles de données ; remplacer uniquement la structure UI obsolète.

## Architecture « CSS Noethys »

Repens Design doit fonctionner comme un design system web centralisé : une règle graphique modifiée au centre se propage à tous les composants qui la consomment.

- `UTILS_DesignSystem.py` contient les rôles sémantiques et palettes.
- `UTILS_UIMetrics.py` contient les métriques d'échelle et de géométrie.
- `UTILS_Interface.py` porte les préférences utilisateur d'apparence.
- **`UTILS_StyleRepens.py` est la façade unique recommandée**, équivalent du CSS consommé par les composants.
- `CTRL_ActionRepens.py`, `CTRL_SurfaceRepens.py`, `CTRL_Bandeau.py`, `CTRL_TexteRepens.py` et `CTRL_FenetreRepens.py` doivent consommer cette façade plutôt que choisir directement couleurs ou dimensions.
- Les nouveaux dialogues utilisent `CTRL_FenetreRepens.Dialog`, les outils non modaux `CTRL_FenetreRepens.Frame`, et les blocs métier `CTRL_FenetreRepens.Section` lorsque ce patron convient.
- Un écran métier ne doit plus fixer de RGB, rayon, fonte, taille d'icône ou marge pour exprimer Repens Design. Il demande un rôle (`primary`, `surface`, `danger`, etc.) ou utilise un composant commun.
- Les dimensions métier intrinsèques restent autorisées lorsqu'elles décrivent réellement la donnée ; les dimensions purement décoratives doivent venir du design system.
- La migration est progressive : on ne monkey-patch pas `wx.Dialog` ou `wx.Panel`. Chaque écran adopte explicitement le shell commun lorsqu'il est refactorisé.

## Hiérarchie typographique sémantique

La typographie suit volontairement une logique proche de l'HTML : le code décrit le **niveau de sens**, jamais une taille de police locale. Noethys et Teamworks doivent employer la même gamme :

`Display → H1 → H2 → H3 → H4 → H5 → H6 → Lead → BodyLarge → Body → BodySmall → Label → Caption → Micro`, avec `DataLarge` pour les valeurs métier importantes.

À 100 %, la gamme couvre environ 7 à 18 points. Les tailles sont définies dans `UTILS_StyleRepens.py`, utilisent la fonte système native de Windows/Linux/macOS et suivent ensuite uniformément le réglage de texte 120/150/200 %.

- `Display` : exceptionnel, gros indicateur ou information dominante de tableau de bord.
- `H1` : titre principal d'une fenêtre ou d'un écran.
- `H2` : grande section métier.
- `H3` et `H4` : sous-sections.
- `H5` et `H6` : petits titres de groupes dans les interfaces denses.
- `Lead` : introduction ou texte d'accroche d'un écran.
- `BodyLarge`, `Body`, `BodySmall` : texte courant selon la densité nécessaire.
- `Label` : libellé court de contrôle, colonne ou groupe.
- `Caption` et `Micro` : informations secondaires très compactes.
- `DataLarge` : heures, compteurs, montants et valeurs métier importantes (`08:30`, `35 h`, `1 245 €`, etc.).

`CTRL_TexteRepens.py` est l'équivalent d'un élément texte HTML stylé par le CSS Repens : il expose directement les helpers `Display`, `H1` à `H6`, `Lead`, `BodyLarge`, `Body`, `BodySmall`, `Label`, `Caption`, `Micro` et `DataLarge`.

Le bandeau commun utilise `H1` puis `Lead`, les sections communes utilisent `H2`, et `Section.AjouterTitre()` crée un `H3` par défaut.

Les alias historiques `title`, `section`, `body_emphasis` et `overline` restent acceptés pour la compatibilité, mais les nouveaux écrans doivent utiliser la gamme sémantique commune.

## Règle générale

> Si un vieux layout empêche l'interface de s'adapter, on ne construit pas une couche autour pour le dompter : on le remplace proprement.

> Si un écran métier choisit lui-même son apparence, le design system n'est pas terminé : l'apparence doit remonter vers le socle Repens.

> Si un titre est défini par sa taille ou son gras plutôt que par son niveau sémantique, il n'est pas encore intégré au design system.
