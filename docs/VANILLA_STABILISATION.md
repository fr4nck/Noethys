# Stabilisation Vanilla — décisions et recettes

## Statut

**VALIDATION MANUELLE REQUISE** — ne pas taguer ni déclarer Vanilla stable avant une nouvelle recette humaine Windows du prochain candidat.

Vanilla reste la baseline wxPython techniquement durcie et fonctionnellement compatible avec Noethys historique. Les évolutions graphiques profondes sont réservées à la future branche Qt.

## Chronologie et candidats

### Candidat `74d25fdd8431eb7a167ab35cab8e1e8aa4e3bdc9`

Ce candidat était **techniquement suffisamment abouti pour recette humaine** : Python 3 / wxPython, audits runtime, sauvegarde-restauration, CI et packaging Windows avaient atteint le niveau attendu pour ouvrir la recette réelle.

Qualifications automatisées acquises :

- CI `#2389`, run `34114566920` : succès ; **761 tests OK** ; contrôle de schéma sans modification SQL applicative ;
- packaging Windows exact, run `34114567033` : succès ;
- installateur `Noethys-Windows-installer`, artifact `10015844325`, SHA-256 `2a3d58c16b7381f0694d02dcc3beb9a2a6df9bd7901651cb11925ed994920f94` ;
- portable `Noethys-Windows-portable`, artifact `10015847439`, SHA-256 `6175ada64c72a454ed54bcf8b38eb6422d667cf6e1c999a1b67ef3335f3f308c`.

**Rejeté graphiquement lors de la recette humaine du 07/09/2026.** Motifs initiaux : thème sombre actuel non retenu et ergonomie de certaines listes avec étape « Voir tout » non retenue. Ce rejet **ne concernait pas l'ensemble des améliorations techniques** du candidat, qui devaient être conservées.

La décision UX a ensuite été affinée pendant la même recette : le **thème clair actuel est retenu**, le suivi automatique du thème système est désactivé pour Vanilla, et le rendu sombre wxPython reste temporairement non supporté.

### Candidat `f777c6cf4d9208d2e756271dfad95a7a7027acdd`

Issu de la PR `#358`, ce candidat a supprimé l'étape « Voir tout » de la recherche d'accueil et verrouillé Vanilla en thème clair, sans changement métier, BDD ou Connecthys.

Qualifications automatisées :

- CI master `#2392`, run `34139688567` : succès ; **771 tests OK** ; imports, AUI, layout et cycle de vie wx verts ; contrôle push : « Aucune modification du schéma applicatif SQL ajoutée. » ;
- packaging Windows exact, run `34139688552` : succès ;
- installateur `Noethys-Windows-installer`, artifact `10025520253`, SHA-256 `360afb57744bd685257f45d2effd2c6df1cb4ea9c2dfc03e79fc0af7ac6ec7fd` ;
- portable `Noethys-Windows-portable`, artifact `10025523339`, SHA-256 `df83a632bba6387777cc81955308ce5dda38f2d68f8ed6a94d8ced441f10267a` ;
- smoke installable : mise à niveau sans perte de configuration, succès ;
- smoke portable : lancement après extraction sans environnement Python externe, succès.

La recette humaine suivante a toutefois révélé des **P1 runtime/UI** non couverts par ces tests :

- bouton **Affichage** du tableau de fréquentation inopérant ;
- bouton **Liste d'attente** inopérant ;
- disparition brutale du processus observée en fin de vidéo de recette. La nouvelle recette devra confirmer si ce dernier symptôme est entièrement résolu par le correctif des parcours concernés ; il n'est pas déclaré résolu par simple déduction.

Le candidat `f777c6cf4d9208d2e756271dfad95a7a7027acdd` reste donc **non validé pour une baseline stable** malgré ses qualifications automatisées réussies.

### Correctif suivant

Branche : `fix/vanilla-remplissage-dialogs`, créée depuis exactement `f777c6cf4d9208d2e756271dfad95a7a7027acdd`.

L'analyse des deux commandes a isolé un point commun reproductible : `DLG_Parametres_remplissage` et `DLG_Attente` construisent tous les deux `CTRL_Grille_periode.CTRL`. La page `Vacances` de ce contrôle est initialisée immédiatement et convertissait encore les champs SQL `date_debut` / `date_fin` par découpage de chaîne (`date[:10]`). Les pilotes Python 3/MySQL peuvent déjà fournir des objets `datetime.date`, qui ne sont pas indexables et provoquent alors une exception avant `ShowModal()`.

La liste d'attente contenait en plus une conversion locale équivalente pour `consommations.date` et `date_saisie`.

