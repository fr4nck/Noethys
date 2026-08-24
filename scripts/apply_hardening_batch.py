#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Applique les corrections mécaniques de la passe globale de hardening.

Le script est volontairement étroit : aucun reformatage global, aucune
transformation SQL et aucune modification métier implicite.

Lots couverts :
- remplacer les ``except:`` nus du code Noethys de premier niveau par
  ``except Exception:`` afin de ne plus avaler ``SystemExit``,
  ``KeyboardInterrupt`` et les autres ``BaseException`` ;
- corriger le rafraîchissement de la recherche individus après lecture d'un
  code-barres famille ;
- sécuriser plusieurs chemins d'erreur réellement démontrés par les audits :
  démarrage Nomadhys avorté après échec d'écoute, avatars utilisateurs absents,
  liste d'anomalies de synchronisation, date de désinscription invalide et
  redémarrage du timer RFID après une exception survenue après son arrêt.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
EXCLUDED_PARTS = {"ObjectListView", "Outils"}


def iter_first_party_python():
    for path in NOETHYS.rglob("*.py"):
        try:
            relative = path.relative_to(NOETHYS)
        except ValueError:
            continue
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        yield path


def replace_bare_excepts(path: Path) -> int:
    source = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return 0

    bare_lines = sorted(
        {node.lineno for node in ast.walk(tree) if isinstance(node, ast.ExceptHandler) and node.type is None},
        reverse=True,
    )
    if not bare_lines:
        return 0

    lines = source.splitlines(keepends=True)
    changed = 0
    for lineno in bare_lines:
        index = lineno - 1
        line = lines[index]
        replaced, n = re.subn(r"\bexcept\s*:", "except Exception:", line, count=1)
        if n != 1:
            raise RuntimeError(f"Impossible de resserrer le except nu : {path}:{lineno}")
        lines[index] = replaced
        changed += 1

    new_source = "".join(lines)
    ast.parse(new_source)
    path.write_text(new_source, encoding="utf-8")
    return changed


def _replace_idempotent(relative: str, old: str, new: str, marker: str) -> bool:
    path = NOETHYS / relative
    source = path.read_text(encoding="utf-8")
    if old in source:
        source = source.replace(old, new, 1)
        ast.parse(source)
        path.write_text(source, encoding="utf-8")
        return True
    if marker in source:
        return False
    raise RuntimeError(f"Motif de hardening introuvable : {relative} / {marker}")


def fix_individual_barcode_refresh() -> bool:
    old = '''                    # MAJ du remplissage\n                    if self.GetGrandParent().GetName() == "general" :\n                        self.GetGrandParent().MAJ() \n                    else:\n                        self.MAJ() \n                    self.OnCancel(None)\n'''
    new = '''                    # Actualise le conteneur métier quand il expose MAJ,\n                    # sinon recharge directement la liste. BarreRecherche n'a\n                    # volontairement pas de méthode MAJ propre.\n                    actualiser = getattr(self.parent, "MAJ", None)\n                    if callable(actualiser):\n                        actualiser()\n                    else:\n                        self.listView.MAJ(forceActualisation=True)\n                    self.OnCancel(None)\n'''
    return _replace_idempotent(
        "Ol/OL_Individus.py", old, new,
        "self.listView.MAJ(forceActualisation=True)",
    )


def fix_nomad_server_abort() -> bool:
    old = '''    except Exception as err:\n        print(("Erreur lancement serveur Nomadhys :", err))\n        log.EcritLog(_(u"Erreur dans le lancement du serveur Nomadhys [factory] :") )\n        log.EcritLog(err)\n\n    try :\n'''
    new = '''    except Exception as err:\n        print(("Erreur lancement serveur Nomadhys :", err))\n        log.EcritLog(_(u"Erreur dans le lancement du serveur Nomadhys [factory] :") )\n        log.EcritLog(err)\n        # Sans socket d'écoute il ne faut ni annoncer un serveur prêt ni\n        # démarrer le reactor : l'ancien code pouvait aussi lire ``port``\n        # avant affectation si la préparation échouait plus tôt.\n        return\n\n    try :\n'''
    return _replace_idempotent(
        "Ctrl/CTRL_Serveur_nomade.py", old, new,
        "Sans socket d'écoute il ne faut ni annoncer un serveur prêt",
    )


