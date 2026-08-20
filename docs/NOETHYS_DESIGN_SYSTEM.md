# Noethys Design System

Ce document définit le langage d'interface de Noethys indépendamment de son implémentation wxPython actuelle.

## Principe

Le métier et les parcours sont le produit. wxPython est un client desktop de ce produit.

Le design system doit pouvoir guider demain :

- Noethys Desktop (wxPython) ;
- un éventuel client mobile ;
- NoethysWeb ;
- les portails liés à Noethys.

## Références

- Fluent 2 : structure et ergonomie desktop ;
- Material Design 3 : tokens, rôles sémantiques, thèmes ;
- principes Liquid Glass : profondeur et séparation contenu/commandes, sans effets décoratifs systématiques ;
- Fluent System Icons : iconographie principale.

## Tokens portables

### Couleur

Les composants consomment des rôles, jamais des RGB métier dispersés :

`surface`, `surface_container`, `on_surface`, `on_surface_variant`, `primary`, `outline`, `selection`, `success`, `warning`, `danger`, `info`.

### Géométrie

La grille de base est 4 px. Les métriques principales sont :

- spacing : 4 / 8 / 12 / 16… ;
- icône inline : 20 ;
- icône toolbar : 24 ;
- ligne table/liste desktop : 28 ;
- hauteur toolbar : calculée depuis icône + texte + padding, jamais fixée indépendamment ;
- panneaux secondaires : compacts et redimensionnables.

Toutes ces valeurs sont des valeurs de référence à 100 % et suivent l'échelle utilisateur.

### Typographie

La taille du texte et l'échelle générale doivent rester deux notions distinctes. La police native de plateforme est privilégiée.

## Layout

Règles obligatoires :

1. Le contenu principal absorbe l'espace restant.
2. Les panneaux secondaires ne doivent pas créer de grands déserts vides.
3. Une liste ou un tableau redimensionnable doit redistribuer la largeur aux colonnes utiles.
4. Un contrôle ne doit jamais être plus grand que son conteneur calculé.
5. Une toolbar calcule sa hauteur à partir de son contenu.
6. Les dimensions fixes historiques doivent être supprimées lorsqu'elles empêchent le responsive.
7. Pas de surcouche destinée uniquement à sauver un mauvais sizer historique : remplacer le layout fautif.

## Densité

Noethys reste un logiciel métier desktop. Moderniser ne signifie pas transformer chaque action en grosse carte tactile.

Trois intentions suffisent : compact, standard, confortable. Le desktop utilise standard par défaut ; le mobile pourra employer une densité différente avec les mêmes rôles et parcours.

## Parcours plutôt que widgets

Exemple :

`Rechercher un individu -> ouvrir sa fiche -> consulter ses réservations`

est un parcours Noethys portable.

Sa représentation desktop peut être une table multi-colonnes ; sa représentation mobile peut être une liste compacte suivie d'une fiche. Le widget n'est pas le métier.

## Migration desktop

Ordre de refonte :

1. tokens et métriques communs ;
2. shell, menus et AUI ;
3. toolbars ;
4. listes et tableaux ;
5. formulaires et dialogues ;
6. dashboard ;
7. contrôles métier particuliers.

Une correction commune est préférée à une collection de patches écran par écran.

## Critères de recette

À 80, 100, 120, 150 et 200 % :

- aucun texte ou pictogramme tronqué ;
- toolbar suffisamment haute pour son contenu ;
- focus et états lisibles ;
- pas de tiers d'écran vide dû à une largeur figée ;
- listes et tableaux exploitent l'espace disponible ;
- clair et sombre conservent les mêmes hiérarchies ;
- couleurs métier cohérentes entre écrans ;
- fonctionnement métier inchangé.
