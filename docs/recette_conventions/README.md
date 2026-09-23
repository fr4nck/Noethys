# Modèles de recette — Convention (Noedoc)

Deux modèles de convention **entièrement anonymisés et fictifs, à titre
d'exemple** — **pas encore le modèle officiel fidèle à la référence
visuelle réelle** (voir le suivi de fidélité visuelle) — prêts à être
importés dans une installation Noethys Vanilla pour tester la
fonctionnalité "Générer une convention" sans écrire de Python.

- `modele_convention_associative.ndc` — exemple court (1 page), style
  association sportive.
- `modele_convention_scolaire.ndc` — exemple long (multipage), style
  convention scolaire pluri-périodes.

Aucune donnée réelle (nom, adresse, personne) n'est présente dans ces
fichiers : tout le texte est un exemple générique à adapter.

## Emplacement réel des fichiers

Ces fichiers vivent désormais dans
`noethys/Static/ModelesConventionExemples/` (et non plus dans ce
dossier `docs/`) : `noethys/Static/` est le seul dossier de ressources
réellement embarqué dans le portable et l'installateur Windows (voir
`packaging/vanilla-noethys.spec`, clé `datas`). Une installation réelle
(Setup ou portable) contient donc ces deux fichiers sur le poste de
l'utilisateur, **sans accès au dépôt GitHub**.

## Import (utilisateur réel, sans toucher au code)

Dans Noethys Vanilla : **Paramétrage > Modèles de documents**, catégorie
**Convention**, bouton **Importer** (icône import), naviguer jusqu'au
dossier d'installation puis `Static/ModelesConventionExemples/` et
sélectionner le fichier `.ndc` souhaité.

## Ce que vous pouvez tester sans toucher au code

Une fois un modèle importé, ouvrez-le dans le concepteur Noedoc
(bouton **Modifier**) et vérifiez que chacune de ces actions se reflète
bien dans le PDF généré depuis une fiche Famille (**Outils > Générer une
convention**) :

- modifier le texte d'un article ;
- ajouter ou supprimer un article (un nouveau bloc de texte à l'intérieur
  du cadre principal s'écoule automatiquement sur la ou les pages
  suivantes) ;
- changer le titre du document ;
- changer le texte affiché autour du tarif (`{CONVENTION_TARIF_HORAIRE}`) ;
- déplacer ou redimensionner un bloc (dans le cadre principal = texte qui
  s'écoule ; hors du cadre principal = objet à position fixe, ex. logo,
  numéro de page) ;
- générer un aperçu / PDF.

Les champs dynamiques (`{CONVENTION_PLANNING_DETAIL}`,
`{CONVENTION_TARIF_HORAIRE}`, `{CONVENTION_REPRESENTANT_NOM_COMPLET}`,
`{CONVENTION_DATE_SIGNATURE}`, `{CONVENTION_LIEU_SIGNATURE}`, ...) sont
listés avec leur description dans le concepteur Noedoc (catégorie
Convention) et documentés dans
`noethys/Utils/UTILS_Convention_champs.py`.

## Import idempotent (sans doublon)

`Utils.UTILS_Export_documents.ImporterModeleExempleIdempotent(fichier)`
importe l'un de ces fichiers sans jamais créer de doublon : si un modèle
portant exactement le même nom et la même catégorie existe déjà, il est
laissé tel quel (jamais modifié) et son IDmodele existant est renvoyé.
Le bouton générique "Importer" de l'écran Modèles de documents, lui,
continue de toujours créer un nouveau modèle (comportement historique,
inchangé, pour tout import utilisateur classique).

## Tests

Ces deux fichiers sont rejoués automatiquement par
`tests/test_vanilla_convention_recette_modeles.py` (import réel +
génération PDF sur des données fictives) et par
`tests/test_vanilla_convention_modele_persistance.py` (import
idempotent, absence de doublon) : toute modification qui les casserait
serait détectée en CI. Leur présence réelle dans l'artefact construit
(Setup/portable) est vérifiée par l'étape CI "Vérifier la présence des
modèles Convention d'exemple dans le paquet".

## À faire avant de qualifier un de ces modèles comme "officiel"

Ces fichiers restent des **exemples génériques**, pas la référence
visuelle réelle. Avant de les proposer comme modèle officiel à un
utilisateur réel, voir le suivi de fidélité visuelle (PDF de référence)
dans le rapport de recette correspondant.
