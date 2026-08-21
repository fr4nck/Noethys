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
- `CTRL_ActionRepens.py`, `CTRL_SurfaceRepens.py`, `CTRL_Bandeau.py` et `CTRL_FenetreRepens.py` doivent consommer cette façade plutôt que choisir directement couleurs ou dimensions.
- Les nouveaux dialogues utilisent `CTRL_FenetreRepens.Dialog`, les outils non modaux `CTRL_FenetreRepens.Frame`, et les blocs métier `CTRL_FenetreRepens.Section` lorsque ce patron convient.
- Un écran métier ne doit plus fixer de RGB, rayon, fonte, taille d'icône ou marge pour exprimer Repens Design. Il demande un rôle (`primary`, `surface`, `danger`, etc.) ou utilise un composant commun.
- Les dimensions métier intrinsèques restent autorisées lorsqu'elles décrivent réellement la donnée ; les dimensions purement décoratives doivent venir du design system.
- La migration est progressive : on ne monkey-patch pas `wx.Dialog` ou `wx.Panel`. Chaque écran adopte explicitement le shell commun lorsqu'il est refactorisé.

## Règle générale

> Si un vieux layout empêche l'interface de s'adapter, on ne construit pas une couche autour pour le dompter : on le remplace proprement.

> Si un écran métier choisit lui-même son apparence, le design system n'est pas terminé : l'apparence doit remonter vers le socle Repens.
