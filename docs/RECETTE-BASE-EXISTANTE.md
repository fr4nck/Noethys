# Recette de validation sur base existante

Cette recette qualifie une version modernisée de Noethys Desktop avec une base déjà utilisée en production, sans migration implicite du schéma.

## Principe de sécurité

- Ne jamais effectuer la première recette sur l'unique base de production.
- Réaliser une sauvegarde complète avant essai.
- Pour les essais d'écriture, travailler sur une copie de la base ou sur un dossier de test explicitement identifié.
- Ne modifier le schéma SQL que dans le cadre d'une migration volontaire, isolée et revue.
- Le garde-fou `scripts/check_schema_compatibility.py` doit rester vert dans la CI.

## 1. Démarrage et connexion

- Lancer Noethys Desktop avec l'environnement Python/paquet qualifié.
- Ouvrir la base existante sans message de conversion ou migration inattendue.
- Vérifier que la fenêtre principale et les menus s'affichent normalement.
- Fermer puis rouvrir la base afin de valider la persistance de la configuration de connexion.

## 2. Lecture des données

Contrôler sur plusieurs enregistrements connus :

- individus et familles ;
- coordonnées et rattachements ;
- activités et groupes ;
- inscriptions ;
- consommations/réservations ;
- prestations et factures ;
- règlements et ventilations ;
- paramètres principaux de la structure.

Les valeurs affichées doivent correspondre aux données de référence avant modernisation.

## 3. Écritures métier sur copie de la base

Sur une copie de la base uniquement :

1. créer un enregistrement de test ;
2. modifier cet enregistrement ;
3. enregistrer et fermer la fiche ;
4. fermer puis rouvrir Noethys ;
5. vérifier que les modifications sont persistées ;
6. supprimer l'enregistrement de test ;
7. vérifier que les données voisines n'ont pas été altérées.

Répéter au minimum sur une fiche individu/famille et sur une opération métier représentative de l'utilisation réelle.

## 4. Facturation et règlements

Sur copie de la base :

- ouvrir une facture existante ;
- vérifier les montants, échéances et ventilations ;
- générer un document de test ;
- ouvrir un règlement existant ;
- vérifier les ventilations et soldes ;
- ne jamais lancer un prélèvement ou un paiement réel pendant la recette.

## 5. Documents, impressions et exports

Tester au minimum :

- génération PDF ;
- aperçu/impression ;
- export tableur/CSV utilisé habituellement ;
- chemins contenant des caractères accentués ;
- nom de fichier comportant des caractères non ASCII ;
- ouverture du fichier produit avec l'application cible.

## 6. Réseau et base distante

Si la base est hébergée sur MySQL/MariaDB :

- tester une connexion normale ;
- tester une fermeture puis reconnexion ;
- vérifier le comportement après une coupure réseau contrôlée ;
- confirmer qu'une erreur réseau ne provoque ni corruption ni écriture partielle visible ;
- vérifier que Noethys peut reprendre après rétablissement de la connexion.

Aucune montée de version du serveur MySQL/MariaDB ne doit être mélangée à cette recette : la qualification du client modernisé et la migration du serveur de base sont deux opérations distinctes.

## 7. Contrôle du schéma

Avant et après la recette sur copie, comparer la structure de la base lorsque l'outil serveur le permet :

- liste des tables ;
- colonnes ;
- index ;
- contraintes pertinentes.

L'ouverture normale du client modernisé ne doit pas ajouter, supprimer, renommer ou altérer ces objets sans migration explicitement prévue.

## 8. Performances de référence

Chronométrer les mêmes opérations sur l'ancienne version et la version modernisée, avec la même copie de base :

- ouverture de la base ;
- affichage d'une liste d'individus/familles ;
- ouverture d'une fiche ;
- affichage des consommations ;
- ouverture de la facturation ;
- génération d'un état représentatif.

Effectuer plusieurs mesures et conserver la médiane plutôt qu'un seul chronométrage.

Toute optimisation ultérieure doit être fondée sur ces mesures et non sur une impression subjective de rapidité.

## 9. Critères de validation

La version est qualifiable sur la base existante si :

- la CI permanente Windows/macOS/Linux est verte ;
- le garde-fou de schéma est vert ;
- la base s'ouvre sans migration imprévue ;
- les principales lectures correspondent aux données de référence ;
- les écritures de test persistent correctement sur une copie ;
- les documents et exports essentiels fonctionnent ;
- aucune corruption ni altération de schéma n'est observée ;
- les régressions éventuelles sont documentées avant diffusion.

## 10. Après qualification

Une montée de version MySQL/MariaDB, une modification de schéma ou une optimisation SQL doit faire l'objet d'une campagne séparée sur clone de la base, avec comparaison avant/après et possibilité de retour arrière.
