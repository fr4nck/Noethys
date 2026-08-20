# Noe-063C — Barèmes Noethys dans le portail Connecthys

## Principe

Noethys doit rester la source de vérité des tarifs. Le portail ne doit pas contenir une seconde copie manuelle des montants.

Le premier composant technique est un **descripteur pur de barèmes** : il transforme les dictionnaires tarifaires déjà utilisés par le moteur de facturation en une représentation publiable, sans recalculer les factures.

## Ce que le descripteur peut publier directement

- montant fixe ;
- tranches de quotient familial ;
- montant par date ;
- montant par date et quotient familial ;
- options tarifaires au choix ;
- dates de validité ;
- tarifs futurs ;
- catégorie tarifaire et activité lorsque ces libellés sont fournis par l'appelant.

## Ce qu'il ne doit pas présenter comme un prix certain

Les règles dépendant du contexte réel restent signalées comme telles :

- horaires ou durée ;
- quantité ;
- nombre d'enfants présents ;
- taux d'effort ;
- événement ;
- forfait/crédit disponible ;
- groupe ;
- étiquette de consommation ;
- cotisation ;
- caisse ;
- période scolaire/vacances ;
- filtre de questionnaire ;
- autres conditions utilisées par le moteur de facturation.

Le portail peut décrire ces règles, mais ne doit pas afficher « votre prix » tant que toutes les conditions nécessaires au calcul réel ne sont pas résolues.

## Compatibilité Connecthys

### V1

Noethys générera un bloc **Tarifs des activités** à partir des barèmes configurés. Le rendu restera un `bloc_texte` historique et ne nécessitera aucune modification du Connecthys hébergé.

### V2

Un véritable bloc **Mes tarifs**, différent pour chaque famille connectée, ne peut pas être obtenu proprement par un bloc HTML global. Connecthys connaît bien `current_user.IDfamille`, mais ses pages personnalisées chargent aujourd'hui les mêmes blocs et éléments pour tous les comptes.

La personnalisation fine nécessitera donc un point d'intégration authentifié côté Connecthys, notamment pour exploiter la catégorie tarifaire de l'inscription sans exposer d'identifiant familial dans une URL.

## Règle de développement

Le descripteur reste indépendant de wxPython et de la base. La lecture SQL et l'interface viendront dans des couches séparées afin que la logique de publication soit testable sans base réelle et puisse être réutilisée dans d'autres sorties (site, documents ou rapports).
