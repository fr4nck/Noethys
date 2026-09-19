# Stabilisation Noethys Vanilla

> Mise à jour : **19 septembre 2026**.
>
> Branche de référence : `maintenance/vanilla`.
>
> Version applicative préparée : **1.3.4.3**, basée sur Noethys upstream **1.3.4.2**.
>
> Statut : **candidat qualifié automatiquement, validation humaine Windows encore requise avant déclaration “stable”**.

## 1. Source de vérité

La ligne Vanilla est maintenue séparément du `master` modernisé. Elle conserve l'interface historique et le modèle de données existant.

Ordre de confiance pour Vanilla :

1. code et tests de `maintenance/vanilla` ;
2. pull requests et commits intégrés sur cette branche ;
3. ce document de stabilisation ;
4. l'audit historique `docs/VANILLA_UI_COMMAND_AUDIT.md`.

Le changelog visible dans le logiciel et le numéro de version affiché sont dérivés de `noethys/Versions.txt`. Pour la version préparée ici, sa première ligne est `Version 1.3.4.3 (19/09/2026)`.

## 2. Baseline et releases précédentes

Snapshot upstream de référence :

`630ef4373dbc05dae1cbc597b9baccb1178e64e4`

Ce snapshot correspond à Noethys upstream **1.3.4.2**.

Deux releases de maintenance ont déjà été publiées le 27 août 2026 :

- `vanilla-1.3.4.2-r1` — première release maintenue Vanilla+ ;
- `vanilla-1.3.4.2-r2` — clôture du premier lot bugfix et ajout de l'installateur Windows.

Ces releases conservaient volontairement `1.3.4.2` comme version applicative interne. La version **1.3.4.3** devient la première version Vanilla dont le numéro visible dans le logiciel distingue explicitement la ligne maintenue du dernier upstream 1.3.4.2.

## 3. Candidat consolidé du 7 septembre 2026

La PR **#361 — “Vanilla — candidat consolidé #360 + #359”** a été fusionnée dans `maintenance/vanilla` le 7 septembre 2026.

SHA candidat fonctionnel :

`f5d1f20a1c7642374b8b7766637d1f029b689d0b`

Elle consolide exclusivement :

- le backport du correctif **#360** sur les commandes **Affichage** et **Liste d'attente**, pour accepter les dates SQL natives Python 3 ;
- le correctif **#359** de fermeture/réouverture de la liste détaillée des consommations ;
- les tests contractuels ciblés de ces deux correctifs ;
- l'extension de la qualification Windows aux fichiers concernés.

La PR **#359** elle-même a été fermée sans merge direct sur sa branche d'origine : son correctif a été intégré dans #361.  
La PR **#363** a été fermée sans merge car elle était devenue redondante après l'intégration de #361.

## 4. Qualification automatisée du SHA `f5d1f20…`

Deux workflows Windows ont terminé avec succès sur le SHA exact :

- run **34157333714** — `Vanilla r2 - portable et installateur` : succès ;
- run **34157333717** — `Vanilla Windows portable` : succès.

Les artefacts correspondants ont été produits :

- `Noethys-Vanilla-r2-Windows` — artifact **10031502121** ;
- `Noethys-Vanilla-Windows-portable` — artifact **10031462063**.

La qualification automatisée couvre notamment :

- compilation Python ;
- tests contractuels Vanilla ;
- import et cycle minimal wxPython sous Windows ;
- build PyInstaller ;
- vérification du payload ;
- création de l'installateur Inno Setup ;
- installation silencieuse ;
- lancement de `Noethys.exe` ;
- conservation de la configuration utilisateur ;
- fabrication du portable.

Cette qualification ne remplace pas les parcours métier interactifs sur une copie réelle de base.

## 5. Correctifs consolidés depuis upstream 1.3.4.2

La version 1.3.4.3 regroupe les correctifs Vanilla accumulés depuis le snapshot upstream, notamment :

