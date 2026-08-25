#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Applique les corrections mécaniques de la passe globale de hardening.

Le script est volontairement étroit : aucun reformatage global, aucune
transformation SQL et aucune modification métier implicite.
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
        replaced, n = re.subn(r"\bexcept\s*:", "except Exception:", lines[index], count=1)
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
    return _replace_idempotent("Ol/OL_Individus.py", old, new, "self.listView.MAJ(forceActualisation=True)")


def fix_nomad_server_abort() -> bool:
    old = '''    except Exception as err:\n        print(("Erreur lancement serveur Nomadhys :", err))\n        log.EcritLog(_(u"Erreur dans le lancement du serveur Nomadhys [factory] :") )\n        log.EcritLog(err)\n\n    try :\n'''
    new = '''    except Exception as err:\n        print(("Erreur lancement serveur Nomadhys :", err))\n        log.EcritLog(_(u"Erreur dans le lancement du serveur Nomadhys [factory] :") )\n        log.EcritLog(err)\n        # Sans socket d'écoute il ne faut ni annoncer un serveur prêt ni\n        # démarrer le reactor.\n        return\n\n    try :\n'''
    return _replace_idempotent("Ctrl/CTRL_Serveur_nomade.py", old, new, "Sans socket d'écoute il ne faut ni annoncer un serveur prêt")


def fix_user_avatar_default() -> bool:
    old = '''    # chargement avatars\n    try :\n        req = """SELECT IDutilisateur, image\n'''
    new = '''    # chargement avatars\n    listeAvatars = []\n    try :\n        req = """SELECT IDutilisateur, image\n'''
    return _replace_idempotent("Utils/UTILS_Utilisateurs.py", old, new, "listeAvatars = []")


def fix_sync_anomalies_default() -> bool:
    path = NOETHYS / "Dlg/DLG_Synchronisation_donnees.py"
    source = path.read_text(encoding="utf-8")
    if "        listeAnomalies = []\n\n        try:\n" in source or "        listeAnomalies = []\n        try:\n" in source:
        return False
    old = '''        try: \n            \n            listeAnomalies = []\n            for track in self.parent.listeTracks :\n'''
    new = '''        listeAnomalies = []\n\n        try:\n            for track in self.parent.listeTracks :\n'''
    if old not in source:
        raise RuntimeError("Motif de hardening introuvable : Dlg/DLG_Synchronisation_donnees.py / listeAnomalies")
    source = source.replace(old, new, 1)
    ast.parse(source)
    path.write_text(source, encoding="utf-8")
    return True


def fix_unsubscribe_date_default() -> bool:
    old = '''    date_erreur = False\n    try:\n        date_desinscription = UTILS_Dates.DateFrEng(date)\n'''
    new = '''    date_erreur = False\n    date_desinscription = None\n    try:\n        date_desinscription = UTILS_Dates.DateFrEng(date)\n'''
    return _replace_idempotent("Utils/UTILS_Procedures.py", old, new, "date_desinscription = None\n    try:")


def fix_documents_timestamp_mutation() -> bool:
    old = '''    # Ajoute l'horodatage dans chaque document\n    try:\n        DB = GestionDB.DB(suffixe="DOCUMENTS")\n        req = "UPDATE documents SET last_update='%s';" % datetime.datetime.now()\n        DB.ExecuterReq(req)\n        DB.Commit()\n        DB.Close()\n    except Exception:\n        pass\n'''
    new = '''    # Ajoute l'horodatage dans chaque document. Une erreur d'écriture doit\n    # remonter à Procedure(), qui sait déjà l'afficher à l'utilisateur.\n    DB = GestionDB.DB(suffixe="DOCUMENTS")\n    try:\n        req = "UPDATE documents SET last_update='%s';" % datetime.datetime.now()\n        DB.ExecuterReq(req)\n        DB.Commit()\n    finally:\n        DB.Close()\n'''
    return _replace_idempotent(
        "Utils/UTILS_Procedures.py",
        old,
        new,
        "Une erreur d'écriture doit\n    # remonter à Procedure()",
    )


