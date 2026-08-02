# Audit CI Windows — Noethys

## État initial du dépôt (avant cette PR)

| Élément | Constat |
|---|---|
| Workflows GitHub Actions | **Aucun** — dossier `.github/` inexistant |
| Version Python supportée | **Python 3** (installation Linux : `python3`). Le code utilise `six` pour la compat 2/3 historique, mais Python 2 n'est plus maintenu dans ce projet |
| wxPython | **wxPython 4.x** requis (Python 3 uniquement) |
| Fichier de dépendances | `requirements.txt` (15 paquets, pas de version épinglée sauf `mysqlclient===`) |
| Tests automatisés | **Aucun** — pas de répertoire `tests/`, pas de `test_*.py` |
| Mode de lancement | `python3 noethys/Noethys.py` (application wxPython) |
| Mode de packaging | `setup.py` + `py2exe` (Windows, Python 2 — non porté en Python 3) |
| Fichier Windows-only | `noethys/Outils/C866CA3A*.py` : encodage `mbcs` (COM typelib SAPI, invalide hors Windows) |

---

## Choix techniques

### Un seul workflow : `.github/workflows/ci.yml`

Pas de duplication Linux/Windows, pas de matrice. Deux jobs distincts :

1. **`compile`** (ubuntu-latest) — vérification syntaxique rapide, sans dépendances lourdes.
2. **`windows-smoke`** (windows-latest) — validation Windows ciblée.

### Routage par chemins (`paths:`)

Le workflow ne se déclenche que si l'un des fichiers suivants change :

| Chemin | Raison |
|---|---|
| `noethys/**` | Code source de l'application |
| `requirements.txt` | Dépendances |
| `setup.py` | Configuration de packaging |
| `tests/**` | Scripts de smoke test |
| `.github/workflows/**` | Le workflow lui-même |

**Effet** : un commit qui modifie uniquement `docs/` ou un `*.md` ne déclenche **aucun** job Python ni Windows.

### Version Python : 3.10

wxPython 4.2.x est installable via `pip install wxPython` sur Windows pour Python 3.8 à 3.12.
Python 3.10 est choisi comme version stable, bien supportée par pip et wxPython.

### Dépendances minimales installées dans le job Windows

| Paquet | Rôle |
|---|---|
| `six` | Compat 2/3 (135 fichiers l'utilisent) |
| `appdirs` | Chemins utilisateur (UTILS_Fichiers) |
| `python-dateutil` | Calculs de dates |
| `pytz` | Fuseaux horaires |
| `wxPython` | Framework GUI (test wx.App) |

Paquets **non installés** : numpy, reportlab, sqlalchemy, matplotlib, mysqlclient, etc. — non requis pour les smoke tests.

### Exclusion `C866CA3A*.py` sur Linux

Ce fichier (`noethys/Outils/C866CA3A-32F7-11D2-9602-00C04F8EE628x0x5x0.py`) est un COM typelib
Python 2 généré par `makepy.py` avec l'encodage `mbcs` (Windows Multibyte Character Set).
`mbcs` est une encoding valide sous Windows mais inexistante sur Linux/macOS.

**Solution** : `python -m compileall -q -x 'C866CA3A' noethys/` sur Linux uniquement.
Le job Windows compile sans exclusion.

---

## Jobs déclenchés selon les chemins

| Type de modification | `compile` | `windows-smoke` |
|---|---|---|
| Uniquement `docs/` ou `*.md` | ✗ non déclenché | ✗ non déclenché |
| `noethys/**/*.py` (code) | ✓ | ✓ |
| `requirements.txt` ou `setup.py` | ✓ | ✓ |
| `tests/**` | ✓ | ✓ |
| `.github/workflows/**` | ✓ | ✓ |

---

## Validations obtenues par le workflow

### Job `compile` (Linux)

- ✅ Compilation de tous les fichiers `.py` sous `noethys/` (sauf le typelib Windows)
- ✅ Détection des erreurs de syntaxe Python 3

### Job `windows-smoke`

- ✅ Compilation de **tous** les fichiers `.py` (y compris `C866CA3A*.py` qui requiert mbcs)
- ✅ Import de `Chemins` (setup des chemins internes)
- ✅ Import de `Utils.UTILS_Divers` et `Utils.UTILS_Decimal` (modules purs Python)
- ✅ Vérification de `FloatToDecimal(3.14) == "3.14"` (calcul décimal de base)
- ✅ Création et destruction d'un `wx.App(False)` sans affichage
- ✅ Version wxPython affichée dans les logs CI

---

## Limites nécessitant une recette Windows réelle

| Limite | Raison |
|---|---|
| Modules wxPython non testés | Les dialogues, contrôles et formulaires nécessitent un affichage et un écran réel |
| Base de données SQLite/MySQL | Non testée : requiert un fichier `.db` réel ou un serveur MySQL |
| Packaging Windows (`py2exe`) | `setup.py` utilise la syntaxe Python 2 (`print "..."`) — non portable en Python 3 sans refonte |
| Modules COM (pyttsx, SAPI) | Nécessitent l'enregistrement COM sur Windows : non testable en CI sandboxé |
| Modules optionnels | `mysqlclient`, `opencv-python`, `pystrich`, etc. — installables mais non exercés |
| Impression / PDF | `reportlab` et `matplotlib` requis pour les PDF — non installés dans ce lot |
| Import complet de `Noethys.py` | Chaîne d'imports chargée, requiert tous les modules et wx initialisé |

---

## Corrections de défauts CI identifiés

| Défaut | Fichier | Correction appliquée |
|---|---|---|
| Encodage `mbcs` invalide sur Linux | `noethys/Outils/C866CA3A*.py` | Exclusion via `-x 'C866CA3A'` dans le job Linux uniquement |
| Avertissements d'échappements invalides | Plusieurs fichiers (`\c`, `\i`, `\.`, etc.) | Non bloquants (SyntaxWarning, exit code 0) — non modifiés dans ce lot |

---

## Prochaines étapes possibles

1. **Tests fonctionnels** : créer une suite pytest pour les modules purs Python (calculs, dates, décimaux).
2. **Portage packaging** : migrer `setup.py` vers Python 3 (`print(...)`) ou vers PyInstaller.
3. **Correction échappements** : remplacer les chaînes `"temp\calendrier.txt"` par des raw strings.
4. **Import étendu** : une fois tous les modules disponibles, tester un import complet de l'arbre de modules avec `wx.App`.

