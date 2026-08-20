# Direction d’interface — Noethys × Material Design 3

Ce document fixe la direction de modernisation visuelle de Noethys. Material Design 3 sert de système de référence, pas de skin à recopier. Noethys reste une application desktop wxPython et conserve ses codes métier, son fonctionnement historique et la densité utile à un logiciel de gestion.

## Principes

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

La première étape est intégrée dans `Utils/UTILS_Interface.py` :

- palette sombre structurée sur des rôles inspirés de Material 3 ;
- accents sombres adaptés aux thèmes Vert/Bleu/Noir ;
- harmonisation des `ObjectListView` et `ListCtrl` pour supprimer le mélange blanc/vert clair + fond noir ;
- conservation des couleurs métier ;
- seconde passe de thématisation après création des fenêtres historiques afin de récupérer les contrôles qui définissent leurs couleurs tardivement ;
- aperçu des réglages d’apparence aligné sur les mêmes rôles.

## Suite logique

- créer des rôles typographiques communs (titre, section, corps, libellé, secondaire) ;
- normaliser les états hover/focus/pressed/disabled ;
- harmoniser les barres d’outils et actions principales ;
- définir une échelle d’espacement commune ;
- réduire progressivement les couleurs codées en dur dans les écrans ;
- adapter les tableaux métier les plus utilisés sans perdre leur densité ;
- tester Windows, Linux et macOS séparément car le rendu natif wxWidgets diffère selon la plateforme.

## Références de conception

- Material Design 3 : https://m3.material.io/
- Material dark theme codelab : https://codelabs.developers.google.com/codelabs/design-material-darktheme?hl=fr

La règle générale reste simple : **moderniser la grammaire visuelle sans réécrire le métier ni masquer l’information utile.**
