# Audit CI Windows — Noethys

## État initial du dépôt (avant cette PR)

| Élément | Constat |
|---|---|
| Workflows GitHub Actions | **Aucun** — dossier `.github/` inexistant |
| Version Python supportée | **Python 3** (installation Linux : `python3`). Utilise `six` pour la compat 2/3 historique |
| wxPython | **wxPython 4.x** requis (Python 3 uniquement) |
| Fichier de dépendances | `requirements.txt` (15 paquets, pas de version épinglée sauf `mysqlclient===`) |
| Tests automatisés | **Aucun** — pas de répertoire `tests/`, pas de `test_*.py` |
| Mode de lancement | `python3 noethys/Noethys.py` (application wxPython) |
| Mode de packaging | `setup.py` + `py2exe` (Windows, Python 2 — non porté en Python 3) |
| Fichier Windows-only | `noethys/Outils/C866CA3A*.py` : encodage `mbcs` (COM typelib SAPI, invalide hors Windows) |
| Répertoires tiers | `ObjectListView/` (Philip Piper) ; `Outils/` (wxScheduler, ultimatelistctrl, COM typelibs) |

---

## Méthodologie d'audit

Adaptée de **fr4nck/Teamworks-CCNS** (`scripts/audit_runtime_risks.py`) :
- détection par expressions régulières sur les lignes ;
- exclusion des répertoires tiers (`ObjectListView/`, `Outils/`) ;
- heuristique de garde `six.PY2` / `six.PY3` pour éviter les faux positifs ;
- seuils CI configurables par motif ;
- export JSON pour traçabilité historique.

Implémenté dans **`scripts/audit_runtime_patterns.py`**.

---

## Choix techniques

### Un seul workflow : `.github/workflows/ci.yml`

Deux jobs, pas de matrice :

1. **`compile`** (ubuntu-latest) — compilation syntaxique + audit runtime.
2. **`windows-smoke`** (windows-latest) — validation Windows ciblée.

### Routage par chemins (`paths:`)

| Chemin modifié | `compile` | `windows-smoke` |
|---|---|---|
| `docs/` seul ou `*.md` seul | ✗ | ✗ |
| `noethys/**` | ✓ | ✓ |
| `requirements.txt` / `setup.py` | ✓ | ✓ |
| `tests/**` | ✓ | ✓ |
| `scripts/**` | ✓ | ✓ |
| `.github/workflows/**` | ✓ | ✓ |

### Version Python : 3.10

wxPython 4.2.x installable via `pip install wxPython` sur Windows pour Python 3.8–3.12.
Python 3.10 est choisi comme version stable, bien supportée.

### Dépendances minimales installées (job Windows uniquement)

`six`, `appdirs`, `python-dateutil`, `pytz`, `wxPython` — suffisant pour les smoke tests.

---

## Résultats de l'audit runtime (`scripts/audit_runtime_patterns.py`)

| Motif | Occurrences | Statut CI | Description |
|---|---|---|---|
| `RESULT_UNGUARDED` | 62 | ⚠️ informatif | `DB.ResultatReq()[N]` sans vérification de longueur préalable |
| `RESULT_ASSIGN` | 59 | ⚠️ informatif | `liste = ResultatReq()` suivi de `liste[N]` sans garde `len/if` |
| `DB_UNCLOSED` | 15 | ⚠️ informatif | `GestionDB.DB()` ouvert sans `DB.Close()` explicite |
| `BARE_EXCEPT` | 601 | ⚠️ informatif | `except:` sans type d'exception |
| `PY2_BUILTINS` | **0** | ✅ **PASS** | Appels `unicode()`, `basestring()`, `raw_input()` non gardés |
| `UNSAFE_EXEC` | 58 | ⚠️ informatif | `eval()` ou `exec()` |
| `INVALID_ESCAPE` | 10 | ⚠️ informatif | Séquences d'échappement invalides (`\c`, `\.`, `\i`, …) |
| `ENCODING_MBCS` | 0 | ✅ **PASS** | Fichiers `mbcs` exclus (répertoire tiers `Outils/`) |

**Seuil CI actif** : `PY2_BUILTINS > 0` → exit(1). Tous les autres motifs sont informatifs.

---