- robustesse des titulaires de familles rattachées ;
- filtrage iCalendar et gestion des événements incomplets ;
- repli sur format PES inconnu et sécurisation de la saisie PES ;
- élimination d'états mutables partagés dans plusieurs contrôles ;
- corrections de noms non définis et défauts runtime ciblés ;
- corrections Python 3 / wxPython dans les listes, synthèses, badgeage, transports, trésorerie, reçus et préférences ;
- fiabilisation de l'administration et de la synchronisation Connecthys sans migration de protocole ou de schéma ;
- respect de l'annulation dans la recherche de date de l'agenda ;
- nettoyage garanti des temporaires de sauvegarde/restauration MySQL ;
- sécurisation de la configuration Connecthys ;
- corrections de cycle de vie des dialogues et de plusieurs use-after-destroy ;
- isolation des fichiers temporaires par processus ;
- protection de parcours facturation/règlement sur données supprimées ou incomplètes ;
- stabilisation du splash de démarrage ;
- rapports de crash locaux et destinataire configurable ;
- correction de l'assistant CAF-CDAP sous Python 3 ;
- compatibilités historiques d'impression/aperçu sous wxPython Phoenix ;
- libération explicite de la base temporaire Connecthys sous Windows ;
- correction des commandes Affichage / Liste d'attente avec dates natives Python 3 ;
- correction du crash natif de fermeture/réouverture de la liste détaillée des consommations.

Le changelog utilisateur correspondant est maintenu dans `noethys/Versions.txt`.

## 6. Décisions de périmètre

Vanilla reste volontairement conservatrice :

- aucune migration implicite ou destructive de base de données ;
- aucun changement de protocole ou de format Connecthys/Ivan pour finaliser cette version ;
- aucune refonte Qt ;
- aucune refonte graphique générale ;
- conservation de l'interface historique ;
- corrections locales et démontrées ;
- conservation des configurations et données existantes autant que possible.

Le bouton **Modifier** de la liste détaillée des consommations, la performance du chargement global des questionnaires et les autres anomalies non nécessaires au lot consolidé restent hors du correctif #361 tant qu'elles ne sont pas isolées et qualifiées séparément.

## 7. Recette humaine encore nécessaire

Avant de déclarer 1.3.4.3 stable, rejouer au minimum sur Windows avec une copie de base réellement utilisée :

1. ouvrir la liste détaillée des consommations ;
2. fermer pendant ou immédiatement après le chargement ;
3. rouvrir immédiatement et répéter plusieurs fois ;
4. refaire le scénario avec la croix Windows ;
5. vérifier l'absence d'Application Error 1000 / `0xc0000005` ;
6. ouvrir **Affichage** dans le tableau de remplissage et valider les paramètres ;
7. ouvrir **Liste d'attente** depuis la toolbar et depuis le menu ;
8. vérifier Capacité / Occupé / Disponible / Attente ;
9. confirmer la fermeture complète puis la relance du logiciel ;
10. vérifier les parcours prioritaires d'impression/export réellement utilisés.

Aucune validation humaine n'est déduite de la seule réussite de la CI.

## 8. Version 1.3.4.3

La version 1.3.4.3 est choisie plutôt qu'un suffixe `-r3` dans `Versions.txt` pour conserver le contrat historique de comparaison numérique des versions dans Noethys.

Le logiciel lit son numéro via `FonctionsPerso.GetVersionLogiciel()`, qui extrait la première version de `Versions.txt`. Les comparaisons historiques découpent ensuite ce numéro sur les points et convertissent chaque composant en entier. Un suffixe comme `1.3.4.2-r3` casserait ce contrat ; `1.3.4.3` reste compatible sans modifier le mécanisme de mise à jour.

L'upstream public Noethys est toujours en **1.3.4.2** au 19 septembre 2026.

## 9. Distribution Windows

La distribution 1.3.4.3 doit conserver :

- un installateur Inno Setup ;
- un portable Windows ;
- le layout PyInstaller historique sans sous-dossier `_internal` ;
- `Versions.txt`, `Licence.txt`, `Icone.ico` et `Static/` dans le payload ;
- la configuration utilisateur lors d'une mise à niveau ;
- l'absence de dossier `Portable/` dans le Setup installable.

Les noms d'artefacts, le `BUILD-INFO.txt`, l'`AppVersion` Inno Setup et les notes de release doivent tous porter **1.3.4.3**.

## 10. Garde-fous de clôture

- Ne pas déclarer Vanilla stable avant la recette humaine Windows du candidat final.
- Ne jamais tester sur l'unique base de production.
- Ne pas mélanger Qt, Teamworks ou adaptations locales au lot de release.
- Ne pas introduire de migration BDD pour ce changement de version.
- Le bump de version et le changelog ne doivent modifier aucune logique métier.
- La release doit être construite sur le SHA exact finalement intégré à `maintenance/vanilla`.