def fix_rfid_timer_restart() -> bool:
    old = '''            except Exception as err:\n                pass\n\n\n\n\n\n\n# -------------------------------------------------------------------------------------------------------------------------------------------\n'''
    new = '''            except Exception as err:\n                try:\n                    if not self.timer_rfid.IsRunning():\n                        self.timer_rfid.Start()\n                except Exception:\n                    pass\n\n\n\n\n\n\n# -------------------------------------------------------------------------------------------------------------------------------------------\n'''
    return _replace_idempotent("Ol/OL_Individus.py", old, new, "if not self.timer_rfid.IsRunning()")


def fix_individuals_rfid_flow() -> bool:
    path = NOETHYS / "Ol/OL_Individus.py"
    source = path.read_text(encoding="utf-8")
    changed = False
    replacements = [
        (
            '''                    if self.dernierRFID != IDbadge :\n                        self.dernierRFID = IDbadge\n\n                    # Recherche du badge RFID dans les questionnaires\n''',
            '''                    # Ignore une lecture répétée du même badge pendant\n                    # la fenêtre anti-rebond.\n                    if self.dernierRFID == IDbadge:\n                        return False\n                    self.dernierRFID = IDbadge\n\n                    # Recherche du badge RFID dans les questionnaires\n''',
            "if self.dernierRFID == IDbadge",
        ),
        (
            '''                    # On stoppe le timer de détection RFID\n                    self.timer_rfid.Stop()\n\n                    time.sleep(2)\n\n                    # Ouverture de la fiche famille\n                    if IDindividu != None:\n                        track = self.dictTracks[IDindividu]\n                        self.SelectObject(track)\n                        self.OuvrirFicheFamille(track)\n\n                    if IDfamille != None:\n                        self.OuvrirFicheFamille(IDfamille=IDfamille)\n\n                    # On relance le timer de détection RFID\n                    self.timer_rfid.Start()\n''',
            '''                    # Ne bloque pas la boucle wx et ne coupe pas le timer :\n                    # l'anti-rebond est assuré par dernierRFID/delai.\n                    if IDindividu != None:\n                        track = self.dictTracks.get(IDindividu)\n                        if track is not None:\n                            self.SelectObject(track)\n                            self.OuvrirFicheFamille(track)\n                        elif IDfamille != None:\n                            self.OuvrirFicheFamille(IDfamille=IDfamille)\n\n                    elif IDfamille != None:\n                        self.OuvrirFicheFamille(IDfamille=IDfamille)\n''',
            "track = self.dictTracks.get(IDindividu)",
        ),
        (
            '''        if dlg.ShowModal() == wx.ID_OK:\n            pass\n        # MAJ du listView\n''',
            '''        if dlg.ShowModal() == wx.ID_OK:\n            pass\n        dlg.Destroy()\n        # MAJ du listView\n''',
            "dlg.Destroy()\n        # MAJ du listView",
        ),
        (
            '''            except Exception:\n                IDfamille = None\n            if IDindividu != None and IDindividu in self.listView.dictTracks :\n''',
            '''            except Exception:\n                IDindividu = None\n            if IDindividu != None and IDindividu in self.listView.dictTracks :\n''',
            "except Exception:\n                IDindividu = None\n            if IDindividu",
        ),
        (
            '''        if dictIndividus == self.dictIndividus and self.forceActualisation == False :\n            return None\n''',
            '''        if dictIndividus == self.dictIndividus and self.forceActualisation == False and self.donnees :\n            return None\n''',
            "and self.forceActualisation == False and self.donnees",
        ),
    ]
    for old, new, marker in replacements:
        if marker in source:
            continue
        if old not in source:
            raise RuntimeError(f"Motif RFID/individus introuvable : {marker}")
        source = source.replace(old, new, 1)
        changed = True
    ast.parse(source)
    if changed:
        path.write_text(source, encoding="utf-8")
    return changed


def count_bare_excepts() -> int:
    total = 0
    for path in iter_first_party_python():
        source = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        total += sum(1 for node in ast.walk(tree) if isinstance(node, ast.ExceptHandler) and node.type is None)
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
        "horodatage DOCUMENTS": fix_documents_timestamp_mutation(),
        "timer RFID": fix_rfid_timer_restart(),
        "flux RFID individus": fix_individuals_rfid_flow(),
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
