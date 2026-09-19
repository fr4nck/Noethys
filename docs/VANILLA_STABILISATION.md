# Noethys Vanilla — état de stabilisation

> Mise à jour : **19 septembre 2026**.
>
> La ligne de distribution Vanilla a désormais sa propre branche de référence : `maintenance/vanilla`.
>
> Ce document, présent sur `master`, sert uniquement de vue de suivi. Pour l'état exécutable réel de Vanilla, la source de vérité est la branche `maintenance/vanilla`, ses tests et ses PR.

## État courant

Vanilla reste volontairement conservatrice : interface historique, données et configurations existantes préservées, correctifs ciblés de robustesse, packaging Windows maintenu et aucune refonte Qt dans cette ligne.

Le candidat fonctionnel consolidé est issu de la PR **#361 — “Vanilla — candidat consolidé #360 + #359”**, fusionnée dans `maintenance/vanilla` le 7 septembre 2026.

SHA intégré :

`f5d1f20a1c7642374b8b7766637d1f029b689d0b`

Il réunit :

- le correctif **#360** pour **Affichage** et **Liste d'attente** avec les valeurs DATE natives Python 3 ;
- le correctif **#359** de fermeture/réouverture de la liste détaillée des consommations ;
- les tests contractuels correspondants ;
- la qualification Windows du candidat consolidé.

La PR #359 a été fermée sans merge direct car son correctif a été repris dans #361.  
La PR #363 a été fermée sans merge car elle était devenue redondante après #361.

## Qualification automatisée de #361

Le SHA `f5d1f20…` a obtenu deux runs Windows verts :

- run **34157333714** — qualification installateur + portable ;
- run **34157333717** — portable Windows.

Artefacts produits :

- artifact **10031502121** — `Noethys-Vanilla-r2-Windows` ;
- artifact **10031462063** — `Noethys-Vanilla-Windows-portable`.

Cette réussite ne vaut pas recette métier humaine.

## Version suivante

La PR **#367 — “Vanilla 1.3.4.3 — aligner version, changelog et distribution”** prépare la première version Vanilla dont le numéro affiché dans le logiciel distingue explicitement la maintenance du dernier upstream public.

Version préparée :

**1.3.4.3**

Base upstream :

**1.3.4.2**

Le choix de `1.3.4.3`, plutôt qu'un suffixe `1.3.4.2-r3` dans le logiciel, est volontaire : le mécanisme historique de comparaison des versions de Noethys attend des composants numériques séparés par des points.

Sur la branche Vanilla, `noethys/Versions.txt` est à la fois :

- la source du numéro affiché dans la fenêtre principale ;
- la source lue par `FonctionsPerso.GetVersionLogiciel()` ;
- le contenu de **A propos > Notes de versions** ;
- une ressource incluse dans les paquets Windows.

La PR #367 aligne également l'AppVersion Inno Setup, le BUILD-INFO, les noms d'artefacts, les notes de release et un test contractuel.

Tant que #367 n'est pas fusionnée, **1.3.4.3 reste une version préparée et non une release publiée**.

## Releases Vanilla déjà publiées

Le 27 août 2026 :

- `vanilla-1.3.4.2-r1` — première release maintenue ;
- `vanilla-1.3.4.2-r2` — clôture du premier lot bugfix, installateur Windows et portable.

Ces deux releases conservaient le numéro applicatif upstream 1.3.4.2.

## Recette humaine encore requise

Avant de déclarer la prochaine Vanilla stable :

1. ouvrir la liste détaillée des consommations ;
2. fermer pendant ou juste après le chargement ;
3. rouvrir immédiatement et répéter plusieurs fois ;
4. refaire par la croix Windows ;
5. vérifier l'absence d'Application Error 1000 / `0xc0000005` ;
6. vérifier **Affichage** dans le tableau de remplissage ;
7. vérifier **Liste d'attente** depuis la toolbar et le menu ;
8. contrôler Capacité / Occupé / Disponible / Attente ;
9. fermer complètement puis relancer Noethys ;
10. vérifier les impressions/exports réellement utilisés sur une copie de base.

Aucune validation humaine n'est déduite automatiquement de la CI.

## Frontière avec `master`

Le `master` poursuit la modernisation technique du fork. Il ne doit plus être confondu avec la ligne de distribution Vanilla.

- `maintenance/vanilla` : maintenance conservatrice et releases Vanilla ;
- `master` : évolution générale du fork ;
- future branche Qt : refonte graphique séparée lorsqu'elle sera réellement engagée.

Les correctifs doivent être portés d'une ligne à l'autre explicitement lorsqu'ils sont pertinents ; aucun merge massif de `master` vers Vanilla n'est prévu.

## Garde-fous

- pas de migration implicite ou destructive pour finaliser Vanilla ;
- pas de modification du protocole Connecthys/Ivan sans chantier séparé ;
- pas de refonte Qt dans `maintenance/vanilla` ;
- recette sur copie de base, jamais sur l'unique production ;
- une CI verte ne remplace pas la recette métier ;
- une release Vanilla doit être construite sur le SHA exact finalement validé.
