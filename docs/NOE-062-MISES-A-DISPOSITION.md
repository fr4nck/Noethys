# Noe-062 — Mises à disposition et conventions

## But

Construire la gestion des mises à disposition sans recopier les moteurs déjà présents dans Noethys.

Le vocabulaire métier exposé à l'utilisateur est **Mises à disposition**. Le vieux module **Locations** reste une source de briques techniques ; il ne devient pas pour autant le modèle métier définitif d'une convention avec une association, une école ou une collectivité.

## Ce que le moteur `Locations` sait déjà faire

L'audit des fichiers `DLG_Saisie_location.py`, `OL_Locations.py` et `UTILS_Locations.py` montre que le socle historique fournit déjà :

- une période début/fin ;
- la création d'occurrences récurrentes ;
- la détection des indisponibilités ;
- des prestations liées avec leur date et leur montant ;
- l'historisation des créations/modifications/suppressions ;
- un questionnaire configurable de type `location` ;
- l'exposition des réponses de questionnaires dans les listes ;
- la construction de champs de fusion ;
- la génération PDF depuis les modèles de documents ;
- l'envoi par e-mail ;
- l'archivage possible d'un PDF dans les documents liés à une réponse de questionnaire.

Il faut réutiliser ces moteurs plutôt que créer des variantes `MiseADisposition_*` indépendantes.

## Limite du modèle historique

Une location est aujourd'hui centrée sur :

- `IDfamille` comme loueur ;
- `IDproduit` comme objet loué ;
- `locations` comme occurrence ;
- une prestation portant `categorie="location"` et `IDdonnee=IDlocation`.

Cette représentation est adaptée à la location de produits mais insuffisante pour porter proprement une relation contractuelle avec une personne morale, ses contacts, son groupe/sa section, ses règles d'adhésion éventuelles, sa programmation annuelle et son mode de facturation.

Le module historique ne doit donc pas être renommé artificiellement ni détourné en modèle universel.

## Premier noyau introduit

`Utils/UTILS_Mises_a_disposition.py` introduit un objet métier pur `ConventionMiseADisposition`.

Il est volontairement indépendant de wxPython et de `GestionDB` afin que les mêmes règles puissent être utilisées par :

- l'interface desktop ;
- les futures migrations de données ;
- l'édition de convention et d'avenant ;
- le reporting ;
- les échanges PMSL-Équipe ;
- des tests unitaires rapides.

Le noyau porte uniquement ce qui est déjà suffisamment stable pour être partagé :

- identifiant UUID stable ;
- période contractuelle ;
- référence ;
- statut ;
- version ;
- lien vers la convention parente pour un avenant ;
- mode de facturation ;
- champs de fusion canoniques.

Il ne crée aucune table et n'altère aucune base existante à ce stade.

## Cycle de vie initial

Statuts techniques autorisés :

- `brouillon` ;
- `validee` ;
- `signee` ;
- `terminee` ;
- `annulee`.

Modes de facturation initiaux issus de l'architecture cible :

- `manuelle` ;
- `mensuelle` ;
- `trimestrielle` ;
- `apres_realise`.

La période de validité est distincte du statut. Une convention peut couvrir une date tout en étant encore en brouillon ; les écrans devront donc choisir explicitement s'ils filtrent sur la période, le statut ou les deux.

## Champs de fusion canoniques

Le noyau expose :

- `{CONVENTION_ID_STABLE}` ;
- `{CONVENTION_REFERENCE}` ;
- `{CONVENTION_VERSION}` ;
- `{CONVENTION_STATUT}` ;
- `{CONVENTION_DATE_DEBUT}` ;
- `{CONVENTION_DATE_FIN}` ;
- `{CONVENTION_MODE_FACTURATION}` ;
- `{CONVENTION_PARENT_ID_STABLE}` ;
- `{CONVENTION_EST_AVENANT}`.

Ces champs ont vocation à rejoindre le moteur documentaire existant ; le modèle de convention fourni par PMSL doit être conservé dans son ordre et sa structure, sans réécriture arbitraire.

## Étapes suivantes

### Noe-062A — Tiers et contacts

Introduire de manière additive le tiers personne morale et ses contacts, sans identifiant administratif obligatoire. Une structure pourra cumuler plusieurs rôles.

### Noe-062B — Relation contractuelle

Relier tiers, saison, bénéficiaire/payeur, activité, groupe libre, tarif, adhésion éventuelle, mode de facturation et convention. La règle appartient à la relation et non au type de structure.

### Noe-062C — Programmation annuelle

Enregistrer les créneaux souhaités puis validés et permettre le renouvellement N-1 avec lignes inchangées/modifiées/supprimées/ajoutées.

### Noe-062D — Convention, annexe et avenants

Brancher les champs canoniques sur le moteur documentaire existant. L'annexe doit être générée date par date depuis la programmation validée ; un changement en cours d'année produit un avenant sans écraser la convention initiale.

### Noe-062E — Réalisé, facturation et reporting

Le même jeu de données doit alimenter planning, validation du réalisé, prestations, facturation et indicateurs. Aucune requête métier concurrente ne doit recalculer différemment les mêmes chiffres.

## Règles de compatibilité

- aucune migration destructive ;
- aucune modification implicite d'une base existante ;
- conservation des locations actuelles ;
- conservation du moteur prestations/facturation ;
- conservation des questionnaires et modèles documentaires ;
- tests sur copie de base réelle avant activation d'une future migration additive.
