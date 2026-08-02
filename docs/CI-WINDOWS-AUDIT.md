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


