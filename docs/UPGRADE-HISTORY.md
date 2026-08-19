# Historique du chantier Upgrade Noethys

## Pourquoi ce document ?

Noethys est un logiciel ancien, vaste et fortement lié à des usages métier réels. Le chantier Upgrade Noethys a donc choisi une modernisation incrémentale plutôt qu'une réécriture.

Ce document conserve les décisions structurantes afin qu'une reprise future du projet ne réintroduise pas des choix déjà étudiés ou ne casse pas involontairement la compatibilité historique.

## Principes figés

### Compatibilité avant nouveauté

Le chantier vise d'abord à prolonger Noethys Desktop :

- mêmes bases existantes autant que possible ;
- mêmes configurations ;
- même logique métier ;
- pas de migration implicite ;
- retour arrière possible ;
- corrections ciblées plutôt que refactorisation globale.

### Base réelle protégée

Une CI verte ne justifie jamais un test directement sur l'unique base de production. Toute RC doit passer par une copie et le scénario Noe-030.

### Windows prioritaire, code source multi-plateforme

Windows est la cible de distribution prioritaire. Le code source reste toutefois qualifié sur macOS et Linux GTK3 afin d'éviter une dérive Windows-only inutile.

### Python 3.10 comme baseline

Python 3.10 est retenu comme baseline de production pour la première RC modernisée. Python 3.11 et 3.12 ont été qualifiés mais restent des cibles de requalification, pas une migration imposée.

### Bases MySQL/MariaDB historiques

Aucune migration de serveur n'est imposée dans le chantier de modernisation. Les changements SQL doivent rester conservateurs et compatibles avec les installations anciennes lorsque cela est raisonnablement possible.

## Audit des forks

Un audit du réseau de forks a montré que `fr4nck/Noethys` est le fork moderne le plus avancé du réseau examiné.

Les autres forks ont servi de sources d'idées et de checklists de régression, pas de branches à fusionner en bloc :

- `JurassicPork/Noethys` : plusieurs correctifs historiques utiles comme liste de vérification ;
- `fautpasycraindre/Noethys` : idées de packaging Python moderne, mais versions/dépendances trop agressives pour un cherry-pick global ;
- autres forks : généralement anciens ou très peu divergents.

Décision : importer les **idées démontrées utiles**, jamais les historiques complets sans audit.

## SQL strict et bases

Le premier bloc a audité les requêtes susceptibles d'échouer avec des modes SQL stricts.

### Règlements

`OL_Reglements` regroupait une sélection large par seul `IDreglement`. La correction a remplacé le `GROUP BY` permissif par une pré-agrégation de `ventilation`, conservant :

- une ligne par règlement ;
- l'ordre des colonnes attendu par `Track` ;
- la somme historique de ventilation ;
- la compatibilité avec les anciens serveurs.

Des tests reproduisent l'ancien et le nouveau résultat.

### Export comptable

Les `GROUP BY` historiques ont été audités et corrigés sans changer la sémantique des exports. Des tests protègent notamment les cas QuadraCOMPTA/Cerig concernés.

### Index et performances

L'audit a privilégié les mesures et les usages réels plutôt qu'une création massive d'index pouvant modifier le coût des écritures ou la compatibilité des bases.

## Qualification Python

### Python 3.11

Qualification fusionnée : `07a62df7`.

- cœur/audits Linux ;
- wxPython macOS ;
- dépendances Windows ;
- build PyInstaller complet Windows.

### Python 3.12

Étude fusionnée : `25e56c2b`.

La compatibilité a été démontrée sans modifier la baseline. Les workflows profonds 3.11/3.12 ont ensuite été passés en déclenchement manuel afin de garder une CI courante frugale.

## wxPython Phoenix et plateformes

### Noe-020 — Phoenix

Fusion : `de0dc583`.

Un audit runtime a distingué les anciens noms wxPython encore supportés des vraies incompatibilités. Il a trouvé un défaut concret :

```text
wx.SystemSettings_GetFont
```

remplacé par :

```text
wx.SystemSettings.GetFont
```

Décision : ne pas réécrire massivement les aliases historiques qui restent fonctionnels.

### Noe-021 — Linux GTK3