## Défauts confirmés et corrigés dans cette PR

| Défaut | Fichier | Ligne | Correction |
|---|---|---|---|
| `unicode(valeur)` non gardé — crash Python 3 | `Ctrl/CTRL_Synthese_deductions.py` | 422 | `str(valeur)` |
| `unicode(_(u"..."))` non gardé — crash Python 3 | `Dlg/DLG_Saisie_utilisateur_reseau.py` | 262 | suppression du wrap `unicode()` inutile |
| `DB.Close()` manquant après commit | `Utils/UTILS_Procedures.py` | A8967() | ajout de `DB.Close()` en fin de fonction |
| Encodage `mbcs` invalide sur Linux | `noethys/Outils/C866CA3A*.py` | — | exclusion via `-x 'C866CA3A'` dans le job Linux |
| Permissions `GITHUB_TOKEN` non restreintes | `.github/workflows/ci.yml` | — | `permissions: contents: read` |

---

## Faux positifs identifiés et exclus

| Pattern | Faux positif | Raison |
|---|---|---|
| `\blong\b` → PY2_BUILTINS | Variable GPS `lat, long = ...` ; mot français "long" dans chaînes | Retiré du détecteur |
| `\bunicode\b` en texte | `type_donnee = "unicode"`, docstrings, commentaires | Détecteur restreint aux appels `unicode(` |
| `unicode(reponse)` L.1429 | Dans `else:` après `if six.PY3:` — Python 2 uniquement | Heuristique `_is_in_py2_only_block` corrigée |
| `xrange(...)` dans `Outils/` | `from six.moves import range as xrange` — compat intentionnelle | Répertoire tiers exclu |
| `self.ctrl.raw_input(...)` | Méthode de `py.shell.Shell`, pas le builtin Python 2 | Détecteur vérifie l'absence de `.` avant `raw_input` |
| `ObjectListView/`, `Outils/` | Code tiers (Philip Piper, wxScheduler, COM typelibs) | Exclus via `THIRD_PARTY_DIRS` |

---

## Risques restants à confirmer (recette Windows manuelle ou PR dédiée)

| Risque | Motif | Occurrences | Priorité |
|---|---|---|---|
| `ResultatReq()[0]` sans garde `len()` | `RESULT_UNGUARDED` | 62 | Médium — crash si SELECT retourne 0 ligne |
| `liste = ResultatReq()` puis `liste[0]` sans garde | `RESULT_ASSIGN` | 59 | Médium — même risque |
| `DB.Close()` manquant dans 15 fonctions | `DB_UNCLOSED` | 15 | Faible — fuites de connexions SQLite (gérées par GC) |
| Séquences `\c`, `\i`, `\.` dans chaînes regex | `INVALID_ESCAPE` | 10 | Faible — SyntaxWarning, non bloquant |
| `eval()`/`exec()` | `UNSAFE_EXEC` | 58 | À auditer (console SQL, templates) |
| `except:` sans type | `BARE_EXCEPT` | 601 | Masquage silencieux d'erreurs |

---

## Limites nécessitant une recette Windows réelle

| Limite | Raison |
|---|---|
| Modules wxPython (dialogues, contrôles) | Nécessitent un affichage réel |
| Base de données SQLite/MySQL | Requiert un fichier `.db` ou un serveur MySQL |
| Packaging Windows (`py2exe`) | `setup.py` en syntaxe Python 2 — non porté en Python 3 |
| Modules COM (pyttsx, SAPI) | Enregistrement COM requis — non testable en CI sandboxé |
| Import complet de `Noethys.py` | Chaîne d'imports complète, requiert wx + tous modules |
| Impression / PDF | `reportlab`, `matplotlib` non installés dans les smoke tests |

---

## Prochaines étapes suggérées

1. **RESULT_UNGUARDED** : ajouter des gardes `if len(result) > 0:` au fil des PR métier.
2. **DB_UNCLOSED** : ajouter `DB.Close()` dans les 15 fonctions identifiées (PR dédiée).
3. **INVALID_ESCAPE** : convertir les chaînes concernées en raw strings `r"..."`.
4. **Tests fonctionnels** : créer une suite pytest pour les modules purs Python.
5. **Packaging Python 3** : migrer `setup.py` de `py2exe` vers PyInstaller.


