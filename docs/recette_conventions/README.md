# Modèles de recette — Convention (Noedoc)

Deux modèles de convention **entièrement anonymisés et fictifs**, prêts à
être importés dans une installation Noethys Vanilla pour tester la
fonctionnalité "Générer une convention" sans écrire de Python.

- `modele_convention_associative.ndc` — exemple court (1 page), style
  association sportive.
- `modele_convention_scolaire.ndc` — exemple long (multipage), style
  convention scolaire pluri-périodes.

Aucune donnée réelle (nom, adresse, personne) n'est présente dans ces
fichiers : tout le texte est un exemple générique à adapter.

## Import

Dans Noethys Vanilla : **Paramétrage > Modèles de documents**, catégorie
**Convention**, bouton **Importer** (icône import), sélectionner le
fichier `.ndc` souhaité.

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

Ces deux fichiers sont aussi rejoués automatiquement par
`tests/test_vanilla_convention_recette_modeles.py` (import réel +
génération PDF sur des données fictives) : toute modification qui les
casserait serait détectée en CI.
