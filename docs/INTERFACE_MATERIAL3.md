# Historique — première direction Material Design 3

> **Document historique.** La direction UI/UX canonique est désormais `docs/DESIGN_SYSTEM_UI_UX.md`, complétée pour wxPython par `docs/WXPYTHON_UI_RULES.md`.
>
> Material Design 3 reste une référence importante pour les tokens, rôles de couleurs, surfaces et thèmes. Il n’est plus la référence principale de la grammaire desktop : ce rôle revient maintenant à Fluent 2.

Ce document conserve la trace de la première phase de modernisation visuelle de Noethys et des choix déjà implémentés dans le moteur d’interface.

## Principes issus de cette phase

1. **Rôles sémantiques plutôt que couleurs RGB dispersées**
   - `surface`
   - `surface_container_lowest`
   - `surface_container_low`
   - `surface_container`
   - `surface_container_high`
   - `surface_container_highest`
   - `on_surface`
   - `on_surface_variant`
   - `outline`
   - `outline_variant`
   - `primary`, `on_primary`, `primary_container`, `on_primary_container`

   Les composants doivent progressivement consommer ces rôles via `UTILS_Interface.GetCouleurRole()`.

2. **Clair et sombre sont deux expressions du même produit**
   - le thème clair historique reste compatible ;
   - le sombre n’est pas une inversion noir/blanc ;
   - l’identité Vert/Bleu/Noir reste une couleur d’accent distincte de l’apparence clair/sombre.

3. **Hiérarchie par surfaces**
   - fond de l’application : `surface` ;
   - listes et contenus profonds : `surface_container_lowest` / `low` ;
   - panneaux et zones fonctionnelles : `surface_container` ;
   - boutons, contrôles saillants et éléments élevés : `surface_container_high` ;
   - éviter les grandes bordures lumineuses et les aplats blancs au milieu du sombre.

4. **Couleurs métier préservées**
   Les alertes, capacités, présences et états fonctionnels restent plus importants que la décoration. Rouge, jaune et vert ne sont donc pas supprimés. En mode sombre, ils utilisent des variantes moins lumineuses afin de garder le signal sans produire d’effet fluorescent.

5. **Texte et lisibilité**
   - texte principal : `on_surface` ;
   - informations secondaires : `on_surface_variant` ;
   - les textes métier peuvent utiliser une couleur dédiée lorsque leur fond porte un état ;
   - pas de blanc pur systématique sur fond presque noir.

6. **Densité desktop**
   Material 3 ne doit pas transformer Noethys en interface mobile surdimensionnée. Les espacements, rayons et tailles de contrôles sont adaptés à une application de gestion utilisée au clavier et à la souris. Le réglage d’échelle 80–200 % reste indépendant du thème.

7. **Composants communs avant écrans particuliers**
   La modernisation doit viser en priorité les briques transversales :
   - `ObjectListView` / `ListCtrl` ;
   - `wx.Grid` ;
   - panneaux et dialogues ;
   - barres d’outils ;
   - champs de saisie ;
   - boutons ;
   - états de sélection, focus, survol et désactivation.

   Une correction centrale vaut mieux qu’une série de retouches écran par écran.

8. **Compatibilité et progressivité**
   - aucun changement de schéma de données pour la couche visuelle ;
   - pas de régression du thème clair ;
   - les couleurs explicitement métier ne doivent pas être écrasées par le moteur de thème ;
   - les anciens écrans peuvent migrer progressivement vers les rôles sémantiques.

## Première implémentation

La première étape a été intégrée dans `Utils/UTILS_Interface.py` :

- palette sombre structurée sur des rôles inspirés de Material 3 ;
- accents sombres adaptés aux thèmes Vert/Bleu/Noir ;
- harmonisation des `ObjectListView` et `ListCtrl` pour supprimer le mélange blanc/vert clair + fond noir ;
- conservation des couleurs métier ;
- seconde passe de thématisation après création des fenêtres historiques afin de récupérer les contrôles qui définissent leurs couleurs tardivement ;
- aperçu des réglages d’apparence aligné sur les mêmes rôles.

## Suite

La suite ne doit pas être pilotée par ce document historique mais par :

- `DESIGN_SYSTEM_UI_UX.md` pour la direction générale ;
- `WXPYTHON_UI_RULES.md` pour les règles d’implémentation ;
- `IMPLEMENTATION_ORDER.md` pour l’ordre de migration.

La règle générale reste : **moderniser la grammaire visuelle sans réécrire le métier ni masquer l’information utile.**