---

Appliquer au nettoyage UI/wxPython de Noethys exactement la même méthode que sur Teamworks-CCNS.

Objectif : éliminer les fenêtres vides, freezes à l’ouverture, dialogues partiellement construits, assertions wxPython et erreurs de layout sans masquer les problèmes.

Règles de travail :

1. Ne pas ajouter de surcouche pour contourner un bug wxPython.
2. Ne jamais utiliser WXSUPPRESS_SIZER_FLAGS_CHECK ou équivalent pour faire disparaître une assertion.
3. Corriger les erreurs à la source, en conservant la logique métier existante.
4. Distinguer clairement :
    * le parent visuel wxPython, utilisé pour construire le contrôle ;
    * le contrôleur métier, qui possède les méthodes et boutons utilisés par ce contrôle.
5. Ne pas supposer que self.parent est le contrôleur métier. Les contrôles inclus dans un Panel, Section, StaticBox, ScrolledWindow, etc. doivent recevoir explicitement leur contrôleur si nécessaire.
6. Vérifier systématiquement l’ordre d’initialisation : un contrôle ne doit pas appeler MAJ(), Refresh(), MAJListeCtrl() ou équivalent avant que les boutons, attributs et dépendances qu’il utilise aient été créés.
7. Traiter les bugs par famille. Lorsqu’un pattern fautif est découvert dans un dialogue, scanner le dépôt pour rechercher toutes les occurrences similaires avant de relancer la CI.
8. Nettoyer les combinaisons de flags wxPython incompatibles, notamment les alignements horizontaux combinés inutilement à wx.EXPAND.
9. Ne pas considérer qu’un dialogue fonctionne simplement parce que son constructeur ne lève pas d’exception.

Garde-fous à ajouter ou conserver dans les smokes Windows :

* ouvrir réellement chaque dialogue structurant ;
* appeler Show(), Layout() et laisser tourner la boucle wx (wx.Yield() ou équivalent adapté) ;
* vérifier que la fenêtre possède une taille non nulle ;
* vérifier que ses contrôles descendants ont réellement été construits ;
* vérifier qu’au moins un contrôle est visible et dimensionné ;
* pour les Notebook / Treebook, parcourir toutes les pages et vérifier leur contenu ;
* détruire proprement chaque dialogue après le test ;
* utiliser un timeout global afin qu’un freeze transforme automatiquement la CI en échec ;
* tester particulièrement Préférences, Paramétrage, fiches individuelles, contrats, recrutement, présences et autres dialogues utilisés régulièrement.

Règle CI :

Une fenêtre qui s’ouvre vide, reste bloquée, ne construit pas son contenu ou déclenche une assertion wxPython doit rendre la CI rouge.

La CI ne doit pas seulement vérifier que Python démarre : elle doit construire réellement les interfaces critiques.

Méthode de correction :

* reproduire l’erreur ;
* identifier la cause structurelle ;
* rechercher les autres occurrences du même pattern ;
* corriger tout le lot cohérent ;
* vérifier le diff pour éviter toute modification métier parasite ;
* relancer les parcours critiques Windows ;
* continuer jusqu’à obtenir un run entièrement vert.

Exemple typique déjà rencontré :

contenu = self.section.GetContentPanel()
self.listCtrl = ListCtrl(contenu)

si ListCtrl utilise ensuite :

self.parent.bouton_modifier
self.parent.Modifier()

alors self.parent désigne contenu, pas le Panel métier.

Correction attendue :

self.listCtrl = ListCtrl(contenu, controller=self)

puis :

class ListCtrl(wx.ListCtrl):
    def __init__(self, parent, controller):
        super().__init__(parent, ...)
        self.controller = controller

et utiliser :

self.controller.bouton_modifier
self.controller.Modifier()

plutôt que détourner artificiellement le parent wx.

Priorité générale : code wxPython propre, déterministe et testable, sans masquer les warnings ou assertions. Le nettoyage graphique ne doit jamais casser la construction fonctionnelle des fenêtres.

C’est essentiellement le protocole qui nous a permis de faire passer Teamworks d’une suite de fenêtres cassées à un parcours Windows entièrement vert.
