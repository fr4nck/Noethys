# Commandes de repas par points de livraison

## Objectif

Le module **Commandes des repas** doit produire une commande exploitable directement par le restaurateur et son livreur.

La notion métier principale n'est donc pas nécessairement l'activité ou le groupe Noethys : c'est le **point de livraison**.

Un point de livraison peut regrouper plusieurs activités, groupes ou unités Noethys lorsque les repas sont livrés au même endroit.

## Principe retenu

Le modèle de commande existant permet déjà de représenter cette logique sans modifier le schéma de la base :

- une colonne **Numérique (Avec suggestion)** représente le nombre de repas réservés pour un point de livraison ;
- cette colonne peut agréger plusieurs couples groupe/unité Noethys ;
- une colonne **Numérique (Libre)** peut être utilisée pour saisir les repas des animateurs ;
- une colonne **Numérique (Total)** additionne les repas enfants et animateurs du point de livraison ;
- plusieurs modèles de commande peuvent représenter des organisations de livraison différentes selon la période.

Le calcul des journées doit utiliser à la fois les ouvertures Noethys et les consommations réellement réservées ou présentes. Une journée comportant des repas réservés ne doit pas disparaître de la commande parce qu'une ouverture manque dans le paramétrage.

## Exemple PMSL

### Point de livraison Bais

Les activités peuvent être regroupées dans une seule colonne de repas réservés lorsque la livraison est commune :

- Bais moins de 6 ans ;
- Bais plus de 6 ans ;
- Club ados.

Configuration conseillée :

1. `Bais - enfants` : **Numérique (Avec suggestion)**, avec toutes les unités repas concernées ;
2. `Bais - animateurs` : **Numérique (Libre)** ;
3. `Bais - total livraison` : **Numérique (Total)**, additionnant les deux colonnes précédentes.

### Moutiers et La Guerche séparés

Créer pour chacun :

- une colonne enfants avec suggestion ;
- une colonne animateurs ;
- une colonne total livraison.

Ce modèle correspond aux périodes où le livreur doit effectuer deux livraisons distinctes.

### Moutiers et La Guerche regroupés

Créer un second modèle de commande dans lequel une même colonne de repas réservés agrège les unités de Moutiers et de La Guerche lorsque les repas sont livrés au même point.

Configuration conseillée :

1. `Moutiers + La Guerche - enfants` : toutes les unités repas concernées ;
2. `Moutiers + La Guerche - animateurs` : saisie du nombre de repas adultes ;
3. `Moutiers + La Guerche - total livraison` : total des deux.

## Gestion des périodes

La première étape conserve le fonctionnement historique de Noethys : le modèle est choisi lors de la création de la commande.

On peut donc disposer, par exemple, de :

- `Mercredis - livraisons séparées` ;
- `Vacances - Moutiers + La Guerche regroupés` ;
- tout autre modèle correspondant à une organisation réelle du livreur.

La période de la commande détermine les journées affichées et les réservations comptabilisées.

## Animateurs

Les repas animateurs ne proviennent pas actuellement des consommations enfants de Noethys. Ils doivent donc être conservés séparément des suggestions automatiques afin d'éviter de mélanger données réservées et ajustements humains.

Dans la première version, ils sont saisis dans une colonne numérique libre par point de livraison et sont inclus dans le total du point.

Une évolution ultérieure pourra alimenter automatiquement ces colonnes depuis le planning d'équipe PMSL lorsque la source de référence sera stabilisée.

## Évolutions prévues

1. rendre la notion de **point de livraison** explicite dans l'interface de création des modèles ;
2. proposer une catégorie de colonne dédiée **Animateurs** plutôt que le libellé générique `Numérique (Libre)` ;
3. permettre d'associer directement des règles de regroupement à des périodes ;
4. proposer automatiquement le bon modèle ou la bonne topologie de livraison selon la période ;
5. récupérer, lorsque cela est fiable, le nombre d'animateurs depuis la source de planning PMSL ;
6. conserver la possibilité de corriger manuellement les quantités avant impression ou envoi au restaurateur.
