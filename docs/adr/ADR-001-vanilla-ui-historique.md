# ADR-001 — Vanilla conserve l'ergonomie Noethys et réserve la refonte à Qt

**Statut : ACCEPTED**

## Contexte

La modernisation graphique introduite dans Vanilla a modifié sensiblement l'apparence et certains comportements d'interface historiques de Noethys. La recette humaine du 07/09/2026 a notamment rejeté le thème sombre comme baseline et l'étape intermédiaire « Voir tout » qui remplaçait l'affichage direct d'une liste utile.

La suite de la recette a retenu le thème clair actuel, mais a également montré qu'une modernisation de contrôle ne peut être acceptée si des commandes historiques deviennent inopérantes. Vanilla doit rester une référence wxPython fiable avant la future branche Qt.

## Décision

Vanilla reste la référence fonctionnelle et ergonomique fidèle à Noethys historique :

- interface claire ;
- suivi automatique du thème système désactivé pour Vanilla ;
- rendu sombre wxPython temporairement non supporté ;
- organisation générale des écrans conservée ;
- listes utiles visibles directement ;
- commandes et actions historiques directement opérantes ;
- améliorations techniques modernes Python 3, wxPython, runtime, imports, tests, packaging et stabilité conservées.

La refonte graphique profonde, les thèmes clair/sombre modernes et les évolutions structurelles de l'interface seront réalisées ultérieurement dans la branche **Qt**, séparément de Vanilla.

## Conséquences

- les évolutions graphiques Repens/Material/sombre incompatibles avec cette décision sont neutralisées ou retirées de Vanilla uniquement lorsqu'elles changent l'ergonomie retenue ;
- les correctifs techniques introduits pendant ces travaux restent conservés ;
- aucune modernisation visuelle ne doit modifier la logique métier, le chargement des données ou les actions disponibles ;
- les futures évolutions UI importantes ne devront plus être introduites directement dans Vanilla ;
- aucune décision UI Vanilla ne justifie une migration BDD, un changement de schéma ou de format, ni un changement du protocole ou du comportement Connecthys/Ivan.

La validation automatisée reste nécessaire mais ne remplace pas la recette humaine Windows pour les parcours interactifs.