Décision de correction : réutiliser `Utils.UTILS_Dates.DateEngEnDateDD`, déjà prévu pour les chaînes historiques et les dates Python natives, avec prise en charge explicite d'un éventuel `datetime.datetime` dans la liste d'attente. **Les requêtes, le chargement, les actions et les structures de données restent inchangés.**

Le SHA exact du nouveau candidat sera celui du master après intégration verte de cette correction et sera communiqué avec l'artefact Windows correspondant ; il ne sera pas tagué stable avant recette humaine.

## Décisions UX Vanilla

- **Thème sombre rejeté en recette humaine.**
- **Thème clair retenu** pour Vanilla.
- **Comportement « Voir tout » rejeté** sur la recherche individus/familles de l'accueil.
- **Décision : retour à l'affichage direct de la liste complète** quand aucun texte de recherche n'est saisi.
- **Suivi automatique du thème système désactivé pour Vanilla.**
- **Thème sombre wxPython / widgets wx temporairement non supporté** tant qu'un rendu sombre cohérent n'a pas été conçu et validé.
- Les commandes historiques doivent rester directement opérantes ; une modernisation visuelle ne doit pas interposer ou neutraliser leur comportement.

## Périmètre technique des corrections UX

### Liste d'accueil

Le composant concerné est `noethys/Ctrl/CTRL_Recherche_individus.py`, dans `BarreRechercheAccueil.Recherche` et l'ancien bouton `ctrl_voir_tout` du `Panel`.

Avant correction, une recherche vide vidait les objets affichés et basculait vers un état d'attente ; le bouton « Voir tout » réinjectait ensuite `listView.donnees`. La stabilisation supprime cette étape intermédiaire : une recherche vide affiche directement `listView.donnees`.

Le chargement reste exclusivement assuré par `ctrl_listview.MAJ(forceActualisation=True)` dans `Panel.MAJ`. La recherche, ses critères, sa limite de résultats, les actions disponibles et la logique métier ne sont pas modifiés.

### Thème clair Vanilla

La préférence active `interface_apparence` est forcée à `clair` par la couche de configuration UI. Sur Windows, l'option wxMSW `msw.dark-mode` est explicitement positionnée à `0` avant la création de `wx.App`, afin que le rendu natif wx ne suive pas le mode sombre Windows.

Le dialogue d'apparence reste présent pour l'échelle, la taille du texte et la couleur d'accent, mais le choix d'apparence est désactivé et conserve `clair` comme valeur active. Les palettes sombres et les upgrades techniques existants ne sont pas supprimés : ils sont simplement non activables dans la baseline Vanilla.

Les listes, AUI, champs de saisie et boutons continuent de consommer les rôles sémantiques existants. Les menus restent natifs wx ; avec le dark mode wxMSW désactivé, ils restent sur le rendu clair.

### Affichage et liste d'attente du tableau de fréquentation

Le correctif P1 ne modifie pas la logique de la toolbar Repens. Les événements restent reliés à `OnParametres` et `OnListeAttente`, qui ouvrent les mêmes dialogues historiques. Seule la conversion des valeurs DATE renvoyées par le pilote Python 3 est sécurisée dans :

- `noethys/Ctrl/CTRL_Grille_periode.py` ;
- `noethys/Ctrl/CTRL_Attente.py`.

## Invariants hors périmètre

- aucune modification de logique métier ;
- aucune modification du chargement des données ;
- aucune migration ni modification de schéma de base de données ;
- aucun changement de format de données ;
- aucun changement de protocole ou de comportement Connecthys / Ivan ;
- aucun changement des requêtes métier de remplissage ou de liste d'attente ;
- aucun revert global des commits UI ;
- thème clair actuel et upgrades Python 3, wxPython, runtime, imports, packaging, sauvegarde-restauration et stabilité conservés.

## Validation attendue

Les contrats automatisés doivent vérifier :

- l'affichage direct de `listView.donnees` et l'absence de l'étape « Voir tout » ;
- le verrouillage de l'apparence claire ;
- la conservation du câblage des boutons **Affichage** et **Liste d'attente** ;
- l'acceptation des valeurs SQL DATE sous forme historique chaîne et sous forme Python native ;
- l'absence de changement des requêtes de ces parcours.

Après CI et packaging Windows verts, une nouvelle recette humaine doit confirmer sur Windows réel :

1. **Affichage** ouvre bien les paramètres et permet de les valider ;
2. **Liste d'attente** ouvre bien la liste et reste utilisable ;
3. les quatre modes Capacité / Occupé / Disponible / Attente restent fonctionnels ;
4. le parcours filmé jusqu'à la fin ne fait plus disparaître Noethys ;
5. liste complète d'accueil, thème clair forcé et autres acquis de `f777c6cf…` restent inchangés.
