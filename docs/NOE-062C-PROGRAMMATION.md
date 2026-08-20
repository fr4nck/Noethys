# Noe-062C — Programmation annuelle des mises à disposition

## Objectif

Décrire une programmation annuelle réutilisable par l'interface, les conventions, l'annexe prévisionnelle, PMSL-Équipe et le reporting, sans recopier le moteur de calendrier historique de Noethys.

Le socle est dans `Utils/UTILS_Mises_a_disposition_programmation.py` et ne dépend ni de wxPython ni de `GestionDB`.

## Séparation des responsabilités

La programmation décrit **ce qui est prévu contractuellement** :

- relation contractuelle ;
- saison ;
- jour de semaine ;
- heure de début et de fin ;
- période éventuelle ;
- groupe / section libre ;
- lieu ;
- observations ;
- état par rapport à N-1.

Elle ne calcule pas elle-même les dates réelles des séances.

Les vacances scolaires, jours fériés, semaines paires/impaires et autres règles de récurrence sont déjà gérés dans le module historique `Locations`. La future génération de l'annexe date par date devra passer par un adaptateur vers ce moteur, afin de conserver une seule logique de calendrier.

## `CreneauProgrammation`

Chaque créneau possède un UUID stable et est lié à l'UUID de sa relation contractuelle.

Règles :

- jour compris entre lundi et dimanche (`0..6`) ;
- heure de fin strictement postérieure à l'heure de début ;
- période facultative mais cohérente si elle est renseignée ;
- les horaires de nuit traversant minuit ne sont pas admis implicitement ; ils devront faire l'objet d'une règle explicite si le besoin apparaît ;
- durée prévisionnelle calculée en minutes ;
- données sérialisables sans objet wxPython ou base de données.

## Renouvellement N-1

Une ligne recopiée vers la nouvelle saison :

- reçoit un nouvel UUID ;
- conserve `identifiant_source`, l'UUID de la ligne N-1 ;
- commence en état `inchange` ;
- conserve jour, horaires, groupe, lieu et observations ;
- **ne recopie jamais implicitement les dates exactes de l'année précédente**.

La nouvelle période est fournie explicitement par l'appelant. Cela évite qu'une programmation 2025-2026 conserve silencieusement des dates 2025 lors de son passage en 2026-2027.

## États de comparaison

Chaque ligne de la saison renouvelée est classée :

- `inchange` ;
- `modifie` ;
- `supprime` ;
- `ajoute`.

Une ligne héritée puis modifiée garde son UUID de la nouvelle saison et son lien vers la source N-1.

Une ligne héritée puis supprimée reste présente avec l'état `supprime`, afin de conserver la décision métier et de pouvoir produire un comparatif.

Une ligne créée puis supprimée pendant la préparation de la même saison disparaît simplement : elle n'a jamais existé dans N-1 et ne doit pas créer une fausse trace de suppression.

## `ProgrammationAnnuelle`

La programmation annuelle porte :

- UUID stable ;
- UUID de la relation contractuelle ;
- saison ;
- statut ;
- UUID de la programmation source N-1 lorsqu'elle provient d'un renouvellement ;
- ensemble des créneaux.

Statuts initiaux :

- `brouillon` ;
- `soumise` ;
- `validee` ;
- `annulee`.

Le renouvellement d'une programmation validée crée une nouvelle programmation en brouillon. Seules les lignes conservées de N-1 sont recopiées.

## Synthèse du renouvellement

Le noyau peut fournir directement le nombre de lignes :

- inchangées ;
- modifiées ;
- supprimées ;
- ajoutées.

Cette synthèse pourra alimenter l'écran de traitement de la demande annuelle et le futur formulaire web de renouvellement sans recalcul concurrent.

## Champs de fusion

La programmation et les créneaux exposent des champs de fusion canoniques, notamment :

- saison ;
- statut ;
- relation ;
- nombre de créneaux ;
- compteurs de comparaison N-1 ;
- jour ;
- horaires ;
- durée ;
- groupe ;
- lieu ;
- période ;
- état de renouvellement.

Ces données serviront ensuite à l'annexe prévisionnelle, mais l'expansion date par date restera effectuée par le moteur calendrier existant.

## Compatibilité

Ce lot :

- ne crée aucune table ;
- ne modifie aucune table ;
- ne déclenche aucune migration ;
- ne touche pas aux locations existantes ;
- n'altère aucune prestation ni facturation ;
- reste testable sans wxPython.

## Étape suivante

**Noe-062D** : créer l'adaptateur entre la programmation validée et les moteurs existants de récurrence/document afin de produire :

1. les occurrences prévisionnelles ;
2. l'annexe date par date ;
3. les champs de fusion complets convention + bénéficiaire + payeur + contacts + programmation ;
4. un avenant lorsqu'une programmation validée change en cours de saison, sans écraser le document initial.
