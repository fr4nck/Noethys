# Noe-063B — RSS / Atom natif pour Connecthys

## But

Afficher dans le portail Connecthys un flux RSS ou Atom sans service tiers. Noethys lit le flux lors de la synchronisation, produit un HTML sûr puis l'exporte dans le mécanisme historique des blocs Texte.

## Principes

- aucune dépendance à FeedWind ;
- aucune modification du serveur Connecthys ;
- bibliothèques standard Python uniquement ;
- URL HTTP(S) uniquement ;
- taille et délai de téléchargement bornés ;
- parsing RSS 2.0 et Atom ;
- titres, dates, extraits et liens échappés ;
- aucun HTML ou script provenant du flux n'est injecté tel quel ;
- nombre d'articles configurable ;
- l'échec d'un flux ne doit jamais bloquer la synchronisation générale ;
- en cas d'échec, conserver le dernier HTML valide déjà stocké.

## Actualisation

Un bloc RSS est dynamique : la présence d'un tel bloc force la réexportation des pages/éléments à chaque synchronisation afin que les actualités suivent automatiquement la source web.

## Suite

Le ciblage par activité (ALSH, EMS, Sport-Santé, couture...) sera construit au-dessus de ce socle, avec possibilité de conserver un flux général commun à tous les adhérents.
