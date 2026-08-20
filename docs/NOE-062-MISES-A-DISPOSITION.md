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

## Noyau métier introduit

`Utils/UTILS_Mises_a_disposition.py` est volontairement indépendant de wxPython et de `GestionDB` afin que les mêmes règles puissent être utilisées par :

- l'interface desktop ;
- les futures migrations de données ;
- l'édition de convention et d'avenant ;
- le reporting ;
- les échanges PMSL-Équipe ;
- des tests unitaires rapides.

### Convention et avenants

`ConventionMiseADisposition` porte :

- identifiant UUID stable ;
- période contractuelle ;
- référence ;
- statut ;
- version ;
- lien vers la convention parente pour un avenant ;
- lien optionnel vers la relation contractuelle ;
- mode de facturation ;
- champs de fusion canoniques.

### Noe-062A — Structures et contacts

`StructureMiseADisposition` représente une structure opérationnelle ou juridique sans exiger d'identifiant administratif. Les types initiaux sont : association, école, collectivité, organisme, entreprise et autre.

Une école peut donc être bénéficiaire d'une intervention même si le payeur est une mairie, un OGEC ou une autre structure.

`ContactStructure` rattache une personne à une structure avec plusieurs rôles possibles : présidence, trésorerie, direction, APEL, responsable de section, planning, facturation, convention, administratif et urgence.

Les rôles sont cumulables et dédupliqués. Ils ne sont pas encodés dans le nom ou la fonction du contact.

### Noe-062B — Relation contractuelle

`RelationContractuelleMiseADisposition` porte les règles qui appartiennent à la relation et non au type de structure :

- structure bénéficiaire ;
- structure payeuse, distincte si nécessaire ;
- saison ;
- activité ;
- groupe / section libre ;
- tarif unitaire ;
- unité de tarif : heure, séance, forfait ou journée ;
- règle d'adhésion ;
- mode de facturation ;
- UUID stable partageable avec les autres composants.

Le tarif utilise `Decimal` afin de ne pas introduire d'arrondis binaires de type `float` dans le noyau financier.

Les règles d'adhésion possibles sont :

- `requise` ;
- `non_requise` ;
- `non_applicable` ;
- `exoneree`.

Cette séparation permet notamment à une même collectivité d'avoir une relation de financement où l'adhésion est non applicable et, dans un autre contexte, une mise à disposition avec une règle différente. Aucune règle du type « mairie = adhésion » n'est codée en dur.

### Noe-062C — Programmation annuelle et renouvellement

`Utils/UTILS_Mises_a_disposition_programmation.py` porte la programmation contractuelle sans générer de dates d'occurrence.

Un créneau contient :

- jour de semaine ;
- horaires ;
- période d'application éventuelle ;
- groupe / section ;
- lieu ;
- observations ;
- identifiant stable ;
- filiation vers le créneau N-1 lorsque la ligne est renouvelée.

Le renouvellement distingue explicitement `inchange`, `modifie`, `supprime` et `ajoute`. Les dates de l'année précédente ne sont jamais transposées implicitement.

### Noe-062D — Convention, annexe et avenants

`Utils/UTILS_Mises_a_disposition_documents.py` prépare la sortie documentaire sans dupliquer le moteur historique.

`RegleCalendrierMiseADisposition` traduit un créneau vers **le contrat exact attendu par la récurrence Locations** :

- `date_debut` / `date_fin` ;
- `heure_debut` / `heure_fin` ;
- `jours_scolaires` / `jours_vacances` ;
- `semaines` ;
- `feries`.

Le module ne contient volontairement **aucun calcul de vacances, jours fériés ou fréquence**. `GenererAnnexeDepuisProgrammation()` reçoit un `calculateur_occurences` et lui transmet ces paramètres. Le calculateur historique reste donc la source de vérité des dates.

L'annexe obtenue :

- est triée date par date ;
- conserve le lien vers chaque créneau ;
- déduplique une occurrence identique retournée deux fois ;
- totalise les durées ;
- expose des lignes structurées et des champs de fusion ;
- utilise des identifiants UUID5 déterministes pour qu'une même programmation et une même période produisent les mêmes identités d'annexe et d'occurrence.

`DossierDocumentaireMiseADisposition` fusionne ensuite les champs de :

- convention ou avenant ;
- relation contractuelle ;
- bénéficiaire ;
- payeur ;
- contact convention ;
- programmation ;
- annexe prévisionnelle.

Le résultat est un **paquet de modèle**, pas un second moteur PDF. Il est destiné à être consommé par les modèles documentaires Noethys existants afin de conserver strictement la structure du modèle PMSL.

Un avenant est identifié par sa filiation vers la convention parente. Il ne remplace pas la convention d'origine.

`SnapshotDocumentContractuel` permet enfin de figer le paquet de modèle avec une empreinte SHA-256. La règle de stockage future est simple : un document validé reçoit un snapshot ; une modification contractuelle crée un nouvel avenant / snapshot au lieu de recalculer silencieusement l'ancien document.

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

Le noyau expose des champs stables pour :

- la convention ;
- la structure bénéficiaire ;
- la structure payeuse ;
- le contact convention ;
- la relation contractuelle ;
- la programmation ;
- l'annexe ;
- le type de document.

Ils ont vocation à alimenter le moteur documentaire existant afin que convention, annexe, e-mail et reporting utilisent les mêmes données. Le modèle de convention fourni par PMSL doit être conservé dans son ordre et sa structure, sans réécriture arbitraire.

## Raccord au moteur historique

Le raccord est volontairement défini comme une **interface de calcul**, pas comme une copie de l'algorithme.

Aujourd'hui `DLG_Saisie_location.Calcule_occurences()` porte encore l'implémentation historique vacances / fériés / fréquence. Noe-062D sait déjà lui fournir exactement le dictionnaire attendu.

La dernière étape de raccord desktop consistera à sortir ce calcul du dialogue `DLG_Saisie_location.py` vers une fonction réutilisable, puis à faire appeler cette même fonction par :

1. le dialogue historique Locations ;
2. la génération d'annexe des mises à disposition.

Cette extraction doit préserver strictement le comportement actuel des locations. Elle n'est pas remplacée par une seconde implémentation.

## Stockage : décision reportée volontairement

Ce lot ne crée toujours aucune table et n'altère aucune base existante.

Le dépôt contient déjà une table historique `contacts`. Avant d'introduire un stockage pour les structures et leurs contacts, il faut cartographier ses usages réels et décider explicitement si elle peut être étendue sans ambiguïté ou si un stockage additif dédié est préférable.

Le même principe vaut pour la relation contractuelle, la programmation et les snapshots documentaires : le schéma ne sera introduit qu'après validation du modèle pur et avec une migration additive testée sur copie de base réelle.

## Étape suivante

### Noe-062E — Réalisé, facturation et reporting

Le même jeu de données doit alimenter planning, validation du réalisé, prestations, facturation et indicateurs. Aucune requête métier concurrente ne doit recalculer différemment les mêmes chiffres.

Avant activation en production, il restera également à :

- effectuer l'extraction technique du calculateur de récurrence hors du dialogue Locations ;
- brancher le paquet de modèle sur le modèle de convention PMSL effectivement utilisé ;
- introduire le stockage additif après recette sur copie de base réelle.

## Règles de compatibilité

- aucune migration destructive ;
- aucune modification implicite d'une base existante ;
- conservation des locations actuelles ;
- conservation du moteur prestations/facturation ;
- conservation des questionnaires et modèles documentaires ;
- aucun recalcul concurrent des vacances, jours fériés ou fréquences ;
- tests sur copie de base réelle avant activation d'une future migration additive.
