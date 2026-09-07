# Stabilisation Vanilla — décisions de recette humaine

## Statut

**VALIDATION MANUELLE REQUISE** — ne pas taguer Vanilla stable avant une nouvelle recette humaine Windows du candidat issu de cette stabilisation.

Le candidat précédent `74d25fdd8431eb7a167ab35cab8e1e8aa4e3bdc9` reste la référence des qualifications acquises avant ces corrections UX, mais il est remplacé pour la poursuite de la recette.

## Décisions UX issues de la recette humaine

- **Thème sombre rejeté en recette humaine.**
- **Thème clair retenu** pour Vanilla.
- **Comportement « Voir tout » rejeté** sur la recherche individus/familles de l'accueil.
- **Décision : retour à l'affichage direct de la liste complète** quand aucun texte de recherche n'est saisi.
- **Suivi automatique du thème système désactivé pour Vanilla.**
- **Thème sombre wxPython / widgets wx temporairement non supporté** tant qu'un rendu sombre cohérent n'a pas été conçu et validé.

## Périmètre technique de la correction

### Liste d'accueil

Le composant concerné est `noethys/Ctrl/CTRL_Recherche_individus.py`, dans `BarreRechercheAccueil.Recherche` et le bouton `ctrl_voir_tout` du `Panel`.

Avant correction, une recherche vide vidait les objets affichés et basculait vers un état d'attente ; le bouton « Voir tout » réinjectait ensuite `listView.donnees`. La stabilisation supprime cette étape intermédiaire : une recherche vide affiche directement `listView.donnees`.

Le chargement reste exclusivement assuré par `ctrl_listview.MAJ(forceActualisation=True)` dans `Panel.MAJ`. La recherche, ses critères, sa limite de résultats, les actions disponibles et la logique métier ne sont pas modifiés.

### Thème clair Vanilla

La préférence active `interface_apparence` est forcée à `clair` par la couche de configuration UI. Sur Windows, l'option wxMSW `msw.dark-mode` est explicitement positionnée à `0` avant la création de `wx.App`, afin que le rendu natif wx ne suive pas le mode sombre Windows.

Le dialogue d'apparence reste présent pour l'échelle, la taille du texte et la couleur d'accent, mais le choix d'apparence est désactivé et conserve `clair` comme valeur active. Les palettes sombres et les upgrades techniques existants ne sont pas supprimés : ils sont simplement non activables dans la baseline Vanilla.

Les listes, AUI, champs de saisie et boutons continuent de consommer les rôles sémantiques existants. Les menus restent natifs wx ; avec le dark mode wxMSW désactivé, ils restent sur le rendu clair. La lisibilité visuelle finale de ces composants doit être confirmée pendant la nouvelle recette humaine Windows, y compris lorsque Windows lui-même est configuré en mode sombre.

## Invariants hors périmètre

- aucune modification de logique métier ;
- aucune modification du chargement des données ;
- aucune modification de schéma de base de données ;
- aucun changement de format de données ;
- aucun changement de protocole ou de comportement Connecthys ;
- compatibilité avec le Connecthys d'Ivan conservée par non-modification de ces interfaces ;
- aucun revert global des commits UI ;
- thème clair actuel et upgrades techniques conservés.

## Validation attendue

Les contrats automatisés doivent vérifier l'affichage direct de `listView.donnees`, l'absence du contrôle/méthode « Voir tout », la conservation du chargement métier existant, le verrouillage de l'apparence claire et le routage sémantique clair des principaux widgets.

Après CI et packaging Windows verts, une nouvelle recette humaine doit confirmer sur Windows réel : liste complète immédiatement visible, recherche/actions inchangées, thème clair même lorsque Windows est sombre, lisibilité des listes/AUI/champs/boutons/menus, puis les contrôles métier/backup-restauration déjà prévus sur une copie réelle de base.