Fusion : `150c9ea9`.

La CI utilise Ubuntu, wxPython GTK3 et Xvfb pour tester :

- backend GTK ;
- API Phoenix ;
- cycle `wx.App` ;
- layout avec sizers et `UltimateListCtrl`.

### Noe-022 — macOS

Fusion : `d8d61a31`.

Le code source est qualifié automatiquement sur macOS avec un smoke de layout représentatif. Cette qualification n'est pas présentée comme un paquet macOS utilisateur signé/notarisé.

## Recette et non-régression

### Noe-030 — base existante

Outillage fusionné : `acedfa58`.

Le préflight :

- ouvre SQLite en lecture seule ;
- calcule SHA-256 avant/après ;
- produit un `schema_digest` ;
- ne sort pas de données nominatives ;
- dispose d'un mode MySQL/MariaDB conservateur.

L'issue reste ouverte jusqu'à la recette sur une copie de base réellement utilisée.

### Noe-031 — suite métier

Fusion : `e8e286a2`.

Tous les `tests/test_*.py` sont exécutés dans la CI principale. Le travail a également réduit le couplage de services PMSL à `GestionDB` lorsqu'une `FakeDB` est injectée.

Décision : un test métier doit vérifier un invariant observable, pas un détail d'implémentation.

## Sauvegarde et restauration

### Noe-032

Fusion : `f8cd03fe`.

L'audit a découvert plusieurs `return False` mal indentés dans `UTILS_Sauvegarde.Restauration`, rendant plusieurs chemins de restauration inconditionnellement défaillants.

La correction conserve les formats historiques et ajoute des tests de restauration SQLite et de flux MySQL simulé.

Décision : aucun changement de format de sauvegarde dans cette RC ; réparer d'abord la fiabilité du comportement existant.

## Packaging Windows

### Noe-040 — véritable artefact

Fusion : `4916ca15`.

Le premier smoke du véritable EXE a révélé un défaut important : PyInstaller 6 utilise par défaut un sous-dossier `_internal`, tandis que `Chemins.py` recherche historiquement les ressources à côté de `Noethys.exe`.

Correction :

```python
contents_directory="."
```

Le layout `onedir` plat est donc explicitement conservé.

Le workflow :

- construit le bundle ;
- contrôle les ressources ;
- crée l'archive ;
- la ré-extrait dans un dossier neuf ;
- retire Python externe du contexte ;
- lance réellement l'EXE ;
- vérifie les imports embarqués ;
- publie l'artefact.

Le runtime hook de smoke produit un marqueur de succès/erreur et utilise une sortie non interactive afin qu'un build `console=False` ne puisse pas bloquer la CI sur une boîte de dialogue invisible.

### Noe-041 — vrai mode portable

Fusion : `bcd8ca96`.

Le dossier `Portable/`, déjà reconnu historiquement par Noethys, est désormais livré explicitement dans l'archive Windows.

Les chemins sont isolés sous ce dossier et les sous-répertoires runtime sont créés à la demande. Les installations classiques sans marqueur `Portable/` conservent leur comportement.

Décision : réutiliser le mécanisme historique plutôt que créer un second système de configuration portable.

## Préparation RC

Préparation documentaire fusionnée : `7bb7121d`.

Toutes les portes automatisées critiques sont désormais considérées franchies. Les deux verrous restants avant une RC validée sont volontairement humains :

1. recette Noe-030 sur une copie de base réellement utilisée ;
2. validation visuelle et métier de l'interface Windows sur cette copie.

Tant que ces deux étapes ne sont pas réalisées, le dépôt peut produire un **candidat technique RC**, mais pas une RC déclarée validée.

## Choix explicitement reportés après la première RC

- installateur Windows système ;
- signature de code ;
- packaging utilisateur macOS ;
- packaging utilisateur Linux ;
- bascule baseline Python 3.11/3.12 ;
- migration obligatoire MySQL/MariaDB ;
- réécriture de l'architecture desktop ;
- interopérabilité approfondie Noethys Desktop / NoethysWeb.

Ces reports sont volontaires : ils réduisent le risque et permettent de stabiliser d'abord la modernisation compatible avec l'existant.
