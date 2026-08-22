# Direction UI/UX commune des projets

> Document de référence commun. Objectif : moderniser les interfaces de façon cohérente sans sacrifier la densité métier, la compatibilité, les habitudes des utilisateurs ni les conventions natives des plateformes.

## 1. Références de conception

La direction retenue combine plusieurs systèmes de design, chacun pour ce qu’il fait le mieux.

### Fluent 2 — référence principale

Fluent 2 sert de référence prioritaire pour :

- les applications desktop ;
- la densité d’information ;
- les formulaires, tableaux, listes et menus ;
- les barres d’outils ;
- les interactions clavier/souris ;
- les états `hover`, `focus`, `pressed`, `selected`, `disabled` ;
- les conventions natives de la plateforme ;
- la typographie et les espacements adaptés au desktop.

L’objectif n’est pas de fabriquer un clone de Microsoft 365, mais d’adopter une grammaire d’interface cohérente avec les usages desktop modernes.

### Material Design 3 — référence complémentaire

Material Design 3 sert surtout de référence pour :

- les design tokens ;
- les rôles sémantiques de couleurs ;
- les surfaces et leur hiérarchie ;
- les thèmes clair/sombre ;
- la cohérence entre composants ;
- les règles de contraste et de lisibilité.

### Apple Liquid Glass — inspiration ciblée

Liquid Glass sert uniquement d’inspiration pour :

- la séparation visuelle entre contenu et couche fonctionnelle ;
- les barres d’outils ;
- les panneaux flottants ;
- les popovers ;
- les dialogues ;
- certains éléments de navigation ;
- la notion de profondeur.

Ne pas multiplier les effets de verre, de transparence ou de flou. Le contenu métier doit rester prioritaire.

## 2. Principe général

Le système visuel doit être fondé sur des rôles sémantiques et non sur des couleurs RGB dispersées dans le code.

Exemples de rôles :

```text
surface
surface_container_lowest
surface_container_low
surface_container
surface_container_high
surface_container_highest

on_surface
on_surface_variant

primary
on_primary
primary_container
on_primary_container

outline
outline_variant

success
warning
danger
info

selection
selection_text
disabled
focus
```

Les composants doivent progressivement utiliser ces rôles au lieu de couleurs codées en dur.

## 3. Clair et sombre

Le thème sombre n’est pas une inversion du thème clair.

Il doit :

- conserver l’identité visuelle du produit ;
- utiliser plusieurs niveaux de surfaces ;
- éviter le noir pur comme unique fond de toute l’interface ;
- éviter le blanc pur comme texte courant ;
- limiter les contrastes agressifs ;
- adapter les couleurs saturées ;
- conserver les couleurs métier sans effet fluorescent ;
- empêcher les grandes zones blanches résiduelles dans une interface sombre.

Une palette sombre doit être complète : fond, panneaux, contrôles, listes, bordures, textes, sélections, états et couleurs métier.

Le changement de thème ne doit donc jamais se limiter à modifier uniquement la couleur d’arrière-plan de la fenêtre principale.

## 4. Hiérarchie des surfaces

La profondeur doit être construite principalement par les surfaces.

Exemple de hiérarchie :

```text
surface
└── fond général de l’application

surface_container_lowest
└── contenu profond / zones de données

surface_container_low
└── listes et tableaux

surface_container
└── panneaux fonctionnels

surface_container_high
└── barres, contrôles importants, éléments élevés

surface_container_highest
└── éléments flottants ou très saillants
```

Éviter les grandes bordures lumineuses. Une différence subtile de luminosité entre deux surfaces est généralement préférable.

## 5. Couleurs métier

Les couleurs métier restent prioritaires sur la décoration.

Exemples :

- vert : succès, validation, présence, capacité correcte ;
- jaune/orange : vigilance, information importante, capacité proche de la limite ;
- rouge : erreur, danger, dépassement, blocage ;
- bleu : information ou action neutre selon le contexte.

En mode sombre, ces couleurs doivent utiliser des variantes moins lumineuses et moins saturées.

L’information ne doit jamais reposer uniquement sur la couleur : utiliser aussi texte, icône, forme, libellé ou état.

## 6. Typographie

La typographie doit rester adaptée à un logiciel ou outil métier.

Principes :

- police native de la plateforme lorsque c’est pertinent ;
- hiérarchie simple : titre, section, corps, libellé, secondaire ;
- tailles compactes mais lisibles ;
- ne pas appliquer des proportions de mobile à une interface desktop ;
- conserver une densité adaptée au travail intensif.

Sous Windows, Segoe UI / Segoe UI Variable constitue une bonne référence. Sur Linux et macOS, privilégier les polices système natives.

## 7. Espacements et densité

Fluent 2 s’appuie sur une logique d’espacement cohérente.

Pour nos projets :

- utiliser une échelle d’espacement régulière ;
- éviter les marges arbitraires différentes sur chaque écran ;
- conserver une densité desktop ;
- ne pas transformer les formulaires et tableaux en cartes géantes ;
- augmenter légèrement l’aération seulement lorsque cela améliore réellement la lisibilité.

Une application métier doit rester rapide à parcourir avec la souris et le clavier.

## 8. États interactifs

Chaque composant interactif doit pouvoir distinguer clairement :

```text
normal
hover
focus
pressed
selected
disabled
error
```

Le focus clavier doit rester clairement visible.

Ne pas utiliser uniquement une variation de couleur trop faible pour indiquer un état important.

## 9. Icônes

### Bibliothèque principale

