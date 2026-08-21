# Noe-063 — Portail Connecthys : contenus dynamiques

## Objectif

Réduire les doubles saisies entre Noethys, le site web, Piwigo et Connecthys en faisant du portail famille une vue de contenus déjà maintenus ailleurs.

## Compatibilité

Le premier lot ne demande aucune modification de Connecthys ni du schéma de base. Les nouveaux contenus enrichis restent stockés et synchronisés comme des blocs historiques `bloc_texte` avec du `texte_html` compatible.

Les blocs Texte existants ne sont pas requalifiés automatiquement : seul le marqueur explicite `noethys_portail_contenu_externe` permet à Noethys de rouvrir un bloc dans l'éditeur `Contenu externe`.

## Lot A — Contenu externe

Le nouvel éditeur permet de configurer sans HTML :

- une URL HTTP(S) ;
- une hauteur d'affichage ;
- les barres de défilement ;
- le plein écran ;
- un titre accessible.

Noethys génère l'iframe, échappe les attributs et conserve la configuration dans le champ `parametres` existant.

## Lots prévus

### Lot B — RSS / Atom natif

Remplacer les widgets tiers de type FeedWind par une lecture directe des flux. Le HTML affiché dans Connecthys sera généré par Noethys et actualisé lors de la synchronisation. En cas d'indisponibilité temporaire du flux, la dernière version valide restera affichée.

### Lot C — Piwigo Display

Permettre les galeries, diaporamas et vidéos Piwigo via un embed dédié, sans recopier les médias dans Connecthys.

### Lot D — Mes tarifs

Afficher des tarifs issus des règles réellement configurées dans Noethys. L'objectif est de pouvoir limiter l'affichage aux activités qui concernent le compte connecté et d'éviter toute copie manuelle des grilles tarifaires.

### Lot E — Actualités ciblées

Prévoir trois politiques de diffusion : actualités générales de l'association, actualités liées aux inscriptions et sélection manuelle de catégories.

### Lot F — Présence numérique

Centraliser les liens vers le site, Facebook, Instagram, LinkedIn, Piwigo et d'autres services configurables afin de les réutiliser dans le portail sans ressaisie.

## Règle d'architecture

Une donnée métier doit avoir une source de vérité :

- Noethys pour les données de gestion et de tarification ;
- le site web pour les contenus éditoriaux et documents de référence ;
- Piwigo pour les médias ;
- Connecthys pour leur présentation aux comptes autorisés.