def fix_user_avatar_default() -> bool:
    old = '''    # chargement avatars\n    try :\n        req = """SELECT IDutilisateur, image\n'''
    new = '''    # chargement avatars\n    listeAvatars = []\n    try :\n        req = """SELECT IDutilisateur, image\n'''
    return _replace_idempotent(
        "Utils/UTILS_Utilisateurs.py", old, new,
        "listeAvatars = []",
    )


def fix_sync_anomalies_default() -> bool:
    old = '''        try: \n            \n            listeAnomalies = []\n            for track in self.parent.listeTracks :\n'''
    new = '''        listeAnomalies = []\n        try:\n            for track in self.parent.listeTracks :\n'''
    return _replace_idempotent(
        "Dlg/DLG_Synchronisation_donnees.py", old, new,
        "        listeAnomalies = []\n        try:\n",
    )


def fix_unsubscribe_date_default() -> bool:
    old = '''    date_erreur = False\n    try:\n        date_desinscription = UTILS_Dates.DateFrEng(date)\n'''
    new = '''    date_erreur = False\n    date_desinscription = None\n    try:\n        date_desinscription = UTILS_Dates.DateFrEng(date)\n'''
    return _replace_idempotent(
        "Utils/UTILS_Procedures.py", old, new,
        "date_desinscription = None\n    try:",
    )


def fix_rfid_timer_restart() -> bool:
    old = '''            except Exception as err:\n                pass\n\n\n\n\n\n\n# -------------------------------------------------------------------------------------------------------------------------------------------\n'''
    new = '''            except Exception as err:\n                # Une erreur peut survenir après l'arrêt volontaire du timer.\n                # Dans ce cas l'ancien code désactivait silencieusement le RFID\n                # jusqu'au redémarrage de l'application.\n                try:\n                    if not self.timer_rfid.IsRunning():\n                        self.timer_rfid.Start()\n                except Exception:\n                    pass\n\n\n\n\n\n\n# -------------------------------------------------------------------------------------------------------------------------------------------\n'''
    return _replace_idempotent(
        "Ol/OL_Individus.py", old, new,
        "l'ancien code désactivait silencieusement le RFID",
    )


def count_bare_excepts() -> int:
    total = 0
    for path in iter_first_party_python():
        source = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        total += sum(
            1 for node in ast.walk(tree)
            if isinstance(node, ast.ExceptHandler) and node.type is None
        )
    return total


def main() -> int:
    bare_before = count_bare_excepts()
    changed_files = 0
    changed_handlers = 0
    for path in iter_first_party_python():
        changed = replace_bare_excepts(path)
        if changed:
            changed_files += 1
            changed_handlers += changed

    fixes = {
        "code-barres famille": fix_individual_barcode_refresh(),
        "serveur Nomadhys": fix_nomad_server_abort(),
        "avatars utilisateurs": fix_user_avatar_default(),
        "anomalies synchronisation": fix_sync_anomalies_default(),
        "date désinscription": fix_unsubscribe_date_default(),
        "timer RFID": fix_rfid_timer_restart(),
    }

    bare_after = count_bare_excepts()
    if bare_after != 0:
        raise SystemExit(f"Hardening incomplet : {bare_after} except nu(s) subsistent")

    print(f"except nus : {bare_before} -> {bare_after} ({changed_handlers} resserrés dans {changed_files} fichiers)")
    for label, changed in fixes.items():
        print(f"{label} : {'corrigé' if changed else 'déjà corrigé'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