Utiliser en priorité **Microsoft Fluent System Icons**.

Principes :

- SVG comme source maître ;
- variantes `regular` par défaut ;
- variantes `filled` pour les éléments sélectionnés ou actifs lorsque cela améliore la compréhension ;
- taille cohérente par contexte ;
- couleur héritée du thème lorsque possible ;
- ne pas multiplier les styles d’icônes différents dans une même interface.

### Bibliothèque secondaire

Utiliser **Material Symbols** uniquement lorsqu’un pictogramme pertinent manque dans Fluent.

### Icônes Apple

Ne pas utiliser SF Symbols comme bibliothèque générale multi-plateforme.

### Migration des anciennes icônes

Ne pas remplacer brutalement toutes les icônes historiques.

Créer un catalogue central par rôle métier :

```text
ajouter
modifier
supprimer
valider
annuler
rechercher
imprimer
exporter
parametres
famille
individu
calendrier
facture
alerte
information
```

Puis migrer progressivement les composants communs et les écrans.

## 10. Matériaux, transparence et profondeur

Les effets de transparence doivent rester exceptionnels.

Utilisation possible :

- toolbar ;
- popover ;
- panneau flottant ;
- boîte de dialogue ;
- navigation secondaire.

Ne pas appliquer d’effet de verre derrière des tableaux, formulaires ou informations métier denses.

Le matériau ne doit jamais réduire la lisibilité.

## 11. Composants communs avant écrans particuliers

Toujours moderniser d’abord les briques transversales.

Ordre recommandé :

1. moteur de thème et design tokens ;
2. listes et tableaux ;
3. champs de saisie ;
4. boutons ;
5. barres d’outils ;
6. navigation ;
7. dialogues ;
8. états focus/hover/disabled ;
9. composants métier réutilisés ;
10. écrans particuliers.

Une correction centrale est préférable à des dizaines de retouches locales.

## 12. Compatibilité et progressivité

La modernisation visuelle ne doit pas provoquer de régression fonctionnelle.

Règles :

- aucune migration de données uniquement pour l’apparence ;
- préserver les configurations existantes ;
- préserver le comportement métier historique sauf décision explicite ;
- laisser les anciens écrans fonctionner pendant la migration ;
- éviter les dépendances lourdes uniquement pour obtenir un effet visuel ;
- respecter les conventions natives de Windows, Linux et macOS quand elles sont meilleures que notre personnalisation.

## 13. Accessibilité

À vérifier systématiquement :

- contraste suffisant ;
- focus clavier visible ;
- taille de texte lisible ;
- information non portée uniquement par la couleur ;
- état désactivé identifiable ;
- respect des préférences système clair/sombre lorsque l’utilisateur choisit le mode système ;
- limiter animations, transparence et effets visuels non nécessaires ;
- prévoir une interface utilisable sans effets décoratifs.

## 14. Philosophie du projet

La règle générale est :

> moderniser la grammaire visuelle sans masquer l’information utile, sans dégrader la densité métier et sans réécrire inutilement le fonctionnement historique.

En pratique :

- Fluent 2 pour la structure et l’ergonomie desktop ;
- Material Design 3 pour les tokens, couleurs et thèmes ;
- Liquid Glass pour certaines notions de profondeur et de couche fonctionnelle ;
- Fluent System Icons pour l’iconographie ;
- composants natifs et conventions de la plateforme chaque fois que c’est pertinent.

## 15. Checklist avant validation d’un écran

- [ ] Les couleurs viennent-elles de rôles sémantiques ?
- [ ] Le thème clair reste-t-il lisible ?
- [ ] Le thème sombre est-il cohérent sans zones blanches agressives ?
- [ ] Les couleurs métier restent-elles compréhensibles ?
- [ ] Le focus clavier est-il visible ?
- [ ] Les états hover/pressed/selected/disabled sont-ils distincts ?
- [ ] Les icônes sont-elles cohérentes avec le catalogue commun ?
- [ ] La densité reste-t-elle adaptée au desktop ?
- [ ] Les composants natifs sont-ils utilisés lorsque possible ?
- [ ] L’écran fonctionne-t-il correctement avec l’échelle d’interface ?
- [ ] L’information reste-t-elle compréhensible sans couleur ?
- [ ] La modernisation n’a-t-elle modifié aucune logique métier involontairement ?

## 16. Sources

### Microsoft Fluent 2

- https://fluent2.microsoft.design/
- https://fluent2.microsoft.design/design-principles
- https://fluent2.microsoft.design/design-tokens
- https://fluent2.microsoft.design/color
- https://fluent2.microsoft.design/typography
- https://fluent2.microsoft.design/material

### Microsoft Fluent System Icons

- https://github.com/microsoft/fluentui-system-icons

### Material Design 3

- https://m3.material.io/
- https://codelabs.developers.google.com/codelabs/design-material-darktheme?hl=fr

### Material Symbols

- https://developers.google.com/fonts/docs/material_symbols

### Apple Liquid Glass

- https://developer.apple.com/documentation/technologyoverviews/liquid-glass

### Ressources complémentaires sur le dark mode

- https://graphiste.com/blog/transitions-dark-mode/
- https://graphiste.com/blog/web-design-guide-mode-sombre/
- https://fr.console-linux.com/?p=26704

## 17. Version du document

Direction initiale définie en août 2026.

Ce fichier constitue désormais la référence UI/UX canonique du fork Upgrade Noethys. Les documents historiques plus anciens peuvent décrire une étape intermédiaire mais ne doivent pas remplacer cette direction.